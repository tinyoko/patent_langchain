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

## 🚀 XserverVPS本番環境デプロイメント

### デプロイメント概要
このセクションでは、特許検索アプリケーションをXserverVPSに独自ドメイン（https://djartipy.com/patent）でデプロイする手順を記録しています。

**デプロイ日**: 2025年7月21日  
**デプロイ環境**: XserverVPS + Docker + Nginx  
**アクセスURL**: https://djartipy.com/patent

### デプロイメント手順

#### 1. ローカル環境からの準備
```bash
# 本番環境用設定ファイルの作成
cp config.py.example config.py
cp .env.example .env

# .envファイルに本番環境用APIキーを設定
# OPENAI_API_KEY=実際のAPIキー
# SERP_API_KEY=実際のAPIキー
# FLASK_SECRET_KEY=ランダムな文字列
# FLASK_HOST=0.0.0.0
# FLASK_PORT=5000
# FLASK_DEBUG=False

# GitHubにプッシュ
git add .
git commit -m "Add production deployment configuration"
git push origin main
```

#### 2. XserverVPSでのセットアップ
```bash
# プロジェクトのクローン
cd /opt/projects
git clone https://github.com/tinyoko/patent_langchain.git
cd patent_langchain

# 仮想環境のセットアップ
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 環境設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# アプリケーションの起動
python app.py
```

#### 3. 既存DifyアプリとのNginx統合

##### XserverVPS環境での実際の操作手順

**前提条件**:
- Difyアプリが `/root/dify/docker` に設置済み
- HTTPSドメイン `djartipy.com` が設定済み
- 特許アプリが `/opt/projects/patent_langchain` で起動中（ポート5000）

##### Step 1: Difyディレクトリ構造の確認
```bash
# rootユーザーでSSH接続後
cd /root/dify/docker

# ディレクトリ構造確認
ls -la
# 出力例:
# drwxr-xr-x 2 root root 4096 Jul 21 10:44 nginx
# -rw-r--r-- 1 root root 8932 Jul 12 16:53 docker-compose.yaml
# -rw-r--r-- 1 root root 1847 Jul 12 16:53 .env

# Nginx設定ディレクトリ確認
ls -la nginx/conf.d/
# 出力例:
# -rw-r--r-- 1 root root 1504 Jul 21 10:26 default.conf
# -rw-r--r-- 1 root root 1504 Jul 21 10:16 default.conf.backup
# -rw-r--r-- 1 root root 1128 Jul 12 16:53 default.conf.template
```

##### Step 2: 現在の設定ファイル内容確認
```bash
# テンプレートファイルの内容確認
cat nginx/conf.d/default.conf.template
```

**確認すべき内容**:
```nginx
# Please do not directly edit this file. Instead, modify the .env variables related to NGINX configuration.

server {
    listen ${NGINX_PORT};
    server_name ${NGINX_SERVER_NAME};

    location /console/api {
      proxy_pass http://api:5001;
      include proxy.conf;
    }
    # ... その他のDify設定 ...
    
    location / {
      proxy_pass http://web:3000;
      include proxy.conf;
    }
    location /mcp {
      proxy_pass http://api:5001;
      include proxy.conf;
    }
}
```

##### Step 3: 安全なバックアップ作成
```bash
# 作業前にバックアップを作成
cp nginx/conf.d/default.conf.template nginx/conf.d/default.conf.template.backup

# バックアップ確認
ls -la nginx/conf.d/default.conf.template*
# 出力例:
# -rw-r--r-- 1 root root 1128 Jul 12 16:53 default.conf.template
# -rw-r--r-- 1 root root 1128 Jul 21 10:47 default.conf.template.backup
```

