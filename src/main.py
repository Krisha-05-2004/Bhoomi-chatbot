# main.py
import sys
from flask import Flask, render_template, request, jsonify
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from rag_pipeline import build_rag_pipeline
from prompt import MAIN_PROMPT
import os
try:
    import openai
except Exception:
    openai = None
from tempfile import NamedTemporaryFile
from werkzeug.utils import secure_filename
import mimetypes
try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None
try:
    import docx
except Exception:
    docx = None
try:
    from langdetect import detect as detect_lang
except Exception:
    # fallback: if langdetect isn't installed we'll return 'und' (undetermined)
    def detect_lang(_text):
        return 'und'

# ====== Conversation Memory ======
chat_history = []
MAX_HISTORY = 6  # Number of previous exchanges Bhoomi remembers

app = Flask(__name__, template_folder="../templates")

# Simple in-memory feedback store: { msg_id: { 'up': int, 'down': int } }
feedback_store = {}

# Load API key locally from replacements.txt
with open(Path(__file__).parent.parent / "replacements.txt", "r") as f:
    OPENAI_API_KEY = f.read().strip()
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if openai is not None:
    openai.api_key = os.environ.get("OPENAI_API_KEY")
else:
    print("⚠️ Warning: openai package not available. /transcribe endpoint will be disabled.")

# Path to your data folder
data_path = Path(__file__).parent.parent / "data"

print("⚙️ Loading Bhoomi RAG pipeline...")
qa_main = build_rag_pipeline(data_path, prompt=MAIN_PROMPT, rebuild=False)

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
        data = request.get_json() or {}
        question = data.get("question", "").strip()
        lang = data.get("lang", "en-IN")  # Default to English if not specified

        if not question:
            return jsonify({"answer": "⚠️ Please enter a question."})

        # Keep conversation memory (simple list)
        context = "\n".join([
            f"User: {m['user']}\nBhoomi: {m['bot']}" for m in chat_history[-MAX_HISTORY:]
        ])
        full_query = f"{context}\nUser ({lang}): {question}\nBhoomi:"

        # Use server-side RAG pipeline (owner-provided key/config). Do not accept client API keys.
        response = qa_main({"query": full_query}) if qa_main else {"result": "⚠️ Model not loaded."}
        # Some pipelines return 'result' and some 'answer'
        answer = response.get("result") or response.get("answer") or "⚠️ Couldn't generate an answer."

        # Save this exchange
        chat_history.append({"user": question, "bot": answer})
        if len(chat_history) > MAX_HISTORY:
            chat_history.pop(0)

        return jsonify({"answer": answer})
    except Exception as e:
        print("⚠️ Error:", e)
        return jsonify({"answer": f"⚠️ Error: {str(e)}"})


@app.route("/upload", methods=["POST"])
def upload():
    try:
        file = request.files.get('image')
        # Implement your image analysing logic here
        # For demo, just return file name
        if not file:
            return jsonify({"answer": "⚠️ No file uploaded."})

        answer = f"Received your image: {file.filename}. Processing result to be implemented."
        return jsonify({"answer": answer})
    except Exception as e:
        print("⚠️ Error in upload:", e)
        return jsonify({"answer": f"⚠️ Error: {str(e)}"})


@app.route("/transcribe", methods=["POST"])
def transcribe_audio():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file uploaded."}), 400

        audio = request.files['audio']
        # save temporarily
        with NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            audio.save(tmp.name)
            tmp_path = tmp.name

        # call OpenAI Whisper via openai sdk
        if openai is None:
            return jsonify({"error": "OpenAI SDK not installed on server."}), 500
        # Ensure server has an OpenAI API key configured
        if not getattr(openai, 'api_key', None):
            return jsonify({"error": "OpenAI API key not configured on server."}), 500
        with open(tmp_path, "rb") as af:
            # use the SDK's transcribe method; adjust if your openai package version differs
            resp = openai.Audio.transcribe("whisper-1", af)
        transcript = resp.get('text', '')

        # detect language from transcript (fallback to 'und')
        try:
            lang = detect_lang(transcript)
        except Exception:
            lang = 'und'

        # cleanup temporary file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        return jsonify({"transcript": transcript, "lang": lang})
    except Exception as e:
        print("⚠️ Transcription error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/upload_doc", methods=["POST"])
