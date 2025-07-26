# 特許データベース検索システム

特許データベースから検索し、AIによる詳細な分析と関連情報検索を行うWebアプリケーションです。

## 🎯 概要

このアプリケーションは、pandas、scikit-learn、OpenAIを活用して構築された特許検索・分析システムです。CSV形式の特許データベースから類似度検索で関連特許を発見し、AIによる詳細な技術分析を提供します。

### 🔄 システム概要（2025年7月更新）
- **PDFアップロード型** → **特許データベース検索型** に全面改良
- **TF-IDF + コサイン類似度**による高速検索
- **段階的UI**: 検索→候補表示→選択→詳細→質問→AI回答

## ✨ 主要機能

### 🔍 特許検索システム
- **TF-IDF + コサイン類似度**による高精度な意味的検索
- **CSV特許データベース**から瞬時に関連特許を発見
- **名称・要約・所管部課名**の包括的検索
- **上位3件の候補表示**で効率的な特許発見

### 📋 段階的インタラクション
- **検索**: キーワード入力による自由記述検索
- **候補表示**: 出願番号・名称・筆頭出願人・発明者を表示
- **選択**: クリック選択による直感的操作
- **詳細表示**: 完全な特許情報（登録情報・発明者・要約等）
- **質問**: 選択特許への自由記述質問
- **AI回答**: GPT-4o-mini による詳細技術分析

### 🤖 AI分析機能
- **特許特化プロンプト**による専門的な技術分析
- **CSVデータベース活用**による詳細情報提供
- **技術的特徴・応用分野・競合分析**等の包括的回答
- **事業関連性**の洞察提供

### 💻 モダンUI/UX
- **レスポンシブデザイン**: PC・タブレット・スマートフォン対応
- **カードベースUI**: 直感的な特許選択
- **ローディング表示**: 処理状況の可視化
- **エラーハンドリング**: 堅牢なユーザー体験

## 🚀 セットアップと起動方法

### ローカル環境での開発

#### 前提条件
- Python 3.8以上
- 仮想環境 `langchain` が設定済み
- OpenAI APIキー
- SerpAPI APIキー

#### 1. 仮想環境のアクティベート
```bash
# patent_langchainディレクトリで実行（親ディレクトリの仮想環境を使用）
source ../langchain/bin/activate

# Windows の場合
# ..\\langchain\\Scripts\\activate
```

#### 2. 依存関係のインストール・確認
```bash
# requirements.txtから必要なライブラリをインストール
pip install -r requirements.txt

# または、インストール済みライブラリの確認
pip list | grep -E "(flask|pandas|scikit-learn|openai|serpapi)"
```

#### 3. 設定ファイルの準備
```bash
# .env.example をコピーして .env を作成
cp .env.example .env

# .env を編集してAPIキーを設定
# OPENAI_API_KEY=your-openai-api-key
# SERP_API_KEY=your-serp-api-key
```

#### 4. 特許データファイルの配置
```bash
# 特許データファイルをプロジェクトルートに配置
# ファイル名: right_list_modified.csv
# ※このファイルはGit管理外のため、別途取得が必要
# patent_data_template.csvでヘッダー構造を確認可能
```

#### 5. 新規依存関係のインストール
```bash
# 新しく追加されたライブラリをインストール
pip install pandas==2.2.2 scikit-learn==1.5.1
```

#### 6. アプリケーションの起動
```bash
# patent_langchain ディレクトリで実行
python app.py
```

#### 7. アクセス
ブラウザで `http://localhost:5001` にアクセス（ポート5001に変更）

### 🖥️ XserverVPSでのデプロイ

XserverVPSでこのアプリケーションを運用する場合の手順です。

#### 前提条件
- XserverVPSのインスタンス（Ubuntu 20.04以上推奨）
- SSH接続可能な環境
- Python 3.8以上がインストール済み
- Gitがインストール済み

#### 1. XserverVPSにSSH接続
```bash
# SSHでVPSに接続
ssh your-username@your-vps-ip-address
```

#### 2. 自動デプロイスクリプトの実行
```bash
# GitHubからプロジェクトをクローンしてデプロイ
wget https://raw.githubusercontent.com/tinyoko/patent_langchain/main/deploy.sh
chmod +x deploy.sh
bash deploy.sh
```

または、手動でリポジトリをクローンしてから実行：

```bash
# プロジェクトのクローン
git clone https://github.com/tinyoko/patent_langchain.git
cd patent_langchain

# デプロイスクリプトの実行
bash deploy.sh
```

#### 3. 環境変数の設定
初回実行時に `.env` ファイルが作成されるので、以下を編集：

```bash
# .envファイルを編集
nano .env
```

必要な設定：
```env
OPENAI_API_KEY=your-openai-api-key
SERP_API_KEY=your-serpapi-key
FLASK_SECRET_KEY=your-secret-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

#### 4. 特許データファイルの配置
```bash
# 特許データファイル（right_list_modified.csv）をアップロード
# SCPやFTPを使用してサーバーにファイルを配置
scp right_list_modified.csv your-username@your-vps-ip:/path/to/patent_langchain/
```

#### 5. アプリケーションの起動
```bash
# 設定完了後、再度デプロイスクリプトを実行
bash deploy.sh
```

#### 6. アクセス確認
- ブラウザで `http://your-vps-ip:5000` にアクセス
- ファイアウォールでポート5000が開いていることを確認

