from flask import Flask, jsonify, render_template, request

from rules import diagnose

app = Flask(__name__)

FOLLOW_UP_QUESTIONS = [
    "这个问题目前是否有明确负责人？",
    "这个岗位要解决的是长期问题还是短期问题？",
    "如果不招人，有没有内部调整或外包的可能？",
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start", methods=["POST"])
def api_start():
    payload = request.get_json(silent=True) or {}
    return jsonify(
        {
            "message": "已进入诊断追问阶段。",
            "questions": FOLLOW_UP_QUESTIONS,
            "context": {
                "company_stage": payload.get("company_stage", ""),
                "team_size": payload.get("team_size", ""),
            },
        }
    )


@app.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    payload = request.get_json(silent=True) or {}
    return jsonify(diagnose(payload))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
