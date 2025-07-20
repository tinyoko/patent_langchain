# CLAUDE.md - 特許公開公報AI検索アシスタント開発記録

## 📋 プロジェクト概要

このドキュメントは、Claude Code を使用した特許公開公報AI検索アシスタントの開発プロセス、技術的詳細、設計思想を記録したものです。

**開発日**: 2025年1月20日  
**開発者**: Claude Code (Anthropic)  
**プロジェクト種別**: LangChain学習教材から発展した特許検索アプリケーション

## 🎯 開発要件

### 初期要求
- 既存のLangChainアプリ（org_app）を参考に、特許公開公報用の検索アプリを作成
- PDFファイルのアップロード機能
- RAGシステムによる特許文書解析
- Web検索による関連情報補完
- モダンなUI/UX

### 技術的制約
- 既存の仮想環境 `langchain` を使用
- 既存のAPIキー（OpenAI、SerpAPI）を活用
- new_appフォルダ内に独立したアプリケーションとして構築

## 🏗️ アーキテクチャ設計

### システム全体図
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask App     │    │   External APIs │
│                 │    │                 │    │                 │
│ • HTML/CSS/JS   │◄──►│ • Route Handler │◄──►│ • OpenAI API    │
│ • File Upload   │    │ • RAG System    │    │ • SerpAPI       │
│ • Question Form │    │ • LangGraph     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Storage  │
                       │                 │
                       │ • ChromaDB      │
                       │ • PDF Files     │
                       └─────────────────┘
```

### データフロー
1. **PDF Upload** → `PyPDFLoader` → `RecursiveCharacterTextSplitter` → `OpenAI Embeddings` → `ChromaDB`
2. **Question** → `RAG Retrieve` → `LangGraph Workflow` → `GPT-4o-mini` → Response
3. **Web Search** → `SerpAPI` → Patent Information → Formatted Links

## 🧩 コンポーネント詳細

### 1. Flask Application (app.py)

#### 主要ルート
- `GET /`: メインページ表示
- `POST /upload`: PDFファイルアップロード・処理
- `POST /ask`: 質問処理・回答生成
- `POST /reset`: システムリセット

#### セキュリティ機能
- `secure_filename()`: ファイル名のサニタイズ
- `allowed_file()`: 拡張子チェック
- ファイルサイズ制限 (16MB)

### 2. RAGシステム実装

#### テキスト分割戦略
```python
RecursiveCharacterTextSplitter(
    chunk_size=1000,      # 1000文字単位で分割
    chunk_overlap=200     # 200文字のオーバーラップ
)
```

#### ベクトル検索
- **Embedding Model**: `text-embedding-3-small`
- **検索件数**: 5件 (特許情報のため一般的な3件より多く設定)
- **類似度検索**: コサイン類似度ベース

#### プロンプトエンジニアリング
特許文書に特化したプロンプトテンプレート：
- 技術的内容の詳細説明
- 先行技術との比較
- 発明の効果の説明
- 関連特許情報の提供

### 3. LangGraphワークフロー

#### ノード構成
```python
workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)    # メイン応答生成
workflow.add_node("tools", tool_node)     # ツール実行
```

#### 条件分岐ロジック
```python
def should_continue(state: MessagesState) -> Literal["tools", END]:
    # tool_calls の存在確認
    # "patent_search" や "検索" キーワードの検出
    # END または tools への分岐
```

#### メモリ機能
- `MemorySaver`: 会話履歴の永続化
- Thread ID: `"patent_analysis"` (特許分析専用)

### 4. Web検索ツール

#### SerpAPI設定
```python
@tool
def patent_search(query: str):
    params = {
        "q": f"特許 {query}",    # 特許キーワードを自動付加
        "hl": "ja",              # 日本語
        "gl": "jp",              # 日本地域
        "api_key": config.SERP_API_KEY
    }