## 📱 使用方法

### ステップ 1: 特許検索
1. 「特許検索」セクションにキーワードを入力
2. 例: 「ロボット」「燃料電池」「ガス検知」「人工知能」
3. 「特許を検索」ボタンをクリック
4. 上位3件の候補が類似度順で表示される

### ステップ 2: 特許選択
1. 検索結果の3件から目当ての特許をクリック選択
2. 出願番号・名称・筆頭出願人・発明者を確認
3. 「この特許を選択」ボタンをクリック
4. 目当ての特許がない場合は「別のキーワードで再検索」

### ステップ 3: 特許詳細確認
1. 選択した特許の完全な情報を確認
   - 出願番号・出願日・登録番号・登録日
   - 所管部課名・筆頭出願人・発明者リスト
   - 詳細な要約
2. 「この特許について質問する」ボタンをクリック

### ステップ 4: AI質問・分析
1. 選択した特許に関する質問を入力
2. 例: 「この特許の技術的特徴は何ですか？」「応用分野は？」「競合技術との違いは？」
3. 「質問する」ボタンをクリック
4. GPT-4o-mini による詳細な技術分析を確認

### ステップ 5: 継続利用
- **続けて質問する**: 同じ特許への追加質問
- **新しい特許を検索**: 別の特許検索を開始

## 🏗️ 技術スタック

### バックエンド
- **Flask**: Webアプリケーションフレームワーク
- **pandas**: CSVデータ処理・DataFrameライブラリ
- **scikit-learn**: 機械学習（TF-IDF、コサイン類似度）
- **OpenAI**: GPT-4o-mini API
- **SerpAPI**: Web検索API（将来の拡張用）

### フロントエンド
- **HTML5**: セマンティックマークアップ
- **CSS3**: モダンなグラデーションデザイン
- **JavaScript (ES6+)**: 非同期通信とDOM操作

### データ処理
- **CSV**: 構造化特許データ
- **TF-IDF Vectorization**: 文書ベクトル化
- **Cosine Similarity**: 文書類似度計算
- **Data Normalization**: 改行文字正規化、欠損値処理

## 📂 ファイル構成

```
patent_langchain/
├── app.py                     # メインアプリケーション
├── config.py                  # 設定ファイル（Git管理外）
├── config.py.example          # 設定テンプレート
├── requirements.txt           # Python依存関係
├── patent_data_template.csv   # 特許データテンプレート（ヘッダーのみ）
├── right_list_modified.csv   # 特許データ（Git管理外）
├── .env                       # 環境変数（Git管理外）
├── .env.example               # 環境変数テンプレート
├── .gitignore                # Git除外設定
├── templates/
│   └── index.html             # 改良されたフロントエンドUI
├── uploads/                   # ファイル用（Git管理外）
├── chroma_db/                # データベース用（Git管理外）
├── README.md                 # このファイル
├── CLAUDE.md                 # 開発履歴・技術詳細
├── deploy.sh                 # デプロイスクリプト
└── run.sh                    # 起動スクリプト
```

## ⚠️ 注意事項

### セキュリティ
- APIキーは絶対にGitリポジトリにコミットしないでください
- `config.py` は `.gitignore` に含まれています
- 特許データファイルは機密性を考慮してGit管理外にしています

### データファイル要件
- `right_list_modified.csv` が必須です
- ファイルが存在しない場合、アプリケーションは起動時にエラーになります
- `patent_data_template.csv` でヘッダー構造を確認できます

### APIコスト
- OpenAI APIとSerpAPIの使用により料金が発生します
- 使用量を定期的に確認することをお勧めします

## 🛠️ トラブルシューティング

### アプリが起動しない場合
1. 仮想環境がアクティベートされているか確認
2. 必要なライブラリがインストールされているか確認
3. `config.py` が正しく設定されているか確認
4. `right_list_modified.csv` ファイルが存在するか確認

### 検索結果が表示されない場合
1. 特許データファイルが正しく配置されているか確認
2. 検索キーワードを変更してみる
3. ファイルの文字エンコーディングを確認

### 依存関係エラーが発生する場合
1. `pip install pandas==2.2.2 scikit-learn==1.5.1` を実行
2. 仮想環境が正しくアクティベートされているか確認

## 🔄 バージョン情報

- **Version**: 2.0.0（特許データベース検索システム）
- **Last Updated**: 2025-07-25
- **Python**: 3.8+
- **Flask**: 3.0.x
- **pandas**: 2.2.2
- **scikit-learn**: 1.5.1
- **OpenAI**: 1.47.0

## 📝 ライセンス

このプロジェクトは学習目的で作成されています。

## 👥 貢献

バグ報告や機能提案は Issues でお知らせください。

---

**注意**: このアプリケーションは教育・研究目的で開発されており、実際の特許分析業務での使用は十分な検証を行ってください。