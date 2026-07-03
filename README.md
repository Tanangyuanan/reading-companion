# reading-companion

Local-first co-reading companion for agent CLIs.

`reading-companion` turns a local folder into a small co-reading workspace: a
browser reader, a realtime chat bridge, highlight logs, reading profile files,
and card templates. It is designed for people who want to read with an AI
companion without uploading private books or reading history to a hosted app.

![reading-companion co-reading interface](assets/screenshots/co-reading-ui.jpg)

The interface is organized around the reading moment: the left side keeps the
table of contents and reading plan, the center stays focused on the book, and
the right side holds the companion conversation. Highlight a passage and turn it
into a case, quote, question, resonance, disagreement, action, or observation;
those interactions become the raw material for cards and personalization memory.

The companion is meant to get more useful over time. Each workspace contains a
small, local personalization memory: it records evidence-backed reading
preferences, recurring questions, useful card styles, and corrections from real
sessions. On later sessions, the agent can load that profile as default context
so it better understands how you read, while still letting your current request
override past habits.

The project is packaged as an agent skill, but the runtime is ordinary local
files plus Python scripts. It can be adapted to Codex, Claude Code, Gemini CLI,
or another agent CLI through a thin adapter.

## What It Does

- Creates a local reading workspace, then starts a Python co-reading bridge
- Serves the browser page locally after the launcher is running
- Supports local EPUB/PDF/HTML/Markdown/text sources or excerpt-only reading
- Captures highlights, reactions, conversations, and card candidates
- Builds a local reading profile from interaction signals, not from generic summaries
- Keeps reading state in a user-owned workspace, not in the skill package
- Auto-detects a local model CLI on `PATH` (`claude`, `codex`, `gemini`) when available
- Works in reader-only mode when no model CLI is installed

## Personalized Reading Memory

The memory system lives in the reading workspace you create, not in this
repository and not in a hosted account.

- `profile.md` stores active reading preferences the agent may use at session start
- `profile-signals.jsonl` stores evidence from highlights, reactions, card choices, and corrections
- `profile-candidates.md` keeps uncertain observations out of the active profile

This memory is deliberately narrow: it should help the agent understand your
reading habits, preferred explanations, card style, and repeated confusion
points. It should not infer private identity, life context, or sensitive traits
unless you explicitly provide them. The current session always has priority over
old profile entries.

## What It Does Not Include

This repository does **not** include real user reading data, private book files,
conversation logs, profile files, harness state, API keys, or personal absolute
paths. Runtime data belongs in the reading workspace you create.

## Use It As A Skill

Install this folder as an agent skill in the place your agent CLI loads skills
from. Keep the folder name `reading-companion`, then restart or reload the
agent if your runtime requires it.

Then ask your agent to start a reading session, for example:

```text
Use reading-companion to read The Manager's Path with me.
```

or:

```text
Start a co-reading workspace for this local EPUB and help me turn highlights
into cards.
```

The agent should use this skill to:

- choose or create a reading workspace outside the skill package
- resolve the book or start in excerpt-only mode
- run the workspace launcher: `python3 <reading-workspace>/启动共读.py`
- give you the local URL after the launcher is running
- read `profile.md`, `profile-signals.jsonl`, and recent session state before the next session

## Manual Smoke Test

If you want to try the runtime without installing it into an agent first, create
a disposable reading workspace:

```bash
python3 scripts/init_reading_workspace.py /tmp/reading-companion-demo --book "Demo Book" --source-mode user-input-driven
```

Start the local Python launcher:

```bash
python3 /tmp/reading-companion-demo/启动共读.py
```

Then open the local page served by that launcher:

```text
http://127.0.0.1:8768/共读.html
```

The URL works only while `启动共读.py` is running. The launcher starts the local
HTTP page and realtime bridge, writes the selected ports to `启动信息.md`, and
keeps runtime state inside the reading workspace.

If `claude`, `codex`, or `gemini` is available on your `PATH`, the launcher will
auto-enable live model replies. If none is found, the page still works for
reading, highlighting, and saving local logs.

Force a specific model CLI:

```bash
COREAD_MODEL_ENABLED=1 COREAD_MODEL_CLI=codex python3 /tmp/reading-companion-demo/启动共读.py
```

Disable model replies:

```bash
COREAD_MODEL_ENABLED=0 python3 /tmp/reading-companion-demo/启动共读.py
```

## Repository Layout

```text
reading-companion/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── RELEASE_CHECKLIST.md
├── agents/
├── assets/
│   ├── coread/
│   ├── frontend/
│   ├── screenshots/
│   └── *-template.md
├── docs/
├── references/
└── scripts/
```

Important files:

- `SKILL.md` - skill entrypoint and operating contract
- `assets/frontend/` - browser reading pages
- `assets/coread/` - local Python bridge and launcher
- `assets/screenshots/` - README product screenshots
- `scripts/init_reading_workspace.py` - creates a new reading workspace
- `references/` - workflow, schemas, prompts, and compatibility notes
- `docs/` - user-facing setup, config, privacy, and development docs

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Configuration](docs/CONFIGURATION.md)
- [Privacy and Data Boundary](docs/PRIVACY.md)
- [Development](docs/DEVELOPMENT.md)
- [Release Checklist](RELEASE_CHECKLIST.md)
- [中文说明](README.zh-CN.md)

## Local Data Boundary

Generated workspaces may contain book files, reading logs, profile signals, and
conversation history. Keep them outside this repository. The included
`.gitignore` blocks common generated files, but you should still run the release
checks before publishing.

```bash
find . -type d \( -name tmp -o -name .harness -o -name .venv -o -name venv -o -name __pycache__ \) -print
rg -n "<personal-name>|<private-assistant-name>|<absolute-home-path>|<credential-var>|<secret-prefix>" . --glob '!references/cli-compatibility.md'
```

Both commands should return no publish-blocking results.

## Status

Early open-source package. The core workflow runs locally and has been smoke
tested, but the project still needs real-world feedback across different agent
CLIs and operating systems.

## License

No public license has been selected yet. Choose and add a license before a
public GitHub release.
