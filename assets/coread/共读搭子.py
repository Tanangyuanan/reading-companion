"""
共读搭子 · 实时聊天桥
- 跑一个 WebSocket 服务（浏览器连过来）
- 监听 共读对话.md 的变化（模型桥接会把回复追加到这里）
- 浏览器消息 → 追加到 共读对话.md 的"待回复"区
- 文件被追加 → 推回浏览器

启动：venv/bin/python 共读搭子.py
停止：Ctrl + C
"""

import asyncio
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

try:
    import websockets
except ImportError:
    print(
        "\n缺少共读桥依赖：websockets\n\n"
        "推荐启动方式：\n"
        "  python3 启动共读.py\n\n"
        "启动器会自动创建本地 .venv 并安装依赖；失败时会写入 启动失败说明.md。\n",
        file=sys.stderr,
    )
    raise SystemExit(1)

try:
    from watchdog.observers.polling import PollingObserver as Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    class FileSystemEventHandler:
        pass

# ============ 配置 ============
BASE_DIR = Path(os.environ.get(
    "COREAD_BASE_DIR",
    str(Path.cwd())
))
AGENT_ROOM = Path(os.environ.get("COREAD_AGENT_ROOM", str(BASE_DIR)))
DIALOG_MD = BASE_DIR / "共读对话.md"
LINES_MD = BASE_DIR / "共读日志.md"
INSIGHTS_MD = BASE_DIR / "03_沉淀卡片" / "共读洞察.md"
HTTP_PORT = int(os.environ.get("COREAD_HTTP_PORT", "8768"))
WS_PORT = int(os.environ.get("COREAD_WS_PORT", "8766"))
MODEL_CLI = os.environ.get("COREAD_MODEL_CLI", "")
MODEL_TIMEOUT = int(os.environ.get("COREAD_MODEL_TIMEOUT", "120"))
MODEL_ENABLED = os.environ.get("COREAD_MODEL_ENABLED", "0") == "1"
MODEL_SEND_HISTORY = os.environ.get("COREAD_MODEL_SEND_HISTORY", "0") == "1"
HARNESS_ENABLED = os.environ.get("COREAD_HARNESS_ENABLED", "0") == "1"
HARNESS_LIMIT = int(os.environ.get("COREAD_HARNESS_LIMIT", "18000"))
WORKSPACE_MAP_ENABLED = os.environ.get("COREAD_WORKSPACE_MAP_ENABLED", "0") == "1"
FAILURE_NOTE = BASE_DIR / "启动失败说明.md"

# ============ 文件监听：把模型新回复推给浏览器 ============
last_size = 0
last_tail = ""  # 上一段尾部内容，用于去重
pending_lines = []  # 浏览器推过来的"待回复"，准备追加到 md

# ============ HTTP 服务：打开共读页 + 托管工作间里的可读文件 ============
def write_startup_failure(title, detail):
    FAILURE_NOTE.write_text(
        "\n".join([
            "# 启动失败说明",
            f"- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- 问题：{title}",
            "",
            "## 发生了什么",
            detail.strip(),
            "",
            "## 可以怎么恢复",
            "1. 重新运行 `python3 启动共读.py`。",
            "2. 如果提示端口被占用，先打开 `http://127.0.0.1:8768/共读.html` 看看旧服务是否可用。",
            "3. 如果是权限问题，需要在允许绑定本地端口的终端环境里启动。",
        ]),
        encoding="utf-8",
    )
    print(f"[搭子] 已写入启动失败说明：{FAILURE_NOTE}", flush=True)

def is_allowed_read_path(path):
    try:
        resolved = path.resolve()
    except Exception:
        return False
    for root in (BASE_DIR.resolve(), AGENT_ROOM.resolve()):
        try:
            resolved.relative_to(root)
            return True
        except ValueError:
            continue
    return False

class CoreadHttpHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[共读HTTP] {self.address_string()} - {fmt % args}", flush=True)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/__workspace_file__":
            self.serve_workspace_file(parsed.query)
            return
        super().do_GET()

    def serve_workspace_file(self, query):
        params = parse_qs(query)
        raw_path = (params.get("path") or [""])[0]
        if not raw_path:
            self.send_error(400, "missing path")
            return

        candidate = Path(raw_path).expanduser()
        if not candidate.is_absolute():
            candidate = (AGENT_ROOM / candidate)
        try:
            candidate = candidate.resolve()
        except Exception:
            self.send_error(400, "invalid path")
            return

        if not is_allowed_read_path(candidate):
            self.send_error(403, "path outside allowed workspace")
            return
        if not candidate.is_file():
            self.send_error(404, "file not found")
            return

        mime = mimetypes.guess_type(candidate.name)[0] or "text/plain"
        data = candidate.read_bytes()
        self.send_response(200)
        content_type = mime
        if mime.startswith("text/") or mime in {"application/javascript", "application/json"}:
            content_type = f"{mime}; charset=utf-8"
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

def start_http_server():
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", HTTP_PORT), CoreadHttpHandler)
    except OSError as exc:
        print(f"[共读HTTP] 端口 {HTTP_PORT} 启动失败：{exc}", flush=True)
        return None
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    print(f"[共读HTTP] 页面服务 → http://127.0.0.1:{HTTP_PORT}/共读.html", flush=True)
    return httpd

class DialogWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        global last_size, last_tail
        if event.is_directory or Path(event.src_path) != DIALOG_MD:
            return
        try:
            content = DIALOG_MD.read_text(encoding="utf-8")
        except Exception:
            return
        # 找新增的内容
        if len(content) > last_size:
            new_part = content[last_size:]
            last_size = len(content)
            # 解析共读搭子标记后的内容（这是模型回复）
            if "**共读搭子**" in new_part or "共读搭子：" in new_part:
                if loop and not loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        broadcast({"type": "reply", "text": new_part.strip()}),
                        loop
                    )

observer = None
watcher_stop = threading.Event()

def poll_dialog_changes():
    watcher = DialogWatcher()
    last_mtime = None
    while not watcher_stop.is_set():
        try:
            mtime = DIALOG_MD.stat().st_mtime if DIALOG_MD.exists() else None
        except Exception:
            mtime = None
        if mtime and mtime != last_mtime:
            last_mtime = mtime
            event = type("DialogPollEvent", (), {"is_directory": False, "src_path": str(DIALOG_MD)})()
            watcher.on_modified(event)
        watcher_stop.wait(1.0)

def start_dialog_watcher():
    global observer
    if WATCHDOG_AVAILABLE:
        observer = Observer()
        observer.schedule(DialogWatcher(), str(BASE_DIR), recursive=False)
        observer.start()
        print(f"[搭子] 文件监听已启动 → {DIALOG_MD}")
        return
    thread = threading.Thread(target=poll_dialog_changes, daemon=True)
    thread.start()
    print(f"[搭子] 文件轮询已启动 → {DIALOG_MD}")

def stop_dialog_watcher():
    watcher_stop.set()
    if observer:
        observer.stop()
        observer.join(timeout=2)

# ============ WebSocket 服务 ============
connected = {}
loop = None

def safe_source_slug(source_id, title=""):
    raw = source_id or title or "default"
    raw = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", raw, flags=re.UNICODE).strip("-_")
    return raw[:48] or "default"

def dialog_path_for_source(source):
    source_id = str((source or {}).get("id") or "current-book")
    title = str((source or {}).get("title") or "未命名内容")
    if source_id == "current-book":
        return DIALOG_MD
    return BASE_DIR / f"共读对话_{safe_source_slug(source_id, title)}.md"

def dialog_title_for_source(source):
    return str((source or {}).get("title") or "未命名内容").strip() or "未命名内容"

