import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask import Flask, render_template, request, jsonify, g
from openai import OpenAI
import os
import config
import re
import json
from datetime import datetime, timedelta

# === Flask アプリケーションの設定 ===
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# ディレクトリ作成
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

# === グローバル変数 ===
patent_df = None
selected_patent = None
vectorizer = None
tfidf_matrix = None
search_texts = None

# === OpenAI クライアント初期化 ===
client = OpenAI(api_key=config.OPENAI_API_KEY)

def load_patent_csv():
    """特許CSVファイルを読み込む"""
    global patent_df
    try:
        # CSVファイルを読み込み
        patent_df = pd.read_csv('right_list_modified.csv')
        
        # データクリーニング
        patent_df = patent_df.fillna('')
        
        # 改行文字の正規化（全ての文字列列に適用）
        for col in ['名称', '要約', '所管部課名']:
            if col in patent_df.columns:
                patent_df[col] = patent_df[col].astype(str).str.replace('_x000D_', '\n', regex=False)
        
        print(f"特許データを読み込みました: {len(patent_df)}件")
        return True
    except Exception as e:
        print(f"CSVファイル読み込みエラー: {e}")
        return False

def initialize_search_system():
    """検索システムの初期化（TF-IDFベクトル化）"""
    global patent_df, vectorizer, tfidf_matrix, search_texts
    
    if patent_df is None:
        print("特許データが読み込まれていません")
        return False
    
    try:
        # 検索対象のテキストを結合（名称 + 要約 + 所管部課名）
        search_texts = []
        for _, row in patent_df.iterrows():
            text = f"{row.get('名称', '')} {row.get('要約', '')} {row.get('所管部課名', '')}"
            search_texts.append(text)
        
        # TF-IDFベクトル化（日本語最適化）
        vectorizer = TfidfVectorizer(
            max_features=3000,          # 語彙数を増加
            stop_words=None,            # ストップワード無効
            ngram_range=(1, 3),         # 3-gramまで拡張
            min_df=1,                   # 最小頻度1（削除しない）
            max_df=1.0,                 # 最大頻度制限を撤廃
            token_pattern=r'[^\s]+',    # 日本語対応の正規表現
            norm='l2',                  # L2正規化
            use_idf=True,               # IDF使用
            sublinear_tf=True           # サブリニアTF使用
        )
        
        tfidf_matrix = vectorizer.fit_transform(search_texts)
        
        print(f"検索システムを初期化しました: {tfidf_matrix.shape}")
        
        # 語彙の詳細確認
        feature_names = vectorizer.get_feature_names_out()
        combustion_terms = [term for term in feature_names if '燃焼' in term]
        print(f"燃焼関連語彙数: {len(combustion_terms)}")
        
        return True
        
    except Exception as e:
        print(f"検索システム初期化エラー: {e}")
        return False

def parse_natural_query(query):
    """自然言語クエリを構造化データに変換"""
    try:
        # OpenAI GPTによるクエリ解析
        prompt = f"""
以下の日本語クエリを解析して、JSON形式で構造化データを返してください。

クエリ: "{query}"

以下のフィールドを抽出してください：
1. keywords: 技術的なキーワード（配列）
2. date_range: 日付範囲 {{start_year: 数値, end_year: 数値}}
3. inventor_conditions: 発明者に関する条件 {{gender: "male"/"female"/null, name_keywords: 配列}}
4. applicant_conditions: 出願人に関する条件 {{organizations: 配列, type: "university"/"company"/null}}
5. law_type: 法別 ("特許"/"実用新案"/"意匠"/"商標"/null)
6. limit: 結果件数 (数値またはnull)
7. sort_order: ソート順 ("newest"/"oldest"/"relevance"/null)

日本語の時間表現の解釈：
- "2010年代" → 2010-2019
- "直近" → 2020年以降
- "新しいもの" → newest
- "最近" → 2020年以降

JSON形式で返答してください（説明文は不要）：
"""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたは特許検索クエリ解析の専門家です。正確なJSON形式で返答してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        # JSONレスポンスをパース
        result_text = response.choices[0].message.content.strip()
        
        # JSON部分を抽出（```json```で囲まれている場合に対応）
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        elif "```" in result_text:
            json_start = result_text.find("```") + 3
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        
        parsed_query = json.loads(result_text)
        
        print(f"解析されたクエリ: {json.dumps(parsed_query, ensure_ascii=False, indent=2)}")
        return parsed_query
        
    except Exception as e:
        print(f"クエリ解析エラー: {e}")
        # フォールバック：シンプルなキーワード検索として扱う
        return {
            "keywords": [query],
            "date_range": None,
            "inventor_conditions": None,
            "applicant_conditions": None,
            "law_type": None,
            "limit": 3,
            "sort_order": "relevance"
        }