##### Step 4: 特許アプリ接続確認
```bash
# 特許アプリの起動状態確認
ss -tlnp | grep 5000
# 出力例: LISTEN 0 128 0.0.0.0:5000 0.0.0.0:* users:(("python",pid=2438213,fd=3))

# Dockerコンテナからホストへの接続テスト
docker exec docker-nginx-1 curl -v http://172.17.0.1:5000
# 正常な場合: HTTP/1.1 200 OK が返される
```

##### Step 5: テンプレートファイルの編集

**重要**: `default.conf`ではなく`default.conf.template`を編集すること

```bash
# viエディタでテンプレートファイルを開く
vi nginx/conf.d/default.conf.template
```

**編集手順**:
1. viエディタで `/mcp` を検索: `/mcp` + Enter
2. `/mcp` ロケーションブロックの**前**にカーソルを移動
3. `O`（大文字のオー）で新しい行を挿入
4. 以下のコードを入力:

```nginx
    location /patent {
      rewrite ^/patent/?(.*) /$1 break;
      proxy_pass http://172.17.0.1:5000;
      include proxy.conf;
    }
```

5. `Esc` → `:wq` → Enter で保存終了

**編集後の最終的な構造**:
```nginx
# Please do not directly edit this file. Instead, modify the .env variables related to NGINX configuration.

server {
    listen ${NGINX_PORT};
    server_name ${NGINX_SERVER_NAME};

    # 既存のDify設定...
    location /e/ {
      proxy_pass http://plugin_daemon:5002;
      proxy_set_header Dify-Hook-Url $scheme://$host$request_uri;
      include proxy.conf;
    }

    # 🔴 特許アプリケーション設定（新規追加）
    location /patent {
      rewrite ^/patent/?(.*) /$1 break;
      proxy_pass http://172.17.0.1:5000;
      include proxy.conf;
    }

    # ⚠️ 重要: /patent設定は / 設定より前に配置
    location / {
      proxy_pass http://web:3000;
      include proxy.conf;
    }
    
    location /mcp {
      proxy_pass http://api:5001;
      include proxy.conf;
    }
    # 以下省略...
}
```

##### Step 6: 設定の確認と検証
```bash
# 編集結果の確認
cat nginx/conf.d/default.conf.template | grep -A 4 -B 1 patent
# 出力例:
#     location /patent {
#       rewrite ^/patent/?(.*) /$1 break;
#       proxy_pass http://172.17.0.1:5000;
#       include proxy.conf;
#     }

# Nginx設定の構文チェック（編集前に確認）
docker exec docker-nginx-1 nginx -t
# 出力例: nginx: configuration file /etc/nginx/nginx.conf test is successful
```

##### Step 7: Dockerコンテナの再起動
```bash
# Nginxコンテナのみ再起動
docker compose restart nginx
# 出力例: [+] Restarting 1/1 ✔ Container docker-nginx-1 Started 10.7s

# 再起動後の確認
docker ps | grep nginx
# 出力例: docker-nginx-1 nginx:latest "sh -c 'cp /docker-..." About a minute ago Up About a minute
```

##### Step 8: 設定反映の確認
```bash
# 生成された実際の設定ファイル確認
cat nginx/conf.d/default.conf | grep -A 4 -B 1 patent
# 出力例:
#       location /patent {
#         proxy_pass http://172.17.0.1:5000;
#         include proxy.conf;
#       }
```

##### Step 9: アクセステストと動作確認
```bash
# ローカルからHTTPSアクセステスト
curl -v https://djartipy.com/patent
# 正常な場合: HTTP/1.1 200 OK と特許アプリのHTMLが返される

# リアルタイムログ監視（別ターミナル推奨）
docker logs -f docker-nginx-1

# 実際のアクセスでログ確認
# ブラウザで https://djartipy.com/patent にアクセス
# ログに以下が出力されることを確認:
# 162.43.36.98 - - [21/Jul/2025:02:46:23 +0000] "GET /patent HTTP/1.1" 200 13422
```

##### トラブルシューティング

**よくある問題と対処法**:

