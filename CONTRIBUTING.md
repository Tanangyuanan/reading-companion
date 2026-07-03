# Contributing

Thanks for helping improve `reading-companion`.

## Good Contributions

- clearer setup docs
- compatibility fixes for different agent CLIs
- frontend usability improvements
- privacy and data-boundary hardening
- card/profile schema improvements
- bug reports with synthetic sample workspaces

## Before Opening A PR

Run:

```bash
PYTHONPYCACHEPREFIX=/tmp/reading-companion-pycache python3 -m py_compile \
  scripts/init_reading_workspace.py \
  scripts/serve_reading_workspace.py \
  assets/coread/启动共读.py \
  assets/coread/共读搭子.py

python3 scripts/init_reading_workspace.py /tmp/reading-companion-smoke --book "Demo Book" --source-mode user-input-driven
```

Run the privacy check:

```bash
find . -type d \( -name tmp -o -name .harness -o -name .venv -o -name venv -o -name __pycache__ \) -print
rg -n "<personal-name>|<private-assistant-name>|<absolute-home-path>|<credential-var>|<secret-prefix>" . --glob '!references/cli-compatibility.md'
```

Do not submit private books, real reading logs, profile files, or absolute local
paths.

## Style

- Prefer plain Python and static HTML over new build systems.
- Keep docs practical and runnable.
- Keep examples synthetic.
- Keep user data out of the repository.