def estimate_gender_from_name(name):
    """日本人名から性別を推定（簡易版）"""
    if not name or not isinstance(name, str):
        return None
    
    # 一般的な女性名の終わり文字
    female_endings = ['子', '美', '恵', '香', '花', '菜', '奈', '里', '絵', '代', '世', '江', '枝']
    # 一般的な男性名の終わり文字
    male_endings = ['雄', '男', '夫', '郎', '朗', '彦', '助', '介', '太', '大', '治', '司', '史', '志']
    
    last_char = name[-1] if name else ''
    
    if last_char in female_endings:
        return 'female'
    elif last_char in male_endings:
        return 'male'
    else:
        return None

def apply_advanced_filters(df, parsed_query):
    """構造化クエリに基づいて高度なフィルタリングを実行"""
    filtered_df = df.copy()
    
    try:
        # 1. 日付範囲フィルタ
        if parsed_query.get('date_range'):
            date_range = parsed_query['date_range']
            start_year = date_range.get('start_year')
            end_year = date_range.get('end_year')
            
            if start_year or end_year:
                # 出願日をパース
                filtered_df['出願日_parsed'] = pd.to_datetime(filtered_df['出願日'], errors='coerce')
                filtered_df['出願年'] = filtered_df['出願日_parsed'].dt.year
                
                if start_year:
                    filtered_df = filtered_df[filtered_df['出願年'] >= start_year]
                if end_year:
                    filtered_df = filtered_df[filtered_df['出願年'] <= end_year]
        
        # 2. 法別フィルタ
        law_type = parsed_query.get('law_type')
        if law_type and '法別' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['法別'].str.contains(law_type, na=False)]
        
        # 3. 発明者条件フィルタ
        inventor_conditions = parsed_query.get('inventor_conditions')
        if inventor_conditions:
            gender = inventor_conditions.get('gender')
            name_keywords = inventor_conditions.get('name_keywords', [])
            
            if gender:
                # 全発明者列を取得
                inventor_cols = [col for col in filtered_df.columns if col.startswith('発明者')]
                
                def check_inventor_gender(row):
                    for col in inventor_cols:
                        inventor_name = row.get(col, '')
                        if inventor_name and estimate_gender_from_name(inventor_name) == gender:
                            return True
                    return False
                
                filtered_df = filtered_df[filtered_df.apply(check_inventor_gender, axis=1)]
            
            if name_keywords:
                # 発明者名にキーワードが含まれるかチェック
                def check_inventor_keywords(row):
                    for col in inventor_cols:
                        inventor_name = str(row.get(col, ''))
                        for keyword in name_keywords:
                            if keyword in inventor_name:
                                return True
                    return False
                
                filtered_df = filtered_df[filtered_df.apply(check_inventor_keywords, axis=1)]
        
        # 4. 出願人条件フィルタ
        applicant_conditions = parsed_query.get('applicant_conditions')
        if applicant_conditions:
            organizations = applicant_conditions.get('organizations', [])
            org_type = applicant_conditions.get('type')
            
            if organizations:
                # 出願人列を取得
                applicant_cols = [col for col in filtered_df.columns if col.startswith('出願人')] + ['筆頭出願人']
                
                def check_applicant_org(row):
                    for col in applicant_cols:
                        applicant_name = str(row.get(col, ''))
                        for org in organizations:
                            if org in applicant_name:
                                return True
                    return False
                
                filtered_df = filtered_df[filtered_df.apply(check_applicant_org, axis=1)]
            
            if org_type == 'university':
                # 大学関連キーワード
                university_keywords = ['大学', '大学院', '学院', '工業大学', '科学技術大学']
                
                def check_university(row):
                    for col in applicant_cols:
                        applicant_name = str(row.get(col, ''))
                        for keyword in university_keywords:
                            if keyword in applicant_name:
                                return True
                    return False
                
                filtered_df = filtered_df[filtered_df.apply(check_university, axis=1)]
        
        print(f"フィルタリング後: {len(filtered_df)}件")
        return filtered_df
        
    except Exception as e:
        print(f"フィルタリングエラー: {e}")
        return filtered_df

