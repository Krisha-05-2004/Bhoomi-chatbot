import streamlit as st
from BACKEND.src.rag_pipeline import build_rag_pipeline

st.title("🌾 Bhoomi - Smart Farming Assistant")

@st.cache_resource
def load_rag():
    return build_rag_pipeline(rebuild=False)

rag = load_rag()

user_input = st.text_input("Ask your question")

if user_input:
    response = rag.invoke(user_input)
    st.write(response)
