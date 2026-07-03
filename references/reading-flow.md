# Reading Flow

## Entry Points

Use these user intents to start the flow:

- "Start reading <book title>"
- "Continue my current book"
- "I want to read"
- "Let's read"
- "Continue reading"
- "Turn this excerpt into a card"
- "Read this chapter with me"
- "Export today's reading notes"
- "Update my reading dashboard"
- "Package this co-reading companion as a reusable/open-source skill"
- "Adapt the reading companion skill to another CLI"

## Intent Router

When the user gives a vague reading request, route by workspace state:

1. No reading workspace exists:
   - Ask for the book title and where the user's books are stored.
   - After the user answers, search the directory, show the best match or matches, and ask for confirmation.
   - After confirmation, initialize the workspace with the confirmed book and source.

2. Reading workspace exists but no active book:
   - Ask what book the user wants to read and where to search for it.

3. Active book exists and the user says "continue", "read", or another vague request:
   - Ask whether to continue the active book at its saved progress or start a new book.
   - Name the active book and progress concretely.

4. Active book exists and the user names a different book:
   - Treat this as a new-book request.
   - Search sources, ask for confirmation, then initialize/switch book.

5. User provides a path or upload:
   - Treat it as the candidate source and ask only for missing book metadata if needed.

Do not make the user manually edit HTML or JSON.

## Frontend Gate

After book resolution and before any reading conversation:

1. Initialize or refresh the reading workspace.
2. Launch the product entrypoint:

```bash
python3 <reading-workspace>/启动共读.py
```

3. Verify `http://127.0.0.1:8768/共读.html` returns `200`.
4. Give the user the reader URL and ask them to confirm it is open.
5. Wait for confirmation before discussing passages, creating cards, or surfacing reading content.

If the user reports a blank page, broken WebSocket, missing book, or port conflict, fix the launcher, config, or runtime files first. Use `scripts/serve_reading_workspace.py` only to smoke-test static frontend assets; it is not the product session path.

## Book Resolution

1. Accept title, path, uploaded file, or current-book request.
2. Search the reading workspace first.
3. Search configured local library paths second.
4. If exactly one source matches, use it.
5. If multiple sources match, ask the user to choose.
6. If no source matches, start user-input-driven mode.

Use `scripts/init_reading_workspace.py` after confirmation:

```bash
python3 <skill>/scripts/init_reading_workspace.py <workspace> \
  --book "<confirmed title>" \
  --book-dir "<confirmed directory>"
```

Or with an exact source:

```bash
python3 <skill>/scripts/init_reading_workspace.py <workspace> \
  --book "<confirmed title>" \
  --source-path "<confirmed source file>"
```

The script writes `book.json`, `current-state.md`, `dashboard-data.json`, and `frontend-config.json`, stages the source file as `books/current.<ext>` for the frontend, and refreshes the product launcher `启动共读.py`.

Modes:

- `source-backed`: local file or full text is available.
- `excerpt-backed`: only user-provided excerpts are available.
- `user-input-driven`: no source text; use only the user's inputs and do not generate chapter-level claims.

## Session Start

At the start of every session:

0. Confirm the co-reading frontend is open, or launch it and wait for confirmation.
1. Load `profile.md`.
2. Load `current-state.md`.
3. Load current book metadata and recent sessions.
4. Load open cards for this book.
5. Load `frontend-config.json` if present.
6. Build a hidden reading strategy:
   - preferred reading mode
   - current book position
   - open questions
   - unresolved cards
   - things to avoid

Do not announce the full strategy unless the user asks.

## During Reading

Good companion behavior:

- react to frontend events as structured reading intents
- respond to the actual excerpt or question
- separate what the book says from what the user says
- invite a concrete reaction when card formation needs the user's contribution
- preserve uncertainty when source context is missing
- adapt immediately when the user corrects the reading mode

Avoid:

- generic chapter summaries
- unsolicited profile-save prompts
- turning every excerpt into a card
- treating a one-off reaction as a stable preference

## Session Close

When the user ends, exports, or pauses reading:

1. Save session summary.
2. Update progress.
3. Update card statuses.
4. Append profile signals.
5. Consolidate eligible profile preferences.
6. Sync dashboard data if configured.
7. Preserve `共读对话.md` and `共读日志.md` as human-readable session traces.

Do this silently unless the user explicitly asks for a summary or export.

## Packaging Or Adaptation Flow

When the user asks to publish, package, or adapt the skill:

1. Inspect only the skill package files needed for release: `SKILL.md`, `references/`, `assets/`, `scripts/`, and `agents/openai.yaml`.
2. Exclude generated workspaces, temporary smoke-test folders, private book files, personal profiles, conversation logs, and absolute user paths.
3. Verify the production launch path remains `启动共读.py` -> `共读搭子.py`; do not document the static server as the main path.
4. Confirm templates initialize an empty reading profile and generic dashboard data.
5. Run skill validation and at least one smoke initialization in a temporary workspace.