def advanced_search(query, top_k=3):
    """自然言語クエリによる高度な特許検索"""
    global patent_df
    
    if patent_df is None:
        return []
    
    try:
        # 1. 自然言語クエリを解析
        parsed_query = parse_natural_query(query)
        
        # 2. 指定された件数を取得
        limit = parsed_query.get('limit', top_k)
        if limit is None:
            limit = top_k
        
        # 3. 高度なフィルタリングを適用
        filtered_df = apply_advanced_filters(patent_df, parsed_query)
        
        if len(filtered_df) == 0:
            return []
        
        # 4. キーワード検索（TF-IDFまたはフォールバック）
        keywords = parsed_query.get('keywords', [])
        if keywords:
            # 複数キーワードを結合
            keyword_query = ' '.join(keywords)
            
            # フィルタリング済みデータでTF-IDF検索を実行
            search_results = search_patents_on_filtered_data(keyword_query, filtered_df, limit)
        else:
            # キーワードなしの場合は、フィルタ結果をそのまま使用
            search_results = []
            for idx, row in filtered_df.head(limit).iterrows():
                search_results.append({
                    'index': int(idx),
                    'similarity': 1.0,  # フィルタ条件に完全マッチ
                    'application_number': row.get('出願番号', ''),
                    'name': row.get('名称', ''),
                    'applicant': row.get('筆頭出願人', ''),
                    'inventor': row.get('発明者 1', ''),
                    'match_type': 'advanced_filter'
                })
        
        # 5. ソート順を適用
        sort_order = parsed_query.get('sort_order', 'relevance')
        if sort_order == 'newest':
            # 登録日順（新しい順）
            search_results = sorted(search_results, key=lambda x: patent_df.iloc[x['index']].get('登録日', ''), reverse=True)
        elif sort_order == 'oldest':
            # 登録日順（古い順）
            search_results = sorted(search_results, key=lambda x: patent_df.iloc[x['index']].get('登録日', ''))
        # relevanceの場合は既に類似度順
        
        return search_results[:limit]
        
    except Exception as e:
        print(f"高度検索エラー: {e}")
        # フォールバック：通常検索
        return search_patents(query, top_k)

def search_patents_on_filtered_data(query, filtered_df, top_k=3):
    """フィルタリング済みデータでTF-IDF検索を実行"""
    try:
        if len(filtered_df) == 0:
            return []
        
        # フィルタリング済みデータの検索テキストを作成
        search_texts = []
        indices = []
        for idx, row in filtered_df.iterrows():
            text = f"{row.get('名称', '')} {row.get('要約', '')} {row.get('所管部課名', '')}"
            search_texts.append(text)
            indices.append(idx)
        
        # TF-IDFベクトル化
        temp_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1,
            token_pattern=r'[^\s]+',
            norm='l2'
        )
        
        temp_tfidf_matrix = temp_vectorizer.fit_transform(search_texts)
        query_vector = temp_vectorizer.transform([query])
        
        # コサイン類似度計算
        similarities = cosine_similarity(query_vector, temp_tfidf_matrix).flatten()
        
        # 結果作成
        results = []
        for i, (original_idx, similarity) in enumerate(zip(indices, similarities)):
            if similarity > 0.01:  # 閾値
                row = filtered_df.iloc[i]
                results.append({
                    'index': int(original_idx),
                    'similarity': float(similarity),
                    'application_number': row.get('出願番号', ''),
                    'name': row.get('名称', ''),
                    'applicant': row.get('筆頭出願人', ''),
                    'inventor': row.get('発明者 1', ''),
                    'match_type': 'filtered_tfidf'
                })
        
        # 類似度順でソート
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        print(f"フィルタ済みTF-IDF検索エラー: {e}")
        return []

def fallback_search(query, top_k=3):
    """フォールバック検索（文字列マッチング）"""
    global patent_df
    
    if patent_df is None:
        return []
    
    matches = []
    query_lower = query.lower()
    
    for idx, row in patent_df.iterrows():
        # 検索対象テキスト
        name = str(row.get('名称', '')).lower()
        summary = str(row.get('要約', '')).lower()
        department = str(row.get('所管部課名', '')).lower()
        
        # マッチ度計算（出現回数に上限を設定）
        name_matches = min(name.count(query_lower), 3) * 3        # 名称マッチ最大9点
        summary_matches = min(summary.count(query_lower), 5) * 2  # 要約マッチ最大10点
        department_matches = min(department.count(query_lower), 2) # 部課名マッチ最大2点
        
        match_score = name_matches + summary_matches + department_matches
        
        if match_score > 0:
            # 類似度を0.0-1.0の範囲に正規化（最大21点）
            max_possible_score = 21  # 9 + 10 + 2
            normalized_similarity = min(match_score / max_possible_score, 1.0)
            
            # フォールバック検索の類似度は0.1-0.8の範囲に制限（TF-IDFと区別）
            final_similarity = 0.1 + (normalized_similarity * 0.7)
            
            matches.append({
                'index': int(idx),
                'similarity': float(final_similarity),
                'application_number': row.get('出願番号', ''),
                'name': row.get('名称', ''),
                'applicant': row.get('筆頭出願人', ''),
                'inventor': row.get('発明者 1', ''),
                'match_type': 'fallback',
                'raw_score': match_score  # デバッグ用
            })
    
    # マッチ度順でソート
    matches.sort(key=lambda x: x['similarity'], reverse=True)
    
    print(f"フォールバック検索: {len(matches)}件のマッチ")
    if matches:
        print(f"最高類似度: {matches[0]['similarity']:.3f} (生スコア: {matches[0].get('raw_score', 0)})")
    
    return matches[:top_k]

