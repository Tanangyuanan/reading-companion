#!/usr/bin/env python3
"""Serve a reading workspace frontend with a tiny local HTTP server."""

from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


class WorkspaceHandler(BaseHTTPRequestHandler):
    workspace: Path

    def log_message(self, fmt: str, *args) -> None:
        print(f"[reading-workspace] {self.address_string()} - {fmt % args}", flush=True)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self.serve_state()
            return

        rel = unquote(parsed.path.lstrip("/")) or "frontend/co-reading.html"
        candidate = (self.workspace / rel).resolve()
        try:
            candidate.relative_to(self.workspace)
        except ValueError:
            self.send_error(403, "outside workspace")
            return
        if candidate.is_dir():
            candidate = candidate / "index.html"
        if not candidate.exists() or not candidate.is_file():
            self.send_error(404, "not found")
            return

        data = candidate.read_bytes()
        mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        if mime.startswith("text/") or mime in {"application/javascript", "application/json"}:
            mime = f"{mime}; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_state(self) -> None:
        books = []
        books_root = self.workspace / "books"
        if books_root.exists():
            for book_json in sorted(books_root.glob("*/book.json")):
                try:
                    books.append(json.loads(book_json.read_text(encoding="utf-8")))
                except Exception:
                    books.append({"title": book_json.parent.name, "status": "unreadable"})

        state = {
            "current_state": read_text(self.workspace / "current-state.md"),
            "profile": read_text(self.workspace / "profile.md"),
            "profile_candidates": read_text(self.workspace / "profile-candidates.md"),
            "dashboard_data": read_json(self.workspace / "dashboard-data.json"),
            "books": books,
        }
        data = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", help="Reading workspace directory")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    workspace = Path(args.workspace).expanduser().resolve()
    if not workspace.exists():
        raise SystemExit(f"Workspace does not exist: {workspace}")

    WorkspaceHandler.workspace = workspace
    server = ThreadingHTTPServer(("127.0.0.1", args.port), WorkspaceHandler)
    print(f"Co-reading frontend: http://127.0.0.1:{args.port}/frontend/co-reading.html", flush=True)
    print(f"Dashboard frontend:  http://127.0.0.1:{args.port}/frontend/dashboard.html", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
