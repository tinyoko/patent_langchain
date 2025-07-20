#!/bin/bash

# 特許検索アプリケーション起動スクリプト (XserverVPS用)

# エラー時に停止
set -e

echo "=== 特許検索アプリケーション デプロイ開始 ==="

# Python仮想環境の作成
if [ ! -d "venv" ]; then
    echo "Python仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境の有効化
echo "仮想環境を有効化中..."
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

# 設定ファイルの確認
if [ ! -f "config.py" ]; then
    echo "警告: config.py が見つかりません。config.py.example をコピーして設定してください。"
    cp config.py.example config.py
    echo "config.py を作成しました。APIキーを設定してください。"
    exit 1
fi

# ChromaDBディレクトリの作成
mkdir -p chroma_db
mkdir -p uploads

# アプリケーションの起動
echo "アプリケーションを起動中..."
export FLASK_APP=app.py
export FLASK_ENV=production
python app.py

echo "=== アプリケーション起動完了 ==="