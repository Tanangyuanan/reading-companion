# Getting Started

This guide shows two paths: use `reading-companion` as an agent skill, or run a
manual smoke test to verify the local co-reading frontend.

## Quick Start Prompt

Paste this into your agent:

```text
Please install and use the reading-companion skill from
https://github.com/Tanangyuanan/reading-companion.

Load it as a skill named reading-companion, create a reading workspace outside
the skill package, ask me for the book title or local file path, run
python3 <reading-workspace>/启动共读.py, then give me the local co-reading URL.
Use the workspace profile files to remember my reading habits across sessions.
```

## Requirements

- Python 3.9+
- A local browser
- Optional: one local model CLI on `PATH`, such as `claude`, `codex`, or `gemini`

No npm install, bundler, database, hosted account, or cloud backend is required.

## 1. Use The Skill

Install this repository folder where your agent runtime loads skills, keeping
the folder name `reading-companion`. After restarting or reloading the agent,
ask it to start or continue a book with `reading-companion`.

The agent should create or locate a reading workspace, resolve the book, run the
workspace launcher, and then hand you the local URL after the page is actually
being served.

## 2. Manual Smoke Test

Create a disposable workspace from the repository root:


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

The three profile files form the local personalization memory. As you read, the
agent can append evidence to `profile-signals.jsonl`, keep uncertain observations
in `profile-candidates.md`, and promote repeated or explicit preferences into
`profile.md`. Future sessions may use that profile to adapt explanations,
questions, and card suggestions to your reading habits.

### Start The Reader

```bash
python3 /tmp/reading-companion-demo/启动共读.py
```

Then open the page served by the launcher:

```text
http://127.0.0.1:8768/共读.html
```

The launcher writes `启动信息.md` in the workspace with the selected HTTP and
WebSocket ports.

### Try Reader-Only Mode

If you want to verify the UI without connecting a model:

```bash
COREAD_MODEL_ENABLED=0 python3 /tmp/reading-companion-demo/启动共读.py
```

You can still open the reader, paste excerpts, highlight, and write logs.

### Try Model Replies

If `claude`, `codex`, or `gemini` is available on `PATH`, the launcher attempts
to use it automatically.

To force a specific command:

```bash
COREAD_MODEL_ENABLED=1 COREAD_MODEL_CLI=codex python3 /tmp/reading-companion-demo/启动共读.py
```

### Use A Local Book File

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
