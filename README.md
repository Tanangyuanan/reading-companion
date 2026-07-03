# reading-companion

Local-first co-reading companion for agent CLIs.

`reading-companion` turns a local folder into a small co-reading workspace: a
browser reader, a realtime chat bridge, highlight logs, reading profile files,
and card templates. It is designed for people who want to read with an AI
companion without uploading private books or reading history to a hosted app.

The project is packaged as an agent skill, but the runtime is ordinary local
files plus Python scripts. It can be adapted to Codex, Claude Code, Gemini CLI,
or another agent CLI through a thin adapter.

## What It Does

- Opens a local co-reading page at `http://127.0.0.1:8768/共读.html`
- Supports local EPUB/PDF/HTML/Markdown/text sources or excerpt-only reading
- Captures highlights, reactions, conversations, and card candidates
- Keeps reading state in a user-owned workspace, not in the skill package
- Auto-detects a local model CLI on `PATH` (`claude`, `codex`, `gemini`) when available
- Works in reader-only mode when no model CLI is installed

## What It Does Not Include

This repository does **not** include real user reading data, private book files,
conversation logs, profile files, harness state, API keys, or personal absolute
paths. Runtime data belongs in the reading workspace you create.

## Quick Start

Create a blank reading workspace:

```bash
python3 scripts/init_reading_workspace.py /tmp/reading-companion-demo --book "Demo Book" --source-mode user-input-driven
python3 /tmp/reading-companion-demo/启动共读.py
```

Open:

```text
http://127.0.0.1:8768/共读.html
```

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
│   └── *-template.md
├── docs/
├── references/
└── scripts/
```

Important files:

- `SKILL.md` - skill entrypoint and operating contract
- `assets/frontend/` - browser reading pages
- `assets/coread/` - local Python bridge and launcher
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