def upload_doc():
    try:
        files = request.files.getlist('docs')
        if not files:
            return jsonify({"error": "No files uploaded."}), 400

        texts = []
        filenames = []
        for f in files:
            filename = secure_filename(f.filename)
            filenames.append(filename)
            suffix = os.path.splitext(filename)[1].lower()
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                f.save(tmp.name)
                tmp_path = tmp.name

            extracted = ''
            try:
                if suffix == '.pdf' and PdfReader is not None:
                    reader = PdfReader(tmp_path)
                    pages = []
                    for p in reader.pages:
                        try:
                            pages.append(p.extract_text() or '')
                        except Exception:
                            pages.append('')
                    extracted = '\n'.join(pages)
                elif suffix in ('.txt', '.md'):
                    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as fh:
                        extracted = fh.read()
                elif suffix in ('.docx',) and docx is not None:
                    doc = docx.Document(tmp_path)
                    extracted = '\n'.join(p.text for p in doc.paragraphs)
                else:
                    # attempt to read as text fallback
                    with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as fh:
                        extracted = fh.read()
            except Exception as e:
                print(f"⚠️ Failed to extract {filename}:", e)
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            if extracted:
                texts.append(f"--- FILE: {filename} ---\n" + extracted)

        if not texts:
            return jsonify({"error": "No readable text extracted from uploaded files."}), 400

        # combine but limit size to avoid very large prompts
        combined = "\n\n".join(texts)
        max_chars = 3000
        payload_text = combined if len(combined) <= max_chars else combined[:max_chars]

        if openai is None:
            return jsonify({"error": "OpenAI SDK not available on server; cannot summarize."}), 500
        if not getattr(openai, 'api_key', None):
            return jsonify({"error": "OpenAI API key not configured on server."}), 500
        system = "You are Bhoomi, an assistant for farmers. Summarize the uploaded documents and produce: 1) a short plain-language summary (3-6 lines), 2) 5 actionable tips, 3) 3 FAQ-style Q&A derived from the content. Keep language concise and farmer-friendly."
        user_prompt = f"Summarize the following document content and extract key points:\n\n{payload_text}"
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user_prompt}],
                max_tokens=800,
                temperature=0.2,
            )
            summary = resp['choices'][0]['message']['content']
        except Exception as e:
            print("⚠️ OpenAI summarize error:", e)
            return jsonify({"error": f"OpenAI error: {str(e)}"}), 500

        return jsonify({"summary": summary, "files": filenames})
    except Exception as e:
        print("⚠️ upload_doc error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/feedback", methods=["POST"])
def feedback():
    """Accept a simple feedback POST with JSON: {id: message_id, type: 'up'|'down'}
    Returns the updated counts for that message.
    This is an in-memory store for now.
    """
    try:
        data = request.get_json() or {}
        mid = data.get('id')
        ftype = data.get('type')
        if not mid or ftype not in ('up','down'):
            return jsonify({'error':'missing id or invalid type'}), 400
        entry = feedback_store.get(mid) or {'up':0,'down':0}
        if ftype == 'up':
            entry['up'] = entry.get('up',0) + 1
        else:
            entry['down'] = entry.get('down',0) + 1
        feedback_store[mid] = entry
        return jsonify(entry)
    except Exception as e:
        print('⚠️ Feedback error:', e)
        return jsonify({'error': str(e)}), 500


@app.route('/feedback_counts', methods=['GET'])
def feedback_counts():
    mid = request.args.get('id')
    if not mid:
        return jsonify({'error':'missing id'}), 400
    entry = feedback_store.get(mid) or {'up':0,'down':0}
    return jsonify(entry)

if __name__ == "__main__":
    # Start the Flask development server (original simple behavior)
    app.run(debug=True)
