# Development

This project intentionally stays simple: static HTML, Python scripts, Markdown
schemas, and local files.

## Principles

- Keep user state outside the skill package.
- Keep the browser frontend build-free.
- Keep model integrations replaceable through environment variables.
- Keep private context adapters optional.
- Treat cards as products of interaction, not AI summaries.

## Smoke Test

From the repository root:

```bash
python3 scripts/init_reading_workspace.py /tmp/reading-companion-smoke --book "Demo Book" --source-mode user-input-driven
COREAD_MODEL_ENABLED=0 python3 /tmp/reading-companion-smoke/启动共读.py
```

Then open:

```text
http://127.0.0.1:8768/共读.html
```

## Python Syntax Check

```bash
PYTHONPYCACHEPREFIX=/tmp/reading-companion-pycache python3 -m py_compile \
  scripts/init_reading_workspace.py \
  scripts/serve_reading_workspace.py \
  assets/coread/启动共读.py \
  assets/coread/共读搭子.py
```

## File Boundaries

Commit reusable package files:

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `docs/`
- `references/`
- `assets/`
- `scripts/`
- `agents/`
- `.gitignore`
- `RELEASE_CHECKLIST.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CHANGELOG.md`

Do not commit generated workspaces, real reading logs, real profile files, or
private book files.

## Frontend Notes

The frontend is intentionally plain HTML/CSS/JS so users can open and modify it
without a build system.

Keep UI text generic. Do not include creator names, private project paths, or
assumptions about the reader's identity.

## Model Bridge Notes

`assets/coread/启动共读.py` may detect generic local commands (`claude`, `codex`,
`gemini`) so first-time users can discover live model replies. It must not
hardcode private absolute paths, keys, or account-specific settings.
