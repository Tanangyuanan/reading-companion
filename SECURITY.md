# Security Policy

## Supported Versions

This project is currently pre-release. Security fixes should target the current
main branch once a public repository exists.

## Reporting Issues

Before a public GitHub issue tracker exists, report security concerns privately
to the repository maintainer.

Please do not include private books, real user reading logs, API keys, or
screenshots containing sensitive content in public issues.

## Sensitive Data Risks

The highest-risk files are generated runtime files, not the reusable skill code:

- `books/current.*`
- `profile.md`
- `profile-signals.jsonl`
- `current-state.md`
- `dashboard-data.json`
- `frontend-config.json`
- `共读对话*.md`
- `共读日志.md`
- `.harness/`
- `.env`

These are blocked by `.gitignore`, but contributors should still run the release
checks before publishing.

## Model CLI Boundary

When model replies are enabled, selected text and conversation context may be
sent to the configured local model CLI. Use reader-only mode for sensitive
material:

```bash
COREAD_MODEL_ENABLED=0 python3 /path/to/workspace/启动共读.py
```
