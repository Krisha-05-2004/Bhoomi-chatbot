import streamlit as st
from .rag_pipeline import build_rag_pipeline

st.title("🌾 Bhoomi - Smart Farming Assistant")

user_input = st.text_input("Ask your question")

if user_input:
    rag = build_rag_pipeline()
    response = rag.invoke(user_input)
    st.write(response)
