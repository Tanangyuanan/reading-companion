# Privacy And Data Boundary

`reading-companion` is local-first, but local-first does not remove every risk. This
document explains what data is created and where it should live.

## Repository Data

The repository should contain reusable code and templates only:

- `SKILL.md`
- `README.md`
- `docs/`
- `references/`
- `assets/`
- `scripts/`
- `agents/`

It should not contain:

- private book files
- generated reading workspaces
- real `profile.md`
- real `profile-signals.jsonl`
- real `共读对话.md`
- real `共读日志.md`
- `.harness/` state
- API keys or model credentials
- personal absolute paths

## Workspace Data

Generated reading workspaces may contain sensitive data:

- source book files staged under `books/`
- reading progress
- highlights and excerpts
- conversation logs
- reading profile signals
- card drafts

The reading profile is a local personalization memory. It may reveal how a user
reads, what kinds of explanations help them, which topics repeatedly confuse
them, and what card formats they prefer. Keep it with the user's workspace and
do not publish real profile files.

Keep workspaces outside this repository. If you need to share a workspace for a
bug report, create a synthetic one with fake text.

## Model CLI Data

When model replies are enabled, selected excerpts, current messages, optional
recent conversation history, and optional adapter context may be sent to the
configured local model CLI.

Reader-only mode avoids sending text to a model process:

```bash
COREAD_MODEL_ENABLED=0 python3 /path/to/workspace/启动共读.py
```

## Release Check

Before publishing:

```bash
find . -type d \( -name tmp -o -name .harness -o -name .venv -o -name venv -o -name __pycache__ \) -print
rg -n "<personal-name>|<private-assistant-name>|<absolute-home-path>|<credential-var>|<secret-prefix>" . --glob '!references/cli-compatibility.md'
```

Review every hit. The goal is no private names, no local paths, and no real
runtime data.
