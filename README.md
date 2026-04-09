# 招聘决策对话工具（MVP）

这是一个帮助老板判断“是否应该通过招聘解决问题”的顾问式对话工具，而不是简单判断“要不要招人”。

## 功能特点

- 先进行**结构化问题复述**。
- 严格按三轮递进提问：
  1. 这件事如果做好，最终要的结果是什么？
  2. 现在有没有人对这个结果负责？
  3. 是没人会做，还是没人负责？
- 输出有立场的**判断句**。
- 拆分为：
  - 可以通过招聘解决的部分
  - 不能通过招聘解决的部分
- 仅在确实需要招聘时输出**人才画像（最多3点）**。
- 最后只给出**唯一建议**。
- 前端分步骤展示，全程对用户展示自然语言，不直接展示 JSON。

## 技术栈

- Python 3.10+
- Flask
- HTML + 原生 JavaScript + CSS

## 目录结构

```bash
.
├── app
│   ├── main.py
│   ├── rules.py
│   ├── static
│   │   └── style.css
│   └── templates
│       └── index.html
├── requirements.txt
└── README.md
```

## 本地运行

```bash
pip install -r requirements.txt
python app/main.py
```

浏览器打开：

```text
http://127.0.0.1:5000
```