def ensure_dialog_file(path, source):
    if path.exists():
        return
    title = dialog_title_for_source(source)
    path.write_text(
        f"# 共读对话 · {title}\n\n"
        "> 浏览器里发的消息会到这里。共读搭子会围绕当前阅读内容回复。\n\n"
        "---\n\n",
        encoding="utf-8"
    )

async def broadcast(msg, source_id=None):
    targets = [
        ws for ws, meta in connected.items()
        if source_id is None or meta.get("sourceId") == source_id
    ]
    if targets:
        await asyncio.gather(*[ws.send(json.dumps(msg)) for ws in targets])

async def handler(ws, path=None):
    global last_size
    source = {"id": "current-book", "title": "当前书"}
    dialog_path = dialog_path_for_source(source)
    connected[ws] = {"sourceId": source["id"], "dialogPath": str(dialog_path)}
    print(f"[搭子] ✅ 浏览器已连接（{len(connected)} 人）", flush=True)
    sys.stdout.flush()
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            if msg.get("type") == "source":
                source = msg.get("source") or source
                dialog_path = dialog_path_for_source(source)
                connected[ws] = {"sourceId": source.get("id"), "dialogPath": str(dialog_path)}
                ensure_dialog_file(dialog_path, source)
                content = dialog_path.read_text(encoding="utf-8")
                last_size = len(content)
                await ws.send(json.dumps({
                    "type": "history",
                    "text": content,
                    "sourceId": source.get("id"),
                    "sourceTitle": dialog_title_for_source(source)
                }))
                print(f"[搭子] 已发 {dialog_title_for_source(source)} history（{len(content)} 字）", flush=True)
            elif msg.get("type") == "user":
                text = msg.get("text", "").strip()
                if not text:
                    continue
                append_user_message(text, dialog_path, source)
                await ws.send(json.dumps({"type": "status", "text": "正在调用模型…"}))
                reply = await asyncio.to_thread(append_companion_reply, text, dialog_path, source)
                await ws.send(json.dumps({"type": "reply", "text": reply, "sourceId": source.get("id")}))
                await ws.send(json.dumps({"type": "status", "text": "已连接 · 共读搭子会回复"}))
                print(f"[搭子] 收到用户（{dialog_title_for_source(source)}）: {text[:40]}...", flush=True)
            elif msg.get("type") == "line":
                line = msg.get("line") or {}
                append_line(line)
                await ws.send(json.dumps({"type": "line_saved"}))
                print(f"[搭子] 已记录划线: {str(line.get('text', ''))[:40]}...", flush=True)
            elif msg.get("type") == "line_deleted":
                line = msg.get("line") or {}
                deleted = delete_line(line)
                await ws.send(json.dumps({"type": "line_deleted", "deleted": deleted}))
                print(f"[搭子] 已取消划线: {str(line.get('text', ''))[:40]}...", flush=True)
            elif msg.get("type") == "insight":
                insight = msg.get("insight") or {}
                saved = append_insight(insight)
                await ws.send(json.dumps({"type": "insight_saved", "saved": saved}))
                print(f"[搭子] 已沉淀洞察: {str((insight.get('line') or {}).get('text', ''))[:40]}...", flush=True)
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected.pop(ws, None)
        print(f"[搭子] 浏览器断开（剩 {len(connected)} 人）", flush=True)

def append_user_message(text, dialog_path=None, source=None):
    """把用户说的话追加到当前内容自己的共读对话文件。"""
    dialog_path = dialog_path or DIALOG_MD
    ensure_dialog_file(dialog_path, source or {"id": "current-book", "title": "当前书"})
    ts = time.strftime("%H:%M:%S")
    with dialog_path.open("a", encoding="utf-8") as f:
        f.write(f"\n**用户** · {ts}\n\n{text}\n\n---\n")
    # 同步 last_size
    global last_size
    last_size = len(dialog_path.read_text(encoding="utf-8"))

