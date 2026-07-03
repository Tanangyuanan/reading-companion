# Release Checklist

Use this checklist before sharing or publishing `reading-companion`.

## Must Include

- `SKILL.md`
- `README.md`
- `references/`
- `assets/`
- `scripts/`
- `agents/openai.yaml`

## Must Exclude

- `tmp/`
- `.harness/`
- `.venv/`, `venv/`, `__pycache__/`
- generated `reading-workspace/` folders
- real book files
- real `profile.md`, `profile-signals.jsonl`, `共读对话.md`, `共读日志.md`
- API keys, tokens, private model config, personal absolute paths

## Verification

```bash
find . -type d \( -name tmp -o -name .harness -o -name .venv -o -name venv -o -name __pycache__ \) -print
rg -n "<personal-name>|<private-assistant-name>|<absolute-home-path>|<credential-var>|<secret-prefix>" . --glob '!references/cli-compatibility.md'
python3 scripts/init_reading_workspace.py /tmp/reading-companion-smoke --book "Demo Book" --source-mode user-input-driven
python3 /tmp/reading-companion-smoke/启动共读.py
```

The smoke workspace may create `.venv/`, generated profile files, logs, and
runtime notes under `/tmp/reading-companion-smoke`; those files are runtime
state, not part of the skill package.
