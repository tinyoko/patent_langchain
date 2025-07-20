# 特許公開公報 AI検索アシスタント

特許公開公報のPDFファイルをアップロードして、AIによる詳細な分析と関連情報検索を行うWebアプリケーションです。

## 🎯 概要

このアプリケーションは、LangChain、LangGraph、OpenAI、ChromaDBを活用して構築されたRAG（Retrieval-Augmented Generation）システムです。特許文書の内容を理解し、質問に対して詳細な回答を生成するとともに、関連する特許情報をWeb検索で補完します。

## ✨ 主要機能

### 📄 PDFアップロード
- ドラッグ&ドロップ対応のファイルアップロード
- PDFファイル形式の自動検証
- 16MBまでのファイルサイズ制限
- セキュアなファイル名処理

### 🧠 RAGシステム
- 特許文書の自動分割とベクトル化
- OpenAI Embeddingsによる高精度な類似度検索
- ChromaDBによる効率的なベクトルストレージ
- 特許文書に特化したプロンプトエンジニアリング

### 🔍 Web検索機能
- SerpAPIを使用した特許関連情報の検索
- 日本語・日本地域に最適化された検索
- 最大5件の関連特許情報表示

### ⚡ LangGraphワークフロー
- ツール使用可否の自動判定
- メモリ機能付き会話履歴
- ストリーミング応答による快適なUX

## 🚀 セットアップと起動方法

### 前提条件
- Python 3.8以上
- 仮想環境 `langchain` が設定済み
- OpenAI APIキー
- SerpAPI APIキー

### 1. 仮想環境のアクティベート
```bash
# new_appディレクトリで実行（親ディレクトリの仮想環境を使用）
source ../langchain/bin/activate

# Windows の場合
# ..\langchain\Scripts\activate
```

### 2. 依存関係のインストール・確認
```bash
# requirements.txtから必要なライブラリをインストール
pip install -r requirements.txt

# または、インストール済みライブラリの確認
pip list | grep -E "(flask|langchain|openai|chromadb|serpapi)"
```

### 3. 設定ファイルの準備
```bash
# config.py.example をコピーして config.py を作成
cp config.py.example config.py

# config.py を編集してAPIキーを設定
# OPENAI_API_KEY = "your-openai-api-key"
# SERP_API_KEY = "your-serp-api-key"
```

### 4. アプリケーションの起動
```bash
# new_app ディレクトリに移動
cd new_app

# Flaskアプリケーションを起動
python app.py
```

### 5. アクセス
ブラウザで `http://localhost:5000` にアクセス

## 📱 使用方法

### ステップ 1: 特許文書のアップロード
1. ホーム画面のアップロードエリアをクリック、またはPDFファイルをドラッグ&ドロップ
2. 特許公開公報のPDFファイルを選択
3. 「アップロード開始」ボタンをクリック
4. 処理完了メッセージが表示されるまで待機

### ステップ 2: 質問の入力
1. 「特許内容について質問する」セクションに質問を入力
2. 例: 「この特許の技術的特徴は何ですか？」「類似の先行技術はありますか？」
3. 「質問する」ボタンをクリック

### ステップ 3: 結果の確認
- **AI分析結果**: 特許文書の内容に基づいた詳細な回答
- **関連する特許情報**: Web検索による関連特許情報のリンク

### その他の機能
- **システムリセット**: アップロードした文書と分析データをクリア

## 🏗️ 技術スタック

### バックエンド
- **Flask**: Webアプリケーションフレームワーク
- **LangChain**: LLMアプリケーション開発フレームワーク
- **LangGraph**: 複雑なワークフロー管理
- **OpenAI**: GPT-4o-mini & Embeddings API
- **ChromaDB**: ベクトルデータベース
- **SerpAPI**: Web検索API

### フロントエンド
- **HTML5**: セマンティックマークアップ
- **CSS3**: モダンなグラデーションデザイン
- **JavaScript (ES6+)**: 非同期通信とDOM操作

### データ処理
- **PyPDF**: PDFファイル解析
- **RecursiveCharacterTextSplitter**: テキスト分割
- **OpenAI Embeddings**: ベクトル化

## 📂 ファイル構成

```
new_app/
├── app.py                  # メインアプリケーション
├── config.py              # 設定ファイル（Git管理外）
├── config.py.example      # 設定テンプレート
├── requirements.txt       # Python依存関係
├── .gitignore             # Git除外設定
├── templates/
│   └── index.html         # フロントエンドUI
├── uploads/               # PDFアップロード用（Git管理外）
├── chroma_db/            # ChromaDBデータ（Git管理外）
├── README.md             # このファイル
└── CLAUDE.md             # 開発履歴・技術詳細
```

## ⚠️ 注意事項

### セキュリティ
- APIキーは絶対にGitリポジトリにコミットしないでください
- `config.py` は `.gitignore` に含まれています
- アップロードファイルは一時的にサーバーに保存されます

### ファイルサイズ制限
- アップロード可能なPDFファイルは最大16MBです
- 大きなファイルの場合、処理に時間がかかる場合があります

### APIコスト
- OpenAI APIとSerpAPIの使用により料金が発生します
- 使用量を定期的に確認することをお勧めします

## 🛠️ トラブルシューティング

### アプリが起動しない場合
1. 仮想環境がアクティベートされているか確認
2. 必要なライブラリがインストールされているか確認
3. `config.py` が正しく設定されているか確認

### アップロードエラーが発生する場合
1. ファイルがPDF形式であることを確認
2. ファイルサイズが16MB以下であることを確認
3. `uploads/` フォルダの書き込み権限を確認

### 検索結果が表示されない場合
1. SerpAPI APIキーが正しく設定されているか確認
2. インターネット接続を確認
3. APIキーの使用制限に達していないか確認

## 🔄 バージョン情報

- **Version**: 1.0.0
- **Last Updated**: 2025-01-20
- **Python**: 3.8+
- **LangChain**: 0.3.x
- **Flask**: 3.0.x

## 📝 ライセンス

このプロジェクトは学習目的で作成されています。

## 👥 貢献

バグ報告や機能提案は Issues でお知らせください。

---

**注意**: このアプリケーションは教育・研究目的で開発されており、実際の特許分析業務での使用は十分な検証を行ってください。