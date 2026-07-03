# Getting Started

This guide creates a disposable reading workspace and starts the local co-reading
page.

## Requirements

- Python 3.9+
- A local browser
- Optional: one local model CLI on `PATH`, such as `claude`, `codex`, or `gemini`

No npm install, bundler, database, hosted account, or cloud backend is required.

## 1. Create A Workspace

From the repository root:

```bash
python3 scripts/init_reading_workspace.py /tmp/reading-companion-demo --book "Demo Book" --source-mode user-input-driven
```

This creates a workspace at `/tmp/reading-companion-demo`.

The workspace contains generated files such as:

```text
profile.md
profile-candidates.md
profile-signals.jsonl
current-state.md
dashboard-data.json
frontend-config.json
共读.html
共读搭子.py
启动共读.py
共读_files/
```

Those files are user state and runtime files. Do not commit a real workspace
back into this repository.

## 2. Start The Reader

```bash
python3 /tmp/reading-companion-demo/启动共读.py
```

Open:

```text
http://127.0.0.1:8768/共读.html
```

The launcher writes `启动信息.md` in the workspace with the selected HTTP and
WebSocket ports.

## 3. Try Reader-Only Mode

If you want to verify the UI without connecting a model:

```bash
COREAD_MODEL_ENABLED=0 python3 /tmp/reading-companion-demo/启动共读.py
```

You can still open the reader, paste excerpts, highlight, and write logs.

## 4. Try Model Replies

If `claude`, `codex`, or `gemini` is available on `PATH`, the launcher attempts
to use it automatically.

To force a specific command:

```bash
COREAD_MODEL_ENABLED=1 COREAD_MODEL_CLI=codex python3 /tmp/reading-companion-demo/启动共读.py
```

## 5. Use A Local Book File

Pass an explicit source path:

```bash
python3 scripts/init_reading_workspace.py /tmp/reading-companion-book \
  --book "My Book" \
  --source-path /path/to/my-book.epub
```

The initializer stages the source into the workspace as `books/current.<ext>` so
the local frontend can read it.

Only use book files you have the right to read locally. Do not publish generated
workspaces containing copyrighted or private books.
