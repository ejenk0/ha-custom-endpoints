from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong", "date": datetime.now().isoformat()})


if __name__ == "__main__":
    app.run(debug=True)
