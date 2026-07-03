---
name: reading-companion
description: Interactive book-reading companion product workflow with a local HTML co-reading frontend and dashboard frontend. Use when a user wants to start or continue reading a book, locate a local book file by title or path, open a co-reading reader UI, hold a reading conversation, capture excerpts and reactions, create user-interaction-based knowledge cards, track reading progress, maintain a lightweight reading profile, update a visual reading dashboard, or package/adapt this local co-reading companion as a portable open-source skill without interrupting the user's reading flow.
---

# Reading Companion

## Core Rule

Treat cards and profile as products of interaction, not automatic book summaries.

Read with the user first. Capture evidence silently. Use the active reading profile as default context on later sessions, but let the user's current intent override history.

The primary user experience is the bundled original co-reading frontend (`共读.html` + `共读搭子.py` + `共读_files`) plus a dashboard HTML. Do not redesign the frontend unless the user explicitly asks. Do not reduce this skill to Markdown files and backend memory. The files and scripts exist to support the frontend experience.

Keep the skill core CLI-agnostic. Put platform-specific trigger, memory, and tool-loading behavior in thin adapters for Claude Code, Codex CLI, Gemini CLI, OpenAI desktop/Codex app, or other agent CLIs. The portable contract is the skill folder, references, templates, scripts, and the user's reading workspace.

## Operating Contract

Use three separate layers:

- **Skill package**: reusable instructions, scripts, references, and generic assets. Never write user reading state here.
- **Reading workspace**: one user's local books, profile, progress, cards, dashboard data, and runtime files.
- **CLI adapter**: host-specific trigger text, model command, memory integration, or browser-opening behavior.

When preparing this skill for reuse or open-source release, keep creator-specific books, names, paths, profiles, harness context, and private model settings out of the skill package. Put only generic templates and disabled-by-default configuration examples in the package.

## Workflow

1. Initialize or locate the reading product workspace.
   - Ensure the workspace has `frontend/co-reading.html`, `frontend/dashboard.html`, structured data files, and book/session/card/profile folders.
   - Ensure the workspace also has the original-compatible `共读.html`, `共读搭子.py`, and `共读_files/`.
   - If missing, run `scripts/init_reading_workspace.py`.
   - Confirm generated user data will live outside the skill folder.

2. Resolve the book.
   - If the request is vague and no active book exists, ask for the book title and where the user's books are stored.
   - If the request is vague and an active book exists, ask whether to continue the active book at its saved progress or start a new book.
   - If the user gives a title, search the configured reading workspace and common local library paths before asking for a path.
   - If multiple matches exist, ask the user to choose the source.
   - If no source exists, start in user-input-driven mode and do not claim full-text access.
   - After confirmation, initialize or switch the book by writing `book.json`, `current-state.md`, `dashboard-data.json`, and `frontend-config.json`.

3. Launch the co-reading frontend.
   - **MANDATORY: guide the user to open the co-reading frontend BEFORE holding any reading conversation or surfacing reading content.** Do not start reading, paste excerpts, ask content questions, or build cards in chat alone.
   - Run `python3 <reading-workspace>/启动共读.py` in the background. It prepares a workspace-local `.venv` when dependencies are missing, then launches the original bridge `共读搭子.py`, which starts both the HTTP server (`:8768`) and the WebSocket bridge (`:8766`). The bridge requires `websockets`; file watching uses `watchdog` when present and otherwise falls back to polling. The launcher may auto-detect a generic local model CLI (`claude`, `codex`, or `gemini`) so new users discover that live model replies are supported; it must not contain personal absolute paths, keys, or private model settings.
   - Verify both ports respond: `curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8768/共读.html` should print `200`.
   - Hand the user the URL: `http://127.0.0.1:8768/共读.html`. Tell them what they will see and ask them to confirm the page is open.
   - **Wait for the user to confirm the interface is open before proceeding to step 4.** If the user reports an issue (link broken, page blank, port conflict), fix the script / config first; do not fall back to chat-only reading.
   - `scripts/serve_reading_workspace.py` is smoke-test only — never offer it as the production entry point.

4. Load reading context.
   - Read `profile.md`, `current-state.md`, the current book's `book.json`, recent sessions, open cards, and dashboard data when present.
   - Generate an internal reading strategy from current profile plus the current book state.
   - Current user intent in this conversation outranks old profile preferences.

