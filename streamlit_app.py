import streamlit as st
from BACKEND.src.rag_pipeline import build_rag_pipeline
import re

def load_css_from_html():
    with open("FRONTEND/templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Extract CSS inside <style>...</style>
    css = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    
    if css:
        st.markdown(f"<style>{css.group(1)}</style>", unsafe_allow_html=True)

load_css_from_html()
st.title("🌾 Bhoomi - Smart Farming Assistant")

@st.cache_resource
def load_rag():
    return build_rag_pipeline(rebuild=False)

rag = load_rag()

user_input = st.text_input("Ask your question")

if user_input:
    response = rag.invoke(user_input)
    st.write(response)
