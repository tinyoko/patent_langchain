from flask import Flask, render_template, request, jsonify, g, redirect, url_for, flash
from werkzeug.utils import secure_filename
from typing import Literal
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from serpapi import GoogleSearch
import os
import config

# === Flask アプリケーションの設定 ===
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# ディレクトリ作成
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

# === グローバル変数 ===
embeddings_model = None
db = None
app_flow = None

def allowed_file(filename):
    """アップロードファイルが許可された拡張子かチェック"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def setup_rag_system(pdf_path):
    """RAGシステムのセットアップ"""
    global embeddings_model, db, app_flow
    
    # PDFローダーでドキュメントを読み込み
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    
    # テキストを分割
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    split_docs = text_splitter.split_documents(documents)
    
    # OpenAIの埋め込みモデルを設定
    embeddings_model = OpenAIEmbeddings(
        api_key=config.OPENAI_API_KEY,
        model="text-embedding-3-small"
    )
    
    # Chromaデータベースを作成
    db = Chroma.from_documents(
        documents=split_docs,
        embedding=embeddings_model,
        persist_directory=config.CHROMA_PERSIST_DIRECTORY
    )
    
    # LangGraphワークフローを設定
    setup_workflow()

def setup_workflow():
    """LangGraphワークフローの設定"""
    global app_flow
    
    # === プロンプトテンプレート ===
    template = """
あなたは特許公開公報の内容とWeb検索を活用して質問に答える特許情報アシスタントです。
以下の特許文書抜粋を参照して質問に答えるか、必要に応じて"patent_search"ツールを使用してください。

特許文書抜粋：{document_snippet}

質問：{question}

答え：特許の技術的内容、先行技術、発明の効果などを詳しく説明してください。
関連する特許や技術情報があれば併せて提供してください。

"""

    # === ツールの設定 ===
    @tool
    def patent_search(query: str):
        """特許関連の情報をWeb検索で取得します。"""
        params = {
            "q": f"特許 {query}",  # 検索クエリに「特許」を追加
            "hl": "ja",  # 言語設定（日本語）
            "gl": "jp",  # 地域設定（日本）
            "api_key": config.SERP_API_KEY  # SerpAPIのAPIキー
        }
        
        search = GoogleSearch(params)
        result = search.get_dict()
        
        results_list = result.get("organic_results", [])
        search_results = [
            f"{res['title']}: {res['snippet']} - {res['link']}" 
            for res in results_list[:5]  # 特許情報なので5件に拡張
        ]

        g.search_results = search_results if search_results else ["関連する特許情報が見つかりませんでした。"]
        return g.search_results

    tools = [patent_search]
    tool_node = ToolNode(tools)

    # === モデルのセットアップ ===
    model = ChatOpenAI(
        api_key=config.OPENAI_API_KEY, 
        model_name="gpt-4o-mini"
    ).bind_tools(tools)

    # === 条件判定 ===
    def should_continue(state: MessagesState) -> Literal["tools", END]:
        messages = state['messages']
        last_message = messages[-1]
        
        if last_message.tool_calls:
            return "tools"
        
        if "patent_search" in last_message.content or "検索" in last_message.content:
            return "tools"
        
        return END

    # === モデルの応答生成関数 ===
    def call_model(state: MessagesState):
        messages = state['messages']
        response = model.invoke(messages)
        return {"messages": [response]}

    # === RAG用ロジック ===
    def rag_retrieve(question: str):
        if db is None:
            return "特許文書がアップロードされていません。"
        
        question_embedding = embeddings_model.embed_query(question)
        docs = db.similarity_search_by_vector(question_embedding, k=5)  # より多くの関連文書を取得
        return "\n".join([doc.page_content for doc in docs])

    # === メッセージの前処理 ===
    def preprocess_message(question: str):
        document_snippet = rag_retrieve(question)
        content = template.format(document_snippet=document_snippet, question=question)
        return [HumanMessage(content=content)]

    # グローバル関数として設定
    global preprocess_message_global
    preprocess_message_global = preprocess_message

    # === ワークフローの構築 ===
    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("tools", 'agent')
    
    checkpointer = MemorySaver()
    app_flow = workflow.compile(checkpointer=checkpointer)

# === Flaskルート設定 ===
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        flash('ファイルが選択されていません')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('ファイルが選択されていません')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        try:
            # RAGシステムをセットアップ
            setup_rag_system(file_path)
            flash('特許文書のアップロードと処理が完了しました')
            return jsonify({"success": True, "message": "特許文書の処理が完了しました"})
        except Exception as e:
            flash(f'ファイル処理中にエラーが発生しました: {str(e)}')
            return jsonify({"success": False, "error": str(e)})
    else:
        flash('PDFファイルのみアップロード可能です')
        return jsonify({"success": False, "error": "PDFファイルのみアップロード可能です"})

@app.route("/ask", methods=["POST"])
def ask():
    if app_flow is None:
        return jsonify({"error": "先に特許文書をアップロードしてください"})
    
    question = request.form["question"]
    inputs = preprocess_message_global(question)
    
    # スレッドIDを設定
    thread = {"configurable": {"thread_id": "patent_analysis"}}

    # ワークフローをストリームモードで実行
    for event in app_flow.stream({"messages": inputs}, thread, stream_mode="values"):
        response = event["messages"][-1].content

    search_results = getattr(g, "search_results", [])
    links = "\n".join(search_results) if search_results else "関連する特許情報は見つかりませんでした"

    return jsonify({"answer": response, "links": links})

@app.route("/reset", methods=["POST"])
def reset():
    """データベースとワークフローをリセット"""
    global db, app_flow
    db = None
    app_flow = None
    
    # アップロードファイルを削除
    for filename in os.listdir(config.UPLOAD_FOLDER):
        file_path = os.path.join(config.UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
    
    return jsonify({"success": True, "message": "システムがリセットされました"})

# === Flaskの起動 ===
if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)