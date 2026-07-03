# Configuration

`reading-companion` is configured through environment variables. Defaults are
local-first and require no cloud backend.

## Runtime

| Variable | Default | Meaning |
| --- | --- | --- |
| `COREAD_BASE_DIR` | current working directory | Reading workspace root. |
| `COREAD_HTTP_PORT` | `8768` | HTTP frontend port. |
| `COREAD_WS_PORT` | `8766` | WebSocket bridge port. |
| `COREAD_AGENT_ROOM` | workspace root | Optional adapter workspace path included in model context. Do not hardcode personal paths in releases. |

## Model Bridge

| Variable | Default | Meaning |
| --- | --- | --- |
| `COREAD_MODEL_ENABLED` | auto | If unset, the launcher tries to detect `claude`, `codex`, or `gemini` on `PATH`. Set `0` for reader-only mode. Set `1` to enable model replies. |
| `COREAD_MODEL_CLI` | empty | Explicit command for model replies. |
| `COREAD_MODEL_TIMEOUT` | `120` | Per-reply timeout in seconds. |
| `COREAD_MODEL_SEND_HISTORY` | `0` | Send recent conversation history to the model when set to `1`. |
| `COREAD_CODEX_MODEL` | empty | Optional Codex model name passed as `-m`. |

Examples:

```bash
COREAD_MODEL_ENABLED=0 python3 /tmp/reading-companion-demo/启动共读.py
```

```bash
COREAD_MODEL_ENABLED=1 COREAD_MODEL_CLI=codex python3 /tmp/reading-companion-demo/启动共读.py
```

```bash
COREAD_MODEL_ENABLED=1 COREAD_MODEL_CLI=claude COREAD_MODEL_TIMEOUT=180 python3 /tmp/reading-companion-demo/启动共读.py
```

## Optional Context Features

These are adapter features. Keep them off in generic releases unless you know
exactly what local context is being sent to the model.

| Variable | Default | Meaning |
| --- | --- | --- |
| `COREAD_HARNESS_ENABLED` | `0` | Read private local harness context if available. |
| `COREAD_HARNESS_LIMIT` | `18000` | Character limit for optional harness context. |
| `COREAD_WORKSPACE_MAP_ENABLED` | `0` | Include a workspace file map in model context. |

Do not enable private context adapters in shared demos unless the user
understands what will be sent to the model CLI.

## Ports

If `8768/8766` are occupied, the launcher tries nearby port pairs automatically
and writes the final values to `启动信息.md`.
