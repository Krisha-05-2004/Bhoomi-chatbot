# main.py
import sys
from flask import Flask, render_template, request, jsonify
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from rag_pipeline import build_rag_pipeline
from prompt import MAIN_PROMPT

app = Flask(__name__, template_folder="../templates")

# Path to your data folder
data_path = Path(__file__).parent.parent / "data"

print("⚙️ Loading Bhoomi RAG pipeline...")
qa_main = build_rag_pipeline(data_path, prompt=MAIN_PROMPT)

if qa_main:
    print("✅ Bhoomi RAG pipeline ready!")
else:
    print("⚠️ Pipeline initialization failed!")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        question = data.get("question", "").strip()

        if not question:
            return jsonify({"answer": "⚠️ Please enter a question."})

        # Query Bhoomi RAG
        response = qa_main({"query": question}) if qa_main else {"result": "⚠️ Model not loaded."}
        answer = response.get("result", "⚠️ Couldn't generate an answer.")
        return jsonify({"answer": answer})

    except Exception as e:
        print("⚠️ Error:", e)
        return jsonify({"answer": f"⚠️ Error: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
