# CLI Compatibility

This skill must work as a portable workflow, not as a Claude-only feature.

## Architecture

Split implementation into two layers:

1. `reading-companion` core
   - `SKILL.md`
   - `references/`
   - `assets/`
   - `scripts/`
   - user-created `reading-workspace/`

2. Thin CLI adapter
   - tells the host CLI when to load this skill
   - points to the skill folder
   - passes the reading workspace path
   - maps available tools to the workflow
   - preserves the same non-interruption and profile rules
   - configures any model CLI or private memory integration without changing the core skill

The adapter can change per CLI. The reading workspace schema must not.

## Minimum Host Contract

Any CLI can use this skill if it can:

- read files from the skill folder
- read and write a local reading workspace
- run Python 3 scripts or let the agent manually create equivalent files
- search local files by title or path
- preserve enough conversation context to run a session

If a host cannot run scripts, follow the templates manually.

## Adapter Responsibilities

Every adapter must do the following:

1. Load `SKILL.md` on trigger.
2. Load only the needed reference files.
3. Never embed a creator-specific profile.
4. Initialize or locate the user's `reading-workspace/`.
5. Launch `python3 <reading-workspace>/启动共读.py`, verify the HTTP reader, and wait for the user to confirm the UI is open before reading with them.
6. At session start, load:
   - `profile.md`
   - `current-state.md`
   - current book `book.json`
   - recent sessions
   - open cards
7. During the session, use profile as default context but obey current user intent first.
8. Save progress, cards, conversation logs, highlight logs, and profile signals silently.
9. Keep dashboard output as a projection of structured data.

## Codex CLI / Codex App

Recommended locations:

- Project-local: `.agents/skills/reading-companion/`
- User-local: `~/.codex/skills/reading-companion/`

Adapter pattern:

```markdown
When the user asks to start/continue reading a book, use the reading-companion skill at <path>.
Read its SKILL.md first, then read only the referenced files required for the task.
Use <reading-workspace-path> as the user reading workspace.
```

Use `scripts/init_reading_workspace.py` when a workspace does not exist.

## Claude Code / Claude CLI

Recommended locations:

- Project-local: `.agents/skills/reading-companion/`
- User-local or mirrored skill directory if the host supports skill discovery

Adapter pattern:

```markdown
For book reading, load <path>/SKILL.md and follow the reading-companion workflow.
Do not use Claude project memory as the reading profile.
Use the skill-created reading workspace for profile, progress, cards, and dashboard data.
```

If a Claude-specific hook or command exists, it should only invoke the same portable scripts and schemas.

## Gemini CLI

Recommended locations:

- Project-local: `.agents/skills/reading-companion/`
- A configured skills or instructions directory if available

Adapter pattern:

```markdown
When reading-companion is requested, load <path>/SKILL.md.
Use references/cli-compatibility.md to map the workflow to Gemini CLI tools.
Persist user reading state in the reading workspace, not in transient chat memory.
```

## Other Agent CLIs

Use a plain instruction shim:

```markdown
Use the reading-companion skill from <path>.
Before answering, read SKILL.md.
For profile work, read references/profile-schema.md.
For cards, read references/card-schema.md.
For prompts, read references/prompt-library.md.
Write all user state to <reading-workspace-path>.
```

## Compatibility Guardrails

- Do not rely on one vendor's memory system as the only source of truth.
- Do not require hidden runtime context to make the skill useful.
- Do not use host-specific prompt syntax inside core references unless the reference is explicitly an adapter.
- Keep scripts ordinary Python with no private package dependency.
- Keep all generated user data outside the skill folder.
- Keep private harness/context features optional and disabled by default.
- Keep model command examples generic; never ship real API keys or personal absolute paths.

## Open-Source Packaging Checklist

Before publishing or handing this skill to another CLI:

1. Include:
   - `SKILL.md`
   - `references/`
   - `assets/`
   - `scripts/`
   - `agents/openai.yaml`
2. Exclude:
   - `tmp/`
   - generated `reading-workspace/` folders
   - real book files
   - `profile.md`, `profile-signals.jsonl`, `共读对话.md`, `共读日志.md` from real sessions
   - `.harness/` state
   - `.venv/`, `venv/`, `__pycache__/`
3. Verify no private paths or names remain:

```bash
rg -n "Anna|小满|Her|/Users/|Agent工作间|COREAD_MODEL_CLI=.*|API_KEY|SECRET" <skill-folder> --glob '!references/cli-compatibility.md'
```

4. Validate the skill:

```bash
python3 <skill-creator>/scripts/quick_validate.py <skill-folder>
```

5. Smoke-initialize a clean workspace:

```bash
python3 <skill-folder>/scripts/init_reading_workspace.py /tmp/reading-companion-smoke --book "Demo Book" --source-mode user-input-driven
python3 /tmp/reading-companion-smoke/启动共读.py
```

Then verify `http://127.0.0.1:8768/共读.html` loads. Stop the process after verification.

## Smoke Test For Any CLI

1. Ask: "Start reading Demo Book."
2. If no source is found, the agent should enter `user-input-driven` mode and initialize a workspace.
3. The agent should launch the co-reading frontend and wait for the user to confirm it is open.
4. Provide one excerpt and one reaction through the session flow.
5. The agent should create or update:
   - a session note
   - a draft or in-progress card
   - a profile signal, if a preference appeared
6. Ask to continue reading.
7. The agent should load prior state before responding.
