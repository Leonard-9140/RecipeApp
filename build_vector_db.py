import os
import chromadb
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# 本地食譜資料夾的路徑
RECIPE_REPO_PATH = "HowToCook_repo"
# ChromaDB 儲存的路徑
CHROMA_DB_PATH = "chroma_db"

def build_database():
    """
    讀取食譜文件，分割它們，產生向量，並存入 ChromaDB。
    """
    if os.path.exists(CHROMA_DB_PATH):
        print(f"向量資料庫 '{CHROMA_DB_PATH}' 已存在，無需重建。")
        print("如果需要強制重建，請先手動刪除此資料夾。")
        return

    print("正在建立向量資料庫，這可能需要幾分鐘時間...")

    # 1. 載入所有食譜文件
    # 我們只處理菜譜部分，忽略其他說明文件
    recipes_path = os.path.join(RECIPE_REPO_PATH, "dishes")
    if not os.path.exists(recipes_path):
        print(f"錯誤：找不到食譜路徑 '{recipes_path}'")
        print("請先確認 `prepare_recipes.py` 已成功執行。")
        return
        
    loader = DirectoryLoader(
        recipes_path, 
        glob="**/*.md", # 尋找所有子資料夾中的 .md 檔案
        loader_cls=UnstructuredMarkdownLoader,
        show_progress=True,
        use_multithreading=True
    )
    documents = loader.load()
    print(f"成功載入 {len(documents)} 份食譜文件。")

    # 2. 分割文件成小區塊
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=750, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)
    print(f"文件被分割成 {len(docs)} 個區塊。")

    # 3. 初始化 Ollama 的向量模型
    # gemma:2b 也可以用來產生高品質的文字向量
    embeddings = OllamaEmbeddings(model="gemma:2b")
    print("Ollama 向量模型已初始化。")

    # 4. 建立並儲存向量資料庫
    print("正在將文件區塊轉換成向量並存入資料庫...")
    # 這一步會呼叫 Ollama 進行大量運算
    vectorstore = Chroma.from_documents(
        documents=docs, 
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH # 指定儲存路徑
    )
    print("向量資料庫建立完成！")
    print(f"資料庫已儲存至 '{CHROMA_DB_PATH}' 資料夾。")

if __name__ == "__main__":
    build_database()