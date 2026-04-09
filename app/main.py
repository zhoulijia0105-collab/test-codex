from flask import Flask, jsonify, render_template, request

from rules import build_restatement, make_decision

app = Flask(__name__)

QUESTIONS = [
    "Q1：这件事如果做好，最终要的结果是什么？",
    "Q2：现在有没有人对这个结果负责？",
    "Q3：是没人会做，还是没人负责？",
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/restate", methods=["POST"])
def api_restate():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "restatement": build_restatement(payload),
            "next_question": QUESTIONS[0],
        }
    )


@app.route("/api/decide", methods=["POST"])
def api_decide():
    payload = request.get_json(silent=True) or {}
    return jsonify(make_decision(payload))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
