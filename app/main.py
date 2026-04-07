from flask import Flask, jsonify, render_template, request

from rules import diagnose

app = Flask(__name__)


@app.route("/")
def index():
    """首页：输入业务问题并查看诊断结果。"""
    return render_template("index.html")


@app.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    """诊断 API：接收文本，返回结构化判断。"""
    payload = request.get_json(silent=True) or {}
    problem_text = payload.get("problem", "")
    result = diagnose(problem_text)
    return jsonify(result)


if __name__ == "__main__":
    # 本地启动：python app/main.py
    app.run(host="127.0.0.1", port=5000, debug=True)