def append_companion_reply(user_text, dialog_path=None, source=None):
    """调用终端里的大模型生成共读搭子回复，写回当前内容自己的对话文件，并返回新增片段。"""
    dialog_path = dialog_path or DIALOG_MD
    reply = generate_model_reply(user_text, dialog_path, source)
    ts = time.strftime("%H:%M:%S")
    block = f"\n**共读搭子** · {ts}\n\n{reply}\n\n---\n"
    with dialog_path.open("a", encoding="utf-8") as f:
        f.write(block)
    global last_size
    last_size = len(dialog_path.read_text(encoding="utf-8"))
    return block.strip()

def generate_model_reply(user_text, dialog_path=None, source=None):
    if not MODEL_ENABLED:
        return (
            "我收到你的消息了，但现在还没有开启终端大模型桥接。\n\n"
            "需要设置 `COREAD_MODEL_ENABLED=1` 和 `COREAD_MODEL_CLI=<your-cli>` 后重启桥服务，"
            "我才会把右侧聊天发给模型 CLI 生成真实回复。"
        )
    if not MODEL_CLI:
        return "模型桥已开启，但还没有设置 COREAD_MODEL_CLI。请指定可用的 CLI 命令，例如 claude、codex 或 gemini。"

    prompt = build_model_prompt(user_text, dialog_path, source)
    executable = shutil.which(MODEL_CLI) or MODEL_CLI
    command = build_model_command(executable, prompt)
    try:
        result = subprocess.run(
            command,
            cwd=str(AGENT_ROOM),
            text=True,
            capture_output=True,
            timeout=MODEL_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"我调用终端里的大模型超时了（{MODEL_TIMEOUT} 秒）。这不是你没发出去，是 模型 CLI 这次没在限定时间内回完。"
    except Exception as exc:
        return f"我这次没能调起终端里的大模型：{exc}"

    reply = result.stdout.strip()
    if result.returncode == 0 and reply:
        return reply

    err = (result.stderr or "").strip()
    if err:
        return f"我收到你的消息了，但终端里的大模型调用失败：\n\n{err}"
    return "我收到你的消息了，但终端里的大模型没有返回内容。"

def build_model_command(executable, prompt):
    cli_name = Path(executable).name.lower()
    if cli_name == "codex":
        command = [
            executable,
            "exec",
            "-c",
            "mcp_servers={}",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
        ]
        codex_model = os.environ.get("COREAD_CODEX_MODEL", "").strip()
        if codex_model:
            command.extend(["-m", codex_model])
        command.append(prompt)
        return command
    if cli_name == "claude":
        return [executable, "-p", prompt]
    if cli_name == "gemini":
        return [executable, "-p", prompt]
    return [executable, "-p", prompt]

def build_model_prompt(user_text, dialog_path=None, source=None):
    source_title = dialog_title_for_source(source or {"title": "当前书"})
    source_type = str((source or {}).get("type") or "epub")
    latest_line = read_latest_line()
    recent_dialog = read_recent_dialog(dialog_path) if MODEL_SEND_HISTORY else ""
    optional_context = read_harness_context() if HARNESS_ENABLED else ""
    workspace_map = read_workspace_map() if WORKSPACE_MAP_ENABLED else ""
    return f"""你是一个共读搭子。用户正在网页共读工作台里读一份内容，内容可能是 EPUB、HTML、PDF、Markdown、Word/PPT 转换稿或项目文档。

工作区根目录：
{AGENT_ROOM}

可选本地上下文：
{optional_context or "（未启用可选本地上下文）"}

工作区目录地图：
{workspace_map or "（本次未取到工作区目录地图）"}

当前阅读内容：
- 标题：{source_title}
- 类型：{source_type}

你的任务：
- 直接回复用户刚刚在右侧聊天栏里说的话。
- 语气自然、具体，不要像客服或说明书。
- 如果有最新划线，优先围绕划线、来源内容和用户的问题一起回应。
- 不要展开工具链细节，除非用户直接问机制。
- 回复控制在 2 到 4 个短段落，先答准，再追问一个贴着当前内容的具体问题。
- 不要把 AI 总结直接当作定稿卡片；卡片定稿必须包含用户自己的触发点、解释、例子或反对意见。

最新划线：
{latest_line or "（还没有新的划线）"}

最近对话：
{recent_dialog or "（本次未发送历史对话，只发送用户当前消息和最新划线）"}

用户刚刚说：
{user_text}
"""

def read_harness_context():
    harness = Path.home() / ".可选本地上下文/bin/harness"
    if not harness.exists():
        return ""
    try:
        result = subprocess.run(
            [str(harness), "context", "--client", "codex"],
            cwd=str(AGENT_ROOM),
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return f"（local context 读取失败：{exc}）"
    if result.returncode != 0:
        return f"（local context 读取失败：{(result.stderr or '').strip()}）"
    return compact_context(result.stdout, HARNESS_LIMIT)

def compact_context(text, limit):
    if not text:
        return ""
    anchors = [
        "## USER",
        "## MEMORY",
        "## RELATIONS",
        "## CUSTOM",
        "## Project Context",
        "## Current active projects",
        "## 当前活跃项目",
        "## 当前状态提醒",
        "## Project Memory Trace",
        "## Current Task",
        "## Handoff Summary",
    ]
    chunks = []
    for anchor in anchors:
        idx = text.find(anchor)
        if idx == -1:
            continue
        next_candidates = [text.find("\n## ", idx + 4), text.find("\n</pa_workspace_context>", idx)]
        next_candidates = [n for n in next_candidates if n != -1]
        end = min(next_candidates) if next_candidates else min(len(text), idx + 3000)
        chunks.append(text[idx:end].strip())
    compact = "\n\n".join(dict.fromkeys(chunks))
    if not compact:
        compact = text[-limit:]
    if len(compact) > limit:
        compact = compact[-limit:]
    return compact

def read_workspace_map():
    try:
        result = subprocess.run(
            ["find", ".", "-maxdepth", "2", "-type", "d"],
            cwd=str(AGENT_ROOM),
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    lines = []
    for raw in result.stdout.splitlines():
        item = raw.removeprefix("./")
        if not item or item.startswith(".git") or item.startswith("__pycache__"):
            continue
        lines.append(item)
        if len(lines) >= 90:
            break
    return "\n".join(lines)

def read_recent_dialog(dialog_path=None, limit=2400):
    dialog_path = dialog_path or DIALOG_MD
    if not dialog_path.exists():
        return ""
    try:
        content = dialog_path.read_text(encoding="utf-8")
    except Exception:
        return ""
    return content[-limit:].strip()

def generate_fallback_reply(user_text):
    text = user_text.strip()
    latest_line = read_latest_line()
    lower = text.lower()

    if "不理" in text or "回复" in text:
        return "在，刚才那版确实不完整：网页只把你的话写进了对话文件，还没有自动生成回复。\n\n现在我已经接上即时回复了。你在右侧说话，我会直接回到这里；如果你同时划了线，我也会优先拿最新划线跟你聊。"

    if text in {"你好", "hi", "hello", "哈喽", "在吗"} or lower in {"hi", "hello"}:
        if latest_line:
            return f"我在。你刚才最近的一条划线是：「{latest_line}」\n\n我们可以从这句往下聊：你是觉得它说中了你现在的管理处境，还是只是先把它标出来？"
        return "我在。现在右侧这条线已经通了：你在这里说话，我会直接回到这里。\n\n你可以先划一句，或者直接说你读到哪一段卡住了。"

    if "刚才" in text and ("划" in text or "看" in text):
        if latest_line:
            return f"我看到了，最新划线是：「{latest_line}」\n\n我第一反应是，这句值得追的不是字面意思，而是它背后的判断假设。你可以先说说：你划它，是因为它解释了某个现实问题，还是让你想到一个反例？"
        return "我还没读到新的划线。你先在正文里选中一段点“划线”，我会拿那一句跟你聊。"

    if "为什么" in text or "怎么" in text:
        return f"这个问题可以拆开看。你刚说的是：{text}\n\n我先给一个小切口：这本书里的判断通常不只是在解释概念，而是在提示某种因果关系。我们可以先问：这里的关键变量是什么，它会把人的选择推向哪里？"

    if latest_line:
        return f"我听到了。把你的话和最新划线放在一起看：「{latest_line}」\n\n这段可以先别急着总结成道理。你现在更想让我帮你做哪一种：解释原文、联系一个现实场景，还是沉淀成一张知识卡片？"

    return f"我听到了：{text}\n\n现在还没有可引用的最新划线。你可以先划一句原文，我会围绕那一句跟你拆。"

def read_latest_line():
    if not LINES_MD.exists():
        return ""
    try:
        content = LINES_MD.read_text(encoding="utf-8")
    except Exception:
        return ""
    quotes = []
    in_html_log = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## 6/19 之后"):
            in_html_log = True
            continue
        if not in_html_log and not stripped.startswith("<!-- line:"):
            continue
        if stripped.startswith("<!-- line:"):
            in_html_log = True
            continue
        if stripped.startswith("> ") and not stripped.startswith("> 自动维护") and not stripped.startswith("> 共读搭子读取") and not stripped.startswith("> **当前"):
            quote = stripped[2:].strip()
            if quote and quote != "---" and len(quote) < 240 and "划线追加的区域" not in quote:
                quotes.append(quote)
    return quotes[-1] if quotes else ""

def append_line(line):
    """把浏览器里的划线追加到共读日志.md。"""
    text = str(line.get("text") or line.get("full") or "").strip()
    if not text:
        return
    source_title = str(line.get("sourceTitle") or "未命名内容").strip()
    source_type = str(line.get("sourceType") or "content").strip()
    ts = str(line.get("ts") or time.strftime("%Y-%m-%d %H:%M"))
    chapter = str(line.get("chapter") or "未知章节").strip()
    href = str(line.get("href") or "").strip()
    tag = str(line.get("tag") or "划线").strip()
    line_id = str(line.get("id") or "").strip()

    if not LINES_MD.exists():
        LINES_MD.write_text(
            "# 共读日志\n\n"
            "> 来自共读工作台的划线。不同 EPUB / HTML / PDF / Markdown / Office 内容会写在同一个日志里，并保留来源。\n\n",
            encoding="utf-8"
        )

    content = LINES_MD.read_text(encoding="utf-8")
    marker_key = line_id or f"{ts}|{chapter}|{text[:40]}"
    marker = f"<!-- line:{marker_key} -->"
    if marker in content:
        return

    with LINES_MD.open("a", encoding="utf-8") as f:
        f.write(f"\n{marker}\n")
        f.write(f"**{ts}** · {source_title} · {chapter} · {tag}\n\n")
        f.write(f"> {text}\n")
        f.write(f"\n`source: {source_type}`\n")
        if href:
            f.write(f"\n`{href}`\n")
        f.write("\n")

def delete_line(line):
    """从共读日志.md 里删除一条浏览器划线。"""
    if not LINES_MD.exists():
        return False
    try:
        content = LINES_MD.read_text(encoding="utf-8")
    except Exception:
        return False

    text = str(line.get("text") or line.get("full") or "").strip()
    ts = str(line.get("ts") or "").strip()
    chapter = str(line.get("chapter") or "").strip()
    line_id = str(line.get("id") or "").strip()
    marker_keys = []
    if line_id:
        marker_keys.append(line_id)
    if ts and chapter and text:
        marker_keys.append(f"{ts}|{chapter}|{text[:40]}")

    for key in marker_keys:
        marker = f"<!-- line:{key} -->"
        start = content.find(marker)
        if start == -1:
            continue
        next_start = content.find("\n<!-- line:", start + len(marker))
        if next_start == -1:
            new_content = content[:start].rstrip() + "\n"
        else:
            new_content = content[:start].rstrip() + "\n\n" + content[next_start + 1:].lstrip()
        LINES_MD.write_text(new_content, encoding="utf-8")
        return True
    return False

def append_insight(insight):
    """把一次共读中的原句、触发点和共读搭子回应沉淀为洞察。"""
    line = insight.get("line") or {}
    quote = str(line.get("full") or line.get("text") or "").strip()
    if not quote:
        return False

    tag = str(line.get("tag") or "洞察").strip()
    source_title = str(line.get("sourceTitle") or "未命名内容").strip()
    source_type = str(line.get("sourceType") or "content").strip()
    chapter = str(line.get("chapter") or "未知章节").strip()
    prompt = str(insight.get("prompt") or "").strip()
    reply = str(insight.get("reply") or "").strip()
    ts = time.strftime("%Y-%m-%d %H:%M")

    INSIGHTS_MD.parent.mkdir(parents=True, exist_ok=True)
    if not INSIGHTS_MD.exists():
        INSIGHTS_MD.write_text(
            "# 共读洞察\n\n"
            "> 从共读工作台里沉淀出来的 insight：不只是金句，而是原句、用户 的触发点、共读搭子回应和可复用方向。\n\n",
            encoding="utf-8"
        )

    title = quote.replace("\n", " ")
    if len(title) > 42:
        title = title[:42] + "…"

    with INSIGHTS_MD.open("a", encoding="utf-8") as f:
        f.write(f"## {ts} · {tag} · {source_title} · {chapter}\n\n")
        f.write(f"`source: {source_type}`\n\n")
        f.write("### 原句\n\n")
        f.write(f"> {quote}\n\n")
        f.write("### 用户的触发点\n\n")
        f.write(f"{prompt or '（未记录）'}\n\n")
        f.write("### 共读搭子共读回应\n\n")
        f.write(f"{reply or '（未记录）'}\n\n")
        f.write("### 可沉淀方向\n\n")
        f.write("- [ ] 是否整理成概念卡 / 方法卡 / 案例卡\n")
        f.write("- [ ] 是否补充用户自己的例子、反对意见或应用场景\n\n")
        f.write(f"<!-- insight:{line.get('id') or title} -->\n\n")
    return True

def notify_hook():
    """写一个信号文件，触发 hook 让共读搭子注意到"""
    # 我们直接用 .last_msg 标志
    # 模型 CLI 端会读共读对话.md，看到 用户 的消息就回
    # 这里不需要额外动作
    pass

async def main():
    global loop
    loop = asyncio.get_running_loop()
    httpd = start_http_server()
    if httpd is None:
        write_startup_failure(
            "HTTP 页面服务启动失败",
            f"无法绑定 127.0.0.1:{HTTP_PORT}，所以浏览器页面无法访问。这通常是端口被占用或当前运行环境不允许监听本地端口。",
        )
        return 1
    start_dialog_watcher()
    try:
        async with websockets.serve(handler, "127.0.0.1", WS_PORT):
            print(f"[搭子] WebSocket 服务 → ws://localhost:{WS_PORT}")
            print(f"[搭子] 页面服务 → http://127.0.0.1:{HTTP_PORT}/共读.html")
            print(f"[搭子] 等浏览器连过来…Ctrl+C 停止")
            await asyncio.Future()  # 永远跑
    except OSError as exc:
        write_startup_failure(
            "WebSocket 服务启动失败",
            f"无法绑定 127.0.0.1:{WS_PORT}：{exc}。页面可能能打开，但右侧实时聊天无法连接。",
        )
        return 1
    finally:
        if httpd:
            httpd.shutdown()
        stop_dialog_watcher()
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n[搭子] 停止")
        stop_dialog_watcher()
