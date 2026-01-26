import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.get("/")
def health():
    return jsonify(status="ok")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)