1. **編集中にファイルが壊れた場合**
```bash
# バックアップから復元
cp nginx/conf.d/default.conf.template.backup nginx/conf.d/default.conf.template

# 復元確認
cat nginx/conf.d/default.conf.template
```

2. **viエディタで編集に失敗した場合**
```bash
# 編集モードを抜ける: Esc
# 保存せずに終了: :q!
# 再度編集開始: vi nginx/conf.d/default.conf.template
```

3. **Docker再起動後に設定が反映されない場合**
```bash
# テンプレートファイルが正しく編集されているか確認
grep -n "patent" nginx/conf.d/default.conf.template

# 生成された設定ファイルを確認
grep -n "patent" nginx/conf.d/default.conf

# 必要に応じて全コンテナ再起動
docker compose down && docker compose up -d
```

4. **404エラーが継続する場合**
```bash
# 特許アプリが起動しているか確認
ss -tlnp | grep 5000

# パスの順序確認（/patent が / より前にあるか）
cat nginx/conf.d/default.conf.template | grep -n "location"

# Dockerコンテナからの直接アクセステスト
docker exec docker-nginx-1 curl http://172.17.0.1:5000
```

##### 設定のポイント
1. **パスリライト**: `rewrite ^/patent/?(.*) /$1 break;`
   - `/patent` → `/` にリライト
   - `/patent/upload` → `/upload` にリライト
   - `/patent/ask` → `/ask` にリライト

2. **Dockerネットワーキング**: `http://172.17.0.1:5000`
   - DockerコンテナからホストシステムへのアクセスにはブリッジゲートウェイIPを使用
   - `host.docker.internal:5000`は環境によって動作しない場合がある

3. **設定順序**: `/patent`設定を`/`設定より前に配置
   - Nginxは上から順にマッチングするため、順序が重要

##### Docker再起動とテスト
```bash
# Nginxコンテナの再起動
cd /root/dify/docker
docker compose restart nginx

# 設定確認
cat nginx/conf.d/default.conf | grep -A 4 -B 1 patent

# HTTPSアクセステスト
curl -v https://djartipy.com/patent
```

### 本番環境での技術的考慮事項

#### セキュリティ
- APIキーは環境変数で管理
- FLASK_DEBUG=Falseに設定
- HTTPSのみでアクセス可能
- Let's Encryptによる自動SSL証明書管理

#### パフォーマンス
- Dockerコンテナ間通信の最適化
- Nginxプロキシバッファリング設定
- 特許アプリの軽量化（ChromaDB in-memory）

#### 監視とログ
```bash
# Nginxアクセスログの確認
docker logs docker-nginx-1 --tail 50

# 特許アプリのログ確認
cd /opt/projects/patent_langchain
tail -f logs/app.log  # ログファイルが設定されている場合
```

### トラブルシューティング

#### よくある問題と解決法

1. **404エラーが返される**
   ```bash
   # Dockerコンテナからホストへの接続確認
   docker exec docker-nginx-1 curl -v http://172.17.0.1:5000
   
   # 特許アプリの起動状態確認
   ss -tlnp | grep 5000
   ```

2. **設定が反映されない**
   ```bash
   # テンプレートファイルの編集確認
   cat /root/dify/docker/nginx/conf.d/default.conf.template | grep patent
   
   # Docker Compose再起動
   docker compose restart nginx
   ```

3. **パスリライトが動作しない**
   - `/patent`設定が`/`設定より前にあることを確認
   - `rewrite`ディレクティブの構文チェック

### システム運用

#### 自動起動設定（今後の改善）
- systemdサービス化による自動起動
- プロセス監視とヘルスチェック
- ログローテーション設定

#### バックアップ
- 設定ファイルのバージョン管理
- アップロードファイルのバックアップ
- データベースの定期バックアップ

---

**最終更新**: 2025年7月21日  
**作成者**: Claude Code (Anthropic)