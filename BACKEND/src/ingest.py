from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_and_split_pdfs(pdf_dir):
    pdf_dir = Path(pdf_dir)
    pdf_files = list(pdf_dir.rglob("*.pdf"))  # 👈 FIX HERE

    if not pdf_files:
        raise ValueError(
            f"No PDF files found in {pdf_dir}. "
            "Please add at least one PDF to data/raw/"
        )

    documents = []
    for pdf in pdf_files:
        loader = PyPDFLoader(str(pdf))
        documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    return splitter.split_documents(documents)
