#!/usr/bin/env python3
"""Product-grade launcher for the local co-reading bridge.

This wrapper keeps the original bridge (`共读搭子.py`) as the runtime, while
making first launch friendlier: it creates a workspace-local venv, installs
declared dependencies when needed, writes a readable failure note, and then
hands off to the bridge.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import textwrap
import venv
from datetime import datetime
from pathlib import Path
from typing import Optional


REQUIRED_MODULES = ("websockets",)
HTTP_PORT = 8768
WS_PORT = 8766


def workspace_root() -> Path:
    return Path(__file__).resolve().parent


def python_path_for_venv(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def has_modules(python: Optional[Path] = None) -> bool:
    if python is None or Path(python).resolve() == Path(sys.executable).resolve():
        return all(importlib.util.find_spec(name) is not None for name in REQUIRED_MODULES)

    probe = "import importlib.util, sys; sys.exit(0 if all(importlib.util.find_spec(n) for n in %r) else 1)" % (
        list(REQUIRED_MODULES),
    )
    return subprocess.run([str(python), "-c", probe]).returncode == 0


def port_bind_error(port: int) -> Optional[str]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError as exc:
            return str(exc)
    return None


def find_port_pair(preferred_http: int, preferred_ws: int) -> tuple[int, int, dict[int, str]]:
    checked_errors = {}
    offsets = [0] + list(range(10, 80, 10))
    for offset in offsets:
        http_port = preferred_http + offset
        ws_port = preferred_ws + offset
        http_error = port_bind_error(http_port)
        ws_error = port_bind_error(ws_port)
        if not http_error and not ws_error:
            return http_port, ws_port, checked_errors
        if http_error:
            checked_errors[http_port] = http_error
        if ws_error:
            checked_errors[ws_port] = ws_error
    return 0, 0, checked_errors


def write_launch_info(root: Path, http_port: int, ws_port: int) -> None:
    note = root / "启动信息.md"
    note.write_text(
        "\n".join([
            "# 启动信息",
            f"- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 页面：http://127.0.0.1:{http_port}/共读.html",
            f"- WebSocket：ws://127.0.0.1:{ws_port}",
            "",
            "如果默认 8768/8766 被旧服务占用，启动器会自动选择下一组可用端口。",
        ])
        + "\n",
        encoding="utf-8",
    )


def detect_model_cli() -> Optional[str]:
    for candidate in (
        os.environ.get("COREAD_MODEL_CLI", ""),
        "claude",
        "codex",
        "gemini",
    ):
        if not candidate:
            continue
        resolved = shutil.which(candidate) or candidate
        if Path(resolved).exists() or shutil.which(resolved):
            return resolved
    return None


def write_failure(root: Path, title: str, detail: str, command: Optional[str] = None) -> None:
    note = root / "启动失败说明.md"
    sections = [
        "# 启动失败说明",
        f"- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 问题：{title}",
        "",
        "## 发生了什么",
        detail.strip(),
        "",
        "## 可以怎么恢复",
        "1. 确认当前目录是这个 reading workspace。",
        "2. 重新运行 `python3 启动共读.py`。",
        "3. 如果是网络或包源问题，等网络恢复后重试；依赖会安装到本工作区 `.venv/`，不会污染系统 Python。",
    ]
    if command:
        sections.extend(["", "## 失败命令", f"```bash\n{command}\n```"])
    note.write_text("\n".join(sections) + "\n", encoding="utf-8")
    print(f"\n已写入：{note}")


def ensure_workspace_shape(root: Path) -> bool:
    missing = [name for name in ("共读搭子.py", "requirements.txt", "共读.html") if not (root / name).exists()]
    if not missing:
        return True
    write_failure(
        root,
        "阅读工作区不完整",
        "缺少这些文件：" + "、".join(missing) + "。\n请先用 reading-companion 的初始化脚本重新创建工作区。",
    )
    return False


def ensure_dependencies(root: Path) -> Optional[Path]:
    if has_modules():
        return Path(sys.executable)

    venv_dir = root / ".venv"
    python = python_path_for_venv(venv_dir)
    if not python.exists():
        print("首次启动：正在创建本地 Python 环境 .venv ...")
        try:
            venv.EnvBuilder(with_pip=True).create(venv_dir)
        except Exception as exc:
            write_failure(root, "创建 .venv 失败", repr(exc))
            return None

    if has_modules(python):
        return python

    req = root / "requirements.txt"
    command = f"{python} -m pip install -r {req}"
    print("正在安装共读桥依赖：websockets ...")
    result = subprocess.run(
        [str(python), "-m", "pip", "install", "-r", str(req)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0 or not has_modules(python):
        write_failure(
            root,
            "依赖安装失败",
            textwrap.dedent(
                f"""
                `共读搭子.py` 至少需要 websockets。启动器已经尝试安装到 `{venv_dir}`，
                但 pip 没有成功完成。

                最近的安装输出：

                ```text
                {result.stdout[-4000:]}
                ```
                """
            ),
            command=command,
        )
        return None
    return python


def launch_bridge(root: Path, python: Path) -> int:
    preferred_http = int(os.environ.get("COREAD_HTTP_PORT", str(HTTP_PORT)))
    preferred_ws = int(os.environ.get("COREAD_WS_PORT", str(WS_PORT)))
    http_port, ws_port, port_errors = find_port_pair(preferred_http, preferred_ws)
    if not http_port or not ws_port:
        detail = "\n".join(f"- 127.0.0.1:{port} -> {err}" for port, err in port_errors.items())
        write_failure(
            root,
            "本地端口不可用",
            f"启动器尝试了多组本地端口，但当前环境无法使用：\n\n{detail}\n\n"
            "请关闭占用端口的旧进程，或在允许监听本地端口的终端环境里重试。",
        )
        return 1

    bridge = root / "共读搭子.py"
    write_launch_info(root, http_port, ws_port)
    print("\n正在启动共读工作区 ...", flush=True)
    print(f"页面：http://127.0.0.1:{http_port}/共读.html", flush=True)
    print("服务启动成功后会显示可打开的本地 URL；停止时按 Ctrl+C。\n", flush=True)
    env = os.environ.copy()
    env["COREAD_HTTP_PORT"] = str(http_port)
    env["COREAD_WS_PORT"] = str(ws_port)
    if env.get("COREAD_MODEL_ENABLED") is None:
        detected_cli = detect_model_cli()
        if detected_cli:
            env["COREAD_MODEL_ENABLED"] = "1"
            env["COREAD_MODEL_CLI"] = detected_cli
            env.setdefault("COREAD_MODEL_SEND_HISTORY", "1")
            env.setdefault("COREAD_MODEL_TIMEOUT", "180")
            print(f"模型桥：已自动接入 {detected_cli}", flush=True)
        else:
            env["COREAD_MODEL_ENABLED"] = "0"
            print(
                "模型桥：未发现 claude/codex/gemini。页面仍可阅读；如需模型回复，请设置 COREAD_MODEL_CLI。",
                flush=True,
            )
    if env.get("COREAD_MODEL_ENABLED") == "1" and not env.get("COREAD_MODEL_CLI"):
        print("模型桥：已启用，但未设置 COREAD_MODEL_CLI，页面会提示如何配置。", flush=True)
    if env.get("COREAD_MODEL_AUTO_DETECT") == "1" and env.get("COREAD_MODEL_ENABLED") != "0" and not env.get("COREAD_MODEL_CLI"):
        detected_cli = detect_model_cli()
        if detected_cli:
            env["COREAD_MODEL_ENABLED"] = "1"
            env["COREAD_MODEL_CLI"] = detected_cli
            env.setdefault("COREAD_MODEL_SEND_HISTORY", "1")
            env.setdefault("COREAD_MODEL_TIMEOUT", "180")
            print(f"模型桥：已自动接入 {detected_cli}", flush=True)
    return subprocess.call([str(python), str(bridge)], cwd=str(root), env=env)


def main() -> int:
    root = workspace_root()
    if not ensure_workspace_shape(root):
        return 1
    python = ensure_dependencies(root)
    if python is None:
        return 1
    return launch_bridge(root, python)


if __name__ == "__main__":
    raise SystemExit(main())
