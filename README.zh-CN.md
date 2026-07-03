# reading-companion

一个本地优先的 AI 共读搭子 skill。

它会把一个本地文件夹变成共读工作区：浏览器阅读页、实时聊天桥、划线日志、阅读画像文件和卡片模板都在本机运行。适合想和 AI 一起读书，但不想把私人书籍、阅读记录、对话历史上传到云端的人。

## 能做什么

- 在本地打开共读页面：`http://127.0.0.1:8768/共读.html`
- 支持本地 EPUB/PDF/HTML/Markdown/文本，也支持没有原文的摘录式共读
- 记录划线、碎念、对话、卡片候选
- 把用户数据写到独立 reading workspace，不写进 skill 包
- 自动探测本机 `PATH` 上的 `claude` / `codex` / `gemini`
- 没有模型 CLI 时，也能作为阅读器和划线工具使用

## 快速开始

创建一个空的共读工作区：

```bash
python3 scripts/init_reading_workspace.py /tmp/reading-companion-demo --book "Demo Book" --source-mode user-input-driven
python3 /tmp/reading-companion-demo/启动共读.py
```

打开：

```text
http://127.0.0.1:8768/共读.html
```

如果本机能找到 `claude`、`codex` 或 `gemini`，启动器会自动接入模型回复；如果找不到，页面仍然可以阅读、划线和保存日志。

指定模型 CLI：

```bash
COREAD_MODEL_ENABLED=1 COREAD_MODEL_CLI=codex python3 /tmp/reading-companion-demo/启动共读.py
```

关闭模型回复，只用阅读器：

```bash
COREAD_MODEL_ENABLED=0 python3 /tmp/reading-companion-demo/启动共读.py
```

## 数据边界

这个仓库不应该包含真实用户数据。真实书籍、profile、共读日志、对话记录都应该在你创建的 reading workspace 里。

发布前请检查：

```bash
find . -type d \( -name tmp -o -name .harness -o -name .venv -o -name venv -o -name __pycache__ \) -print
rg -n "<个人姓名>|<私人助手名>|<本机绝对路径>|<凭证变量>|<密钥前缀>" . --glob '!references/cli-compatibility.md'
```

## 文档

- [快速上手](docs/GETTING_STARTED.md)
- [配置说明](docs/CONFIGURATION.md)
- [隐私和数据边界](docs/PRIVACY.md)
- [开发说明](docs/DEVELOPMENT.md)
- [发布检查清单](RELEASE_CHECKLIST.md)

## 当前状态

这是早期开源包。核心流程已经可以本地启动，但还需要更多不同系统、不同 agent CLI 的真实试用反馈。

## License

当前还没有选择公开 license。正式公开 GitHub 仓库前，需要先补 license。