def search_patents(query, top_k=3):
    """ハイブリッド特許検索（TF-IDF + フォールバック）"""
    global patent_df, vectorizer, tfidf_matrix
    
    if patent_df is None or vectorizer is None or tfidf_matrix is None:
        print("検索システムが初期化されていません")
        return fallback_search(query, top_k)
    
    try:
        # Phase 1: TF-IDF検索
        print(f"=== TF-IDF検索開始: '{query}' ===")
        
        # クエリをベクトル化
        query_vector = vectorizer.transform([query])
        
        # クエリベクトルの詳細確認
        query_features = query_vector.toarray()[0]
        non_zero_features = query_features[query_features > 0]
        print(f"クエリベクトル非ゼロ要素数: {len(non_zero_features)}")
        
        if len(non_zero_features) == 0:
            print("クエリが語彙に含まれていません - フォールバック検索に切り替え")
            return fallback_search(query, top_k)
        
        # コサイン類似度計算
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # 詳細デバッグ情報
        max_sim = similarities.max()
        positive_count = (similarities > 0).sum()
        significant_count = (similarities > 0.01).sum()
        
        print(f"最大類似度: {max_sim:.6f}")
        print(f"類似度>0の件数: {positive_count}")
        print(f"類似度>0.01の件数: {significant_count}")
        
        # 上位候補を取得
        top_indices = similarities.argsort()[-top_k*2:][::-1]  # 余裕をもって多めに取得
        
        tfidf_results = []
        for idx in top_indices:
            if similarities[idx] > 0.001:  # 閾値をさらに下げる
                patent = patent_df.iloc[idx]
                tfidf_results.append({
                    'index': int(idx),
                    'similarity': float(similarities[idx]),
                    'application_number': patent.get('出願番号', ''),
                    'name': patent.get('名称', ''),
                    'applicant': patent.get('筆頭出願人', ''),
                    'inventor': patent.get('発明者 1', ''),
                    'match_type': 'tfidf'
                })
        
        print(f"TF-IDF検索結果: {len(tfidf_results)}件")
        
        # Phase 2: 結果が不十分な場合はフォールバック検索を併用
        if len(tfidf_results) < top_k:
            print("=== フォールバック検索を併用 ===")
            fallback_results = fallback_search(query, top_k)
            
            # 結果をマージ（重複除去）
            all_results = tfidf_results.copy()
            used_indices = {r['index'] for r in tfidf_results}
            
            for fb_result in fallback_results:
                if fb_result['index'] not in used_indices:
                    all_results.append(fb_result)
                    if len(all_results) >= top_k:
                        break
            
            # 類似度順でソート
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            final_results = all_results[:top_k]
            
        else:
            final_results = tfidf_results[:top_k]
        
        print(f"最終検索結果: {len(final_results)}件")
        for i, result in enumerate(final_results):
            print(f"{i+1}. [{result['similarity']:.4f}] {result['name'][:50]}... ({result['match_type']})")
        
        return final_results
        
    except Exception as e:
        print(f"TF-IDF検索エラー: {e} - フォールバック検索に切り替え")
        return fallback_search(query, top_k)