```

#### 検索結果処理
- 上位5件のオーガニック検索結果を取得
- タイトル、スニペット、リンクを構造化
- Flask.g を使用した結果の一時保存

### 5. フロントエンド設計

#### UI/UXの特徴
- **グラデーション背景**: 視覚的な美しさ
- **ドラッグ&ドロップ**: 直感的なファイルアップロード
- **ローディングアニメーション**: 処理状況の可視化
- **レスポンシブデザイン**: 様々な画面サイズに対応

#### JavaScript機能
- ファイル選択・アップロード
- 非同期通信 (Fetch API)
- DOM操作による動的コンテンツ更新
- エラーハンドリング

## 🔧 技術的な実装詳細

### RAGシステムの最適化

#### チャンク戦略
特許文書の特性を考慮した分割：
- **chunk_size: 1000**: 技術的説明の文脈を保持
- **chunk_overlap: 200**: 段落間の関連性を維持
- **k=5**: より多くの関連情報を取得

#### 埋め込みモデル選択
- `text-embedding-3-small`: コストと性能のバランス
- 日本語特許文書に対する高い精度
- 低レイテンシーでの検索実現

### LangGraphワークフローの設計思想

#### 条件分岐の詳細化
```python
# 複数の条件でツール使用を判定
if last_message.tool_calls:
    return "tools"
if "patent_search" in last_message.content:
    return "tools"
if "検索" in last_message.content:
    return "tools"
return END
```

#### エラーハンドリング
- グローバル変数の安全な初期化
- データベース接続の状態管理
- ファイル処理例外の適切な処理

### フロントエンドの技術選択

#### CSS設計
- **グラデーション**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
- **シャドウ効果**: `box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1)`
- **トランジション**: 滑らかなユーザー体験

#### JavaScript設計
- **ES6+**: モダンな JavaScript 機能を活用
- **Promise/Async**: 非同期処理の適切な実装
- **エラーハンドリング**: try-catch による堅牢性

## 📊 パフォーマンス考慮事項

### スケーラビリティ
- **ChromaDB**: インメモリ運用でのレスポンス最適化
- **ストリーミング**: LangGraphのstream_mode活用
- **ファイルサイズ制限**: メモリ使用量の制御

### コスト最適化
- **GPT-4o-mini**: 高性能・低コストモデルの選択
- **Embedding API**: 効率的なベクトル化
- **SerpAPI**: 必要最小限の検索実行

## 🎯 org_appからの改良点

### 機能拡張
1. **ファイルアップロード**: 静的PDFから動的アップロードへ
2. **UI/UX**: シンプルなフォームからモダンなインターフェースへ
3. **エラーハンドリング**: 堅牢性の向上
4. **リセット機能**: システム状態の管理

### コード品質
1. **関数分離**: setup_rag_system(), setup_workflow() の分離
2. **設定管理**: config.py の構造化
3. **セキュリティ**: ファイルアップロードのセキュリティ強化
4. **ドキュメント**: 包括的なドキュメント作成

## 🔮 今後の改善計画

### 短期的改善 (1-2週間)
- [ ] マルチファイルアップロード対応
- [ ] 特許番号による自動検索
- [ ] 検索履歴の保存・表示
- [ ] 回答の品質評価機能

### 中期的改善 (1-2か月)
- [ ] データベースの永続化 (SQLite/PostgreSQL)
- [ ] ユーザー認証・セッション管理
- [ ] 特許画像・図表の解析対応
- [ ] REST API の提供

### 長期的改善 (3-6か月)
- [ ] 機械学習による特許分類
- [ ] 類似特許の自動発見
- [ ] 特許マップ可視化
- [ ] 多言語対応 (英語特許等)

## 🐛 既知の制限事項

### 技術的制限
1. **ファイルサイズ**: 16MB制限による大型特許文書の制約
2. **言語**: 日本語特許のみ対応
3. **図表**: テキストのみの解析
4. **メモリ**: インメモリデータベースによる揮発性

### APIコスト
1. **OpenAI**: トークン使用量に比例したコスト
2. **SerpAPI**: 月間検索回数制限
3. **レート制限**: API呼び出し頻度の制約

## 📈 メトリクス・監視

### 推奨監視項目
- API レスポンス時間
- ファイル処理時間
- エラー発生率
- ユーザー満足度

### ログ出力
現在は Flask のデバッグログのみ。本番環境では以下を推奨：
- アクセスログ
- エラーログ
- パフォーマンスログ
- セキュリティログ

## 🔒 セキュリティ考慮事項

### 実装済み
- ファイル拡張子チェック
- ファイル名サニタイズ
- APIキーの環境変数管理
- CORS対策 (同一オリジン)

### 推奨追加対策
- HTTPS の強制
- ファイルウイルススキャン
- レート制限の実装
- 入力値のバリデーション強化

---

**このドキュメントは開発プロセスの透明性と将来の保守性を目的として作成されました。**

**最終更新**: 2025年1月20日  
**作成者**: Claude Code (Anthropic)