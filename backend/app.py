from flask import Flask, jsonify, request
from flask_cors import CORS
from agent import ask
app = Flask(__name__)
CORS(app)   
@app.get("/health")
def health():
    return jsonify({"status": "ok"})
@app.post("/ask")
def ask_endpoint():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Please send a question."}), 400
    if len(question) > 500:
        return jsonify({"error": "Question is too long (max 500 characters)."}), 400
    try:
        return jsonify(ask(question))
    except Exception as e:
        return jsonify({"error": f"The AI service had a problem: {str(e)[:200]}"}), 502
if __name__ == "__main__":
    app.run(port=5000, debug=True)