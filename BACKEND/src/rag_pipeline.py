import os
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

from .ingest import load_and_split_pdfs
from .llm import get_llm
from config import RAW_DATA_DIR, VECTORSTORE_DIR



def build_rag_pipeline(rebuild=True):
    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-base"
    )

    index_file = VECTORSTORE_DIR / "index.faiss"

    if index_file.exists() and not rebuild:
        print("Loading existing vectorstore...")
        vectorstore = FAISS.load_local(
            str(VECTORSTORE_DIR),
            embeddings,
            allow_dangerous_deserialization=True
        )
    else:
        print("Building vectorstore from PDFs...")
        chunks = load_and_split_pdfs(RAW_DATA_DIR)
        vectorstore = FAISS.from_documents(chunks, embeddings)
        vectorstore.save_local(str(VECTORSTORE_DIR))

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 10}
        )
    template = """
    You are Bhoomi 🌱, a smart and friendly farming expert.

IMPORTANT RULES:
- Do NOT introduce yourself again if the conversation is continuing.
- Only introduce yourself once at the beginning of the conversation.
- Do NOT repeat greetings like "Hello" in every response.
- Be concise unless the user asks for detail.
- Speak naturally like a knowledgeable mentor.

Context:
{context}

Question:
{question}

Answer clearly and conversationally:
"""

    QA_PROMPT = PromptTemplate(
        input_variables=["context", "question"],
        template=template,
        )

    return RetrievalQA.from_chain_type(
        llm=get_llm(),
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": QA_PROMPT},
        )