5. Read with the user.
   - Respond to excerpts, doubts, disagreements, and associations.
   - Prefer structured signals coming from the frontend (highlight text, tag, source id, progress, button intent) over free-floating chat context.
   - Avoid interrupting the user to ask whether to save profile data.
   - Ask content-driven questions only when they deepen the reading or unblock card formation.

6. Create interaction-based cards.
   - A card can be drafted from source text, but it cannot be marked final unless the user has contributed a trigger, interpretation, example, disagreement, or application.
   - Keep draft, in-progress, and final card states distinct.

7. Record progress and signals.
   - Automatically write reading progress, session notes, excerpts, draft cards, and card status.
   - Record possible profile signals to `profile-signals.jsonl` with evidence and confidence. Do this silently.

8. Update profile after the session.
   - Merge only low-risk, evidence-backed reading preferences into `profile.md`.
   - Keep identity, role, life context, and sensitive inferences as candidates unless the user explicitly says to remember them.
   - If the user corrects a profile assumption during the session, adjust the current conversation immediately and write a correction signal for later consolidation.

9. Sync dashboard.
   - Treat dashboard data as a projection of structured book, session, card, and profile state.
   - Do not use dashboard HTML as the only source of truth when structured data exists.

## State Write Contract

Write user state to the reading workspace, not to the skill package:

- Book metadata: `books/<book-slug>/book.json`
- Current session state: `current-state.md`
- Durable profile: `profile.md`
- Candidate profile observations: `profile-candidates.md`
- Evidence stream: `profile-signals.jsonl`
- Dashboard projection: `dashboard-data.json`
- Conversation and highlight logs used by the original frontend: `共读对话.md` and `共读日志.md`
- Cards: `books/<book-slug>/cards/` when available; otherwise the workspace's established card folder

## Context Priority

Use this priority when profile, state, and current messages conflict:

1. User's current message
2. Explicit correction in the current session
3. Current book state
4. Active profile preferences
5. Historical profile candidates
6. General reading heuristics

## Resource Routing

- Read `references/reading-flow.md` before implementing the full workflow or answering design questions about the flow.
- Read `references/profile-schema.md` when creating, updating, or interpreting profile files.
- Read `references/card-schema.md` when creating cards or deciding card status.
- Read `references/frontend-architecture.md` when creating, updating, or launching the co-reading HTML frontend or dashboard frontend.
- Read `references/prompt-library.md` when building prompt templates, agent instructions, or examples.
- Read `references/cli-compatibility.md` when adapting this skill to Claude Code, Codex CLI, Gemini CLI, OpenAI desktop/Codex app, another agent CLI, or an open-source packaging/release context.
- Use `assets/profile-template.md`, `assets/session-template.md`, and `assets/card-template.md` when initializing a workspace.
- Use `assets/frontend/co-reading.html` and `assets/frontend/dashboard.html` as the default frontend templates.
- Use the bundled original `assets/frontend/共读.html`, `assets/coread/共读搭子.py`, `assets/coread/启动共读.py`, and `assets/frontend/共读_files/` for the actual co-reading product experience.
- Run `scripts/init_reading_workspace.py` to create a blank reading workspace with templates, frontends, and no user-specific data.
- Use `scripts/init_reading_workspace.py --book ... --book-dir ...` or `--source-path ...` after user confirmation so the user never has to manually edit HTML.
- Run `scripts/serve_reading_workspace.py <workspace>` only for static smoke tests; it is not the product launch path.

## Non-Negotiables

- Do not include the creator's personal profile or private context in generated templates.
- Do not ship a reading workspace without the co-reading frontend and dashboard frontend.
- Do not infer that a user has a job, family, age, location, or life situation unless the user says it.
- Do not mark a card as final from AI summary alone.
- Do not repeatedly ask the user whether to save profile data.
- Do not let old profile preferences override a user's current stated reading mode.
- Do not begin a reading conversation, paste book content, or build cards in chat before the user has confirmed the co-reading frontend is open. Always guide the user to the UI first and wait for their confirmation.
- Do not replace `共读搭子.py` with `serve_reading_workspace.py` for production. Use `启动共读.py` as the product launcher because it still runs `共读搭子.py`; `serve_reading_workspace.py` is smoke-test only and has no realtime bridge.
- Do not publish a skill package that contains real user reading history, private book files, absolute personal paths, API keys, or enabled private harness/model settings.
