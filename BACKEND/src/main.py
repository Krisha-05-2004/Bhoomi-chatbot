
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

from flask import Flask, request, jsonify, render_template
app = Flask(__name__, template_folder="FRONTEND/templates", static_folder="FRONTEND/static")

from dotenv import load_dotenv
from textblob import TextBlob
from .llm import get_llm

from .rag_pipeline import build_rag_pipeline
from .utils import build_context
from config import MAX_HISTORY

load_dotenv()

app = Flask(
    __name__,
    template_folder=str(BASE_DIR.parent / "FRONTEND" / "templates"),
    static_folder=str(BASE_DIR.parent / "FRONTEND" / "static")
)

qa = build_rag_pipeline(rebuild=False)

chat_history = []
feedback_store = {}

def convert_table_to_html(text):
    lines = text.strip().split("\n")

    if "|" not in text:
        return text

    table_html = "<table border='1' style='border-collapse: collapse; width:100%;'>"

    for i, line in enumerate(lines):
        if "|" in line:
            columns = [col.strip() for col in line.split("|") if col.strip()]

            if i == 0:
                table_html += "<tr>" + "".join(f"<th>{col}</th>" for col in columns) + "</tr>"
            else:
                table_html += "<tr>" + "".join(f"<td>{col}</td>" for col in columns) + "</tr>"

    table_html += "</table>"

    return table_html


@app.route("/")
def home():
    return render_template("index.html")
# other routes like /ask etc.

if __name__ == "__main__":
    app.run()

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    lang = data.get("lang", "en")
    lang = lang.split("-")[0]
    
    
    # Bullet formatting
    if "points" in question.lower():
        question += "\nAnswer strictly in this format:\n1. Point\n2. Point\n3. Point\nDo not use markdown symbols."
    
    # Table formatting
    if "table" in question.lower():
        question += "\nPresent the answer in a clean table format using | to separate columns. Do not include separator lines like ---."

    context = build_context(chat_history, MAX_HISTORY)

    # Always generate in English (strongest language)
    full_query = f"""
Conversation:
{context}

Answer in clear, simple English suitable for farmers.

User Question:
{question}

Bhoomi:
"""

    response = qa.invoke({"query": full_query})
    answer = response["result"]

    # 🌍 Language Map
    language_map = {
        "kn": "Kannada",
        "hi": "Hindi",
        "te": "Telugu",
        "en": "English"
    }

    target_language = language_map.get(lang, "English")

    # Translate only if needed
    if lang != "en":
        translate_prompt = f"""
Translate the following text into {target_language}.
Use natural, simple language suitable for farmers.
Only provide the translated text.

Text:
{answer}
"""
        llm = get_llm()
        translated = llm.invoke(translate_prompt)
        answer = translated.content if hasattr(translated, "content") else str(translated)

    chat_history.append({"user": question, "bot": answer})
    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)

    # Convert table text to HTML
    def convert_table_to_html(text):
        lines = text.strip().split("\n")

        if "|" not in text:
            return text

        table_html = "<table border='1' style='border-collapse: collapse; width:100%;'>"

        for i, line in enumerate(lines):
            if "|" in line and "---" not in line:

                columns = [col.strip() for col in line.split("|") if col.strip()]
                if i == 0:
                    table_html += "<tr>" + "".join(f"<th>{col}</th>" for col in columns) + "</tr>"
                else:
                    table_html += "<tr>" + "".join(f"<td>{col}</td>" for col in columns) + "</tr>"

        table_html += "</table>"
        return table_html

    formatted_answer = convert_table_to_html(answer)

    return jsonify({"answer": formatted_answer})

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json()
    msg_id = data.get("id")

    feedback_store[msg_id] = feedback_store.get(msg_id, 0) + 1
    return jsonify({"up": feedback_store[msg_id]})


@app.route("/feedback_counts")
def feedback_counts():
    msg_id = request.args.get("id")
    return jsonify({"up": feedback_store.get(msg_id, 0)})


if __name__ == "__main__":
    app.run(debug=False)
