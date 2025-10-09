import os
import time
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI

from prompt import MAIN_PROMPT

# Load .env
load_dotenv(Path(__file__).parent.parent / ".env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found in .env")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def build_rag_pipeline(data_folder, prompt=MAIN_PROMPT, batch_size=10, rebuild=False):
    data_folder = Path(data_folder).resolve()
    vectorstore_path = data_folder / "vector_db"
    print(f"⚙️ Loading data from: {data_folder}")

    if not data_folder.exists():
        print(f"❌ Data folder not found: {data_folder}")
        return None

    embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, model="text-embedding-3-small")

    if vectorstore_path.exists() and not rebuild:
        try:
            print("🔁 Loading existing FAISS vectorstore...")
            vectorstore = FAISS.load_local(str(vectorstore_path), embeddings, allow_dangerous_deserialization=True)
            print(f"✅ Vectorstore loaded with {len(vectorstore.index_to_docstore_id)} vectors.")
        except Exception as e:
            print(f"⚠️ Failed to load FAISS DB: {e}, rebuilding...")
            vectorstore = None
    else:
        vectorstore = None

    if vectorstore is None:
        pdf_files = list(data_folder.rglob("*.pdf"))
        if not pdf_files:
            print("⚠️ No PDFs found in data folder.")
            return None

        print(f"📚 Found {len(pdf_files)} PDF files.")
        documents = []
        for pdf_path in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_path))
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                print(f"⚠️ Skipping {pdf_path.name}: {e}")

        if not documents:
            print("⚠️ No pages loaded from PDFs.")
            return None

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(documents)
        print(f"🧩 Split into {len(chunks)} chunks.")

        vectorstore = None
        for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
            batch = chunks[i:i + batch_size]
            temp_store = FAISS.from_documents(batch, embeddings)
            if vectorstore is None:
                vectorstore = temp_store
            else:
                vectorstore.merge_from(temp_store)
            time.sleep(1.5)

        vectorstore.save_local(str(vectorstore_path))
        print(f"💾 Saved vectorstore to: {vectorstore_path}")

    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini", temperature=0)

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )
    print("🤖 Bhoomi RAG pipeline ready!")
    return qa