# === ルート定義 ===

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/search_patents', methods=['POST'])
def search_patents_endpoint():
    """特許検索API"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': '検索キーワードを入力してください'}), 400
        
        # 特許検索実行
        results = search_patents(query)
        
        if not results:
            return jsonify({'error': '該当する特許が見つかりませんでした'}), 404
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': f'検索エラー: {str(e)}'}), 500

@app.route('/search_patents_advanced', methods=['POST'])
def search_patents_advanced_endpoint():
    """自然言語による高度な特許検索API"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': '検索クエリを入力してください'}), 400
        
        # 高度な特許検索実行
        results = advanced_search(query)
        
        if not results:
            return jsonify({'error': '該当する特許が見つかりませんでした'}), 404
        
        # 追加情報を含めて返す
        enhanced_results = []
        for result in results:
            patent = patent_df.iloc[result['index']]
            enhanced_result = result.copy()
            enhanced_result.update({
                'application_date': patent.get('出願日', ''),
                'registration_date': patent.get('登録日', ''),
                'law_type': patent.get('法別', ''),
                'department': patent.get('所管部課名', ''),
                'summary_preview': patent.get('要約', '')[:100] + '...' if len(str(patent.get('要約', ''))) > 100 else patent.get('要約', '')
            })
            enhanced_results.append(enhanced_result)
        
        return jsonify({
            'results': enhanced_results,
            'search_type': 'advanced_natural_language'
        })
        
    except Exception as e:
        return jsonify({'error': f'高度検索エラー: {str(e)}'}), 500

@app.route('/select_patent', methods=['POST'])
def select_patent_endpoint():
    """特許選択API"""
    global selected_patent
    
    try:
        data = request.get_json()
        index = data.get('index')
        
        if index is None or patent_df is None:
            return jsonify({'error': '無効な選択です'}), 400
        
        # 選択された特許を取得
        selected_patent = patent_df.iloc[index].to_dict()
        
        # 詳細情報を返す
        patent_details = {
            'application_number': selected_patent.get('出願番号', ''),
            'application_date': selected_patent.get('出願日', ''),
            'registration_number': selected_patent.get('登録番号', ''),
            'registration_date': selected_patent.get('登録日', ''),
            'expiration_date': selected_patent.get('存続期間満了日', ''),
            'name': selected_patent.get('名称', ''),
            'department': selected_patent.get('所管部課名', ''),
            'summary': selected_patent.get('要約', ''),
            'main_applicant': selected_patent.get('筆頭出願人', ''),
            'inventors': [selected_patent.get(f'発明者 {i}', '') for i in range(1, 14) if selected_patent.get(f'発明者 {i}', '')],
            'applicants': [selected_patent.get(f'出願人 {i}', '') for i in range(1, 12) if selected_patent.get(f'出願人 {i}', '')]
        }
        
        return jsonify(patent_details)
        
    except Exception as e:
        return jsonify({'error': f'選択エラー: {str(e)}'}), 500

@app.route('/ask_about_patent', methods=['POST'])
def ask_about_patent():
    """選択した特許についての質問に回答"""
    global selected_patent
    
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': '質問を入力してください'}), 400
        
        if not selected_patent:
            return jsonify({'error': '特許が選択されていません'}), 400
        
        # 特許情報を整理
        patent_info = f"""
特許情報:
- 出願番号: {selected_patent.get('出願番号', '')}
- 名称: {selected_patent.get('名称', '')}
- 要約: {selected_patent.get('要約', '')}
- 所管部課: {selected_patent.get('所管部課名', '')}
- 筆頭出願人: {selected_patent.get('筆頭出願人', '')}
- 発明者: {selected_patent.get('発明者 1', '')}
- 出願日: {selected_patent.get('出願日', '')}
- 登録番号: {selected_patent.get('登録番号', '')}
- 登録日: {selected_patent.get('登録日', '')}
"""
        
        # プロンプト作成
        prompt = f"""
あなたは特許分析の専門家です。以下の特許情報を基に、ユーザーの質問に詳細に回答してください。

{patent_info}

ユーザーの質問: {question}

回答の際は以下の点を考慮してください：
1. 技術的な特徴と革新性
2. 産業応用の可能性
3. 技術分野における位置づけ
4. 発明の効果と優位性

専門的でありながら分かりやすい回答をお願いします。
"""
        
        # OpenAI APIで回答生成
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたは特許分析の専門家として、技術的で詳細な分析を提供します。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        
        answer = response.choices[0].message.content
        
        return jsonify({'answer': answer})
        
    except Exception as e:
        return jsonify({'error': f'回答生成エラー: {str(e)}'}), 500

# === アプリケーション初期化 ===
if __name__ == "__main__":
    # 特許データ読み込み
    if load_patent_csv():
        print("特許データベースの準備が完了しました")
        
        # 検索システム初期化
        if initialize_search_system():
            print("検索システムの初期化が完了しました")
        else:
            print("警告: 検索システムの初期化に失敗しました")
    else:
        print("警告: 特許データの読み込みに失敗しました")
    
    # アプリケーション起動
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)