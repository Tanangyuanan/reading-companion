# Frontend Architecture

This skill is a reading product, not only a note workflow.

## Required Frontends

Every initialized reading workspace must include:

- `frontend/co-reading.html`: the main co-reading reader.
- `frontend/dashboard.html`: the visual reading dashboard.
- `共读.html`: compatibility copy of the original co-reading frontend.
- `共读搭子.py`: compatibility copy of the original local bridge/server.
- `启动共读.py`: product launcher that prepares local dependencies and starts `共读搭子.py`.
- `共读_files/`: local JS dependencies used by the original co-reading frontend.

The co-reading page is the user's active reading surface. The dashboard is the review and state surface.

## Runtime Boundary

The product runtime is local-first:

- The browser reads local/static frontend assets.
- `共读搭子.py` owns the HTTP server, WebSocket bridge, conversation log, and optional model subprocess.
- `启动共读.py` prepares workspace-local Python dependencies and starts `共读搭子.py`.
- The agent or server adapter writes durable state files in the reading workspace.

Do not assume a cloud backend, database, hosted auth, or vendor memory system. If a model CLI is configured, treat it as a replaceable adapter behind environment variables.

## Co-Reading Frontend

The co-reading page should provide:

- book/source selector
- reading area or excerpt input
- highlight/excerpt capture
- conversation panel
- card candidate panel
- current progress
- link to dashboard

When no reading profile or book-specific plan exists, the co-reading page must not pretend to know why the user is reading. It should expose two low-friction choices:

- ask the user a few lightweight questions before creating a personalized reading plan
- generate a generic plan from the current book/source and update it later from user interactions

Selection/highlight buttons must send structured intent to the companion, not only the button label. For example, "反对" should include the selected sentence plus instructions to steelman the author, identify assumptions, find failure cases, and ask the user what kind of disagreement they mean.

Highlight styles should be visually distinct by tag so the reading surface carries meaning without opening the drawer. Use restrained translucent colors rather than heavy highlighter blocks:

- 案例: warm orange
- 金句: yellow
- 疑问: blue
- 共鸣: pink
- 反对: red
- 行动: green
- 洞察: purple

The page can operate in three source modes:

- `source-backed`: a local book file exists.
- `excerpt-backed`: the user provides excerpts.
- `user-input-driven`: the user talks about the book without source text.

For broad CLI compatibility, the default template works without a build step and stores interaction drafts in browser `localStorage`. Host agents should still persist durable state to the reading workspace files.

## Dashboard Frontend

The dashboard should show:

- current book and source mode
- reading progress
- book list
- card counts by status
- recent cards
- active profile preferences
- pending profile candidates
- next reading actions

The dashboard is a projection. Structured files remain the source of truth.

## Data Contract

Use these workspace files:

```text
reading-workspace/
├── frontend/
│   ├── co-reading.html
│   └── dashboard.html
├── frontend-config.json
├── dashboard-data.json
├── profile.md
├── profile-candidates.md
├── profile-signals.jsonl
├── current-state.md
├── 共读.html
├── 共读搭子.py
├── 启动共读.py
├── 共读对话.md
├── 共读日志.md
├── 共读_files/
└── books/
    └── <book-slug>/
        ├── book.json
        ├── sessions/
        ├── notes/
        └── cards/
```

The frontend may cache local UI state, but durable progress, cards, and profile data must be written to workspace files by the agent or server adapter.

`frontend-config.json` is written by initialization/switching scripts. Users should not edit HTML to change books.

Example:

```json
{
  "book": { "title": "Book Title", "author": "", "startedAt": "2026-06-23" },
  "sources": [
    {
      "id": "current-book",
      "type": "epub",
      "title": "Book Title",
      "path": "./books/current.epub",
      "chapter": "正文",
      "plan": "从当前书源开始共读。"
    }
  ]
}
```

## Launch

The supported product launch path is `启动共读.py`, which prepares a workspace-local `.venv` when needed and then runs the original `共读搭子.py`. The bridge requires `websockets`; `watchdog` is optional because the bridge falls back to a simple polling watcher when it is unavailable. The bridge runs two services in one process:

```bash
python3 <reading-workspace>/启动共读.py
```

It starts:

- **WebSocket server on `:8766`** — the realtime chat bridge. The frontend connects here, browser messages flow over WS, and the script appends them to `<workspace>/共读对话.md` for an external model CLI to answer.
- **HTTP server on `:8768`** — serves the co-reading page and dashboard. Open:
  ```text
  http://127.0.0.1:8768/共读.html        # original co-reading frontend
  http://127.0.0.1:8768/frontend/co-reading.html   # same frontend, alternate path
  http://127.0.0.1:8768/frontend/dashboard.html    # reading dashboard
  ```

`scripts/serve_reading_workspace.py` is **smoke-test only** — it serves static files on an arbitrary port (default `:8787`) with no chat bridge. Do not use it as a substitute for `共读搭子.py` in production.

## Environment Variables

Document model and harness settings as local adapter settings:

| Variable | Default | Meaning |
| --- | --- | --- |
| `COREAD_BASE_DIR` | current working directory | Reading workspace root. |
| `COREAD_HTTP_PORT` | `8768` | HTTP frontend port. |
| `COREAD_WS_PORT` | `8766` | WebSocket bridge port. |
| `COREAD_MODEL_ENABLED` | auto | If unset, the launcher tries to detect a generic local CLI (`claude`, `codex`, `gemini`). Set to `0` to force reader-only mode or `1` to require model replies. |
| `COREAD_MODEL_CLI` | empty | Command used for model replies. When empty and model mode is not disabled, the launcher tries generic CLI names on `PATH`. |
| `COREAD_MODEL_AUTO_DETECT` | optional | Set to `1` to retry generic CLI auto-detection when custom adapter env vars are being composed. |
| `COREAD_MODEL_TIMEOUT` | `120` | Per-reply timeout in seconds. |
| `COREAD_MODEL_SEND_HISTORY` | `0` | Send recent conversation history to the model when set to `1`. |
| `COREAD_HARNESS_ENABLED` | `0` | Enable a private harness/context adapter when available. Keep off in generic releases. |
| `COREAD_AGENT_ROOM` | runtime-specific | Adapter workspace path. Do not hardcode personal absolute paths. |
| `COREAD_WORKSPACE_MAP_ENABLED` | `0` | Include a workspace map in model context when set to `1`. Keep off by default. |

For open-source packaging, include the variable names and behavior, not private values.

## Design Requirements

- Keep the interface functional on first open.
- Do not require bundlers, package install, or cloud services.
- Reuse the bundled original co-reading frontend unless the user explicitly asks for a redesigned UI.
- Do not include creator-specific books, profile entries, or private paths in templates.
- Do not ship generated smoke-test data or conversation logs as default user state.
- Keep frontend text generic enough for any user.
- Make cards visibly distinct by status: draft, in-progress, final.
