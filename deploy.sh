#!/bin/bash

# XserverVPS用 特許検索アプリケーション デプロイスクリプト
# 使用方法: bash deploy.sh

set -e

echo "=========================================="
echo "特許検索アプリケーション デプロイ開始"
echo "=========================================="

# 必要なツールの確認
command -v python3 >/dev/null 2>&1 || { echo "Python3が見つかりません。インストールしてください。"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "Gitが見つかりません。インストールしてください。"; exit 1; }

# プロジェクトディレクトリに移動
PROJECT_DIR="patent_langchain"
if [ ! -d "$PROJECT_DIR" ]; then
    echo "GitHubからプロジェクトをクローン中..."
    git clone https://github.com/tinyoko/patent_langchain.git
    cd $PROJECT_DIR
else
    echo "既存のプロジェクトディレクトリを使用します..."
    cd $PROJECT_DIR
    echo "最新の変更を取得中..."
    git pull origin main
fi

# Python仮想環境の作成
echo "Python仮想環境をセットアップ中..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "仮想環境を作成しました。"
else
    echo "既存の仮想環境を使用します。"
fi

# 仮想環境の有効化
echo "仮想環境を有効化中..."
source venv/bin/activate

# pipのアップグレード
echo "pipをアップグレード中..."
pip install --upgrade pip

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install -r requirements.txt

# 必要なディレクトリの作成
echo "必要なディレクトリを作成中..."
mkdir -p uploads
mkdir -p chroma_db

# 環境設定ファイルの確認
if [ ! -f ".env" ]; then
    echo "環境設定ファイル(.env)が見つかりません。"
    echo ".env.exampleを.envにコピーしています..."
    cp .env.example .env
    echo ""
    echo "⚠️  重要: .envファイルを編集して、以下の設定を行ってください："
    echo "   - OPENAI_API_KEY: OpenAIのAPIキー"
    echo "   - SERP_API_KEY: SerpAPIのAPIキー"
    echo "   - FLASK_SECRET_KEY: Flaskのシークレットキー"
    echo ""
    echo "設定完了後、再度このスクリプトを実行してください。"
    exit 1
fi

# 環境変数の確認
echo "環境変数を確認中..."
source .env

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ OPENAI_API_KEYが設定されていません。.envファイルを確認してください。"
    exit 1
fi

if [ -z "$SERP_API_KEY" ] || [ "$SERP_API_KEY" = "your_serpapi_key_here" ]; then
    echo "❌ SERP_API_KEYが設定されていません。.envファイルを確認してください。"
    exit 1
fi

echo "✅ 環境変数の設定が確認できました。"

# アプリケーションの起動
echo ""
echo "=========================================="
echo "アプリケーションを起動しています..."
echo "=========================================="
echo ""
echo "🚀 アプリケーションが起動しました！"
echo "📍 アクセスURL: http://$(hostname -I | awk '{print $1}'):5000"
echo "🛑 停止するには Ctrl+C を押してください"
echo ""

# Flaskアプリケーションの実行
export FLASK_APP=app.py
python app.py