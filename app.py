from flask import Flask, render_template, request, jsonify
from src.rag_pipeline import build_rag_pipeline
from pathlib import Path
from prompt import MAIN_PROMPT

app = Flask(__name__)
data_path = Path("data")

print("🚀 Building Bhoomi RAG Pipeline...")
qa_main = build_rag_pipeline(data_path, prompt=MAIN_PROMPT)

if not qa_main:
    print("⚠️ Pipeline failed to initialize.")
else:
    print("✅ Bhoomi pipeline is ready!")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_query = data.get("query")

    if not user_query:
        return jsonify({"answer": "⚠️ Please provide a valid question."})

    instruction = """
Answer clearly in simple farmer-friendly language.
Use short sentences and bullet points where needed.
"""

    try:
        full_input = {
            "context": "",
            "question": f"{instruction}\n{user_query}"
        }

        # Run the RAG model
        response = qa_main.run(full_input)
        formatted_response = response.replace("\n", "<br>")
        return jsonify({"answer": formatted_response})

    except Exception as e:
        print("❌ Error:", e)
        return jsonify({"answer": f"⚠️ Error while generating response: {str(e)}"})

if __name__ == "__main__":
    app.run(debug=True)
