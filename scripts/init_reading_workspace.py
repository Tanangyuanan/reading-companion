#!/usr/bin/env python3
"""Create a blank reading workspace for the reading-companion skill."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import date
from pathlib import Path


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^\w\-\u4e00-\u9fff]+", "", value)
    return value or "untitled-book"


def write_if_missing(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def copy_runtime_file(source: Path, target: Path) -> None:
    """Copy product runtime files so existing workspaces receive launcher fixes."""
    if source.exists():
        shutil.copyfile(source, target)


def infer_source_type(path: Path | None) -> str:
    if not path:
        return "user-input-driven"
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"epub", "pdf", "html", "htm", "md", "markdown", "txt"}:
        return "html" if suffix == "htm" else ("md" if suffix == "markdown" else suffix)
    return suffix or "file"


def normalize_for_match(value: str) -> str:
    return re.sub(r"[\s《》<>（）()\\[\\]【】\"'._-]+", "", value).lower()


def find_source(book_title: str | None, book_dir: str | None) -> Path | None:
    if not book_title or not book_dir:
        return None
    root = Path(book_dir).expanduser()
    if not root.exists():
        return None
    wanted = normalize_for_match(book_title)
    supported = {".epub", ".pdf", ".html", ".htm", ".md", ".markdown", ".txt"}
    matches = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in supported:
            haystack = normalize_for_match(path.stem)
            if wanted and wanted in haystack:
                matches.append(path)
    return sorted(matches, key=lambda p: (p.suffix.lower() != ".epub", len(str(p))))[0].resolve() if matches else None


def build_frontend_config(book_title: str | None, source_path: Path | None, source_mode: str, path_prefix: str = ".") -> dict:
    title = book_title or "未选择书籍"
    source_type = infer_source_type(source_path)
    if source_mode == "user-input-driven":
        source_type = "md"
        source = {
            "id": "current-book",
            "type": "md",
            "title": title,
            "author": "",
            "path": f"{path_prefix}/current-state.md",
            "chapter": "阅读状态",
            "plan": "还没有书源。先通过用户输入、摘抄或本地导入开始共读。"
        }
    else:
        source = {
            "id": "current-book",
            "type": source_type,
            "title": title,
            "author": "",
            "path": f"{path_prefix}/books/current.{infer_source_type(source_path)}" if source_path else f"{path_prefix}/books/current.epub",
            "chapter": "正文",
            "plan": "从当前书源开始共读。"
        }
    return {
        "book": {
            "title": title,
            "author": "",
            "startedAt": date.today().isoformat(),
        },
        "sources": [
            source,
            {
                "id": "reading-status",
                "type": "md",
                "title": "阅读工作区 · 当前状态",
                "path": f"{path_prefix}/current-state.md",
                "chapter": "阅读状态",
                "plan": "用共读工作台查看当前阅读进度。"
            },
        ],
    }


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stage_source_file(workspace: Path, source_path: Path | None) -> Path | None:
    if not source_path or not source_path.exists() or not source_path.is_file():
        return None
    source_type = infer_source_type(source_path)
    staged = workspace / "books" / f"current.{source_type}"
    staged.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != staged.resolve():
        shutil.copyfile(source_path, staged)
    return staged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", help="Target reading workspace directory")
    parser.add_argument("--book", help="Optional first book title")
    parser.add_argument("--source-path", help="Confirmed source file path for the book")
    parser.add_argument("--book-dir", help="Directory to search when source path is not provided")
    parser.add_argument("--source-mode", choices=["source-backed", "excerpt-backed", "user-input-driven"], help="Override source mode")
    args = parser.parse_args()

    root = Path(args.workspace).expanduser().resolve()
    skill_root = Path(__file__).resolve().parents[1]
    assets = skill_root / "assets"

    root.mkdir(parents=True, exist_ok=True)
    for folder in ["books", "exports", "dashboard"]:
        (root / folder).mkdir(exist_ok=True)

    frontend_root = root / "frontend"
    frontend_root.mkdir(exist_ok=True)
    frontend_assets = skill_root / "assets" / "frontend"
    for name in ["co-reading.html", "dashboard.html"]:
        source = frontend_assets / name
        target = frontend_root / name
        if source.exists() and not target.exists():
            shutil.copyfile(source, target)
    for name in ["共读.html"]:
        source = frontend_assets / name
        target = root / name
        if source.exists() and not target.exists():
            shutil.copyfile(source, target)
    for folder in ["共读_files"]:
        source = frontend_assets / folder
        target = root / folder
        if source.exists() and not target.exists():
            shutil.copytree(source, target)
        frontend_target = frontend_root / folder
        if source.exists() and not frontend_target.exists():
            shutil.copytree(source, frontend_target)

    coread_root = skill_root / "assets" / "coread"
    for name in ["共读搭子.py", "启动共读.py"]:
        source = coread_root / name
        target = root / name
        copy_runtime_file(source, target)
    requirements = skill_root / "assets" / "requirements.txt"
    if requirements.exists():
        shutil.copyfile(requirements, root / "requirements.txt")

    write_if_missing(root / "profile.md", (assets / "profile-template.md").read_text(encoding="utf-8"))
    write_if_missing(root / "profile-candidates.md", "# Profile Candidates\n\n")
    write_if_missing(root / "profile-signals.jsonl", "")
    write_if_missing(root / "current-state.md", "# Current Reading State\n\n- current_book:\n- current_position:\n")
    write_if_missing(
        root / "dashboard-data.json",
        json.dumps(
            {
                "books": [],
                "cards": [],
                "profile": {"active_preferences": [], "candidates": []},
                "updated_at": None,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    if args.book:
        source_path = Path(args.source_path).expanduser().resolve() if args.source_path else find_source(args.book, args.book_dir)
        source_mode = args.source_mode or ("source-backed" if source_path else "user-input-driven")
        staged_source = stage_source_file(root, source_path) if source_path and source_mode != "user-input-driven" else None
        slug = slugify(args.book)
        book_root = root / "books" / slug
        for folder in ["sessions", "notes", "cards"]:
            (book_root / folder).mkdir(parents=True, exist_ok=True)
        write_json(
            book_root / "book.json",
            {
                "title": args.book,
                "source_mode": source_mode,
                "source_path": str(source_path) if source_path else None,
                "workspace_source_path": str(staged_source) if staged_source else None,
                "status": "active",
                "current_position": "not_started",
            },
        )
        (root / "current-state.md").write_text(
            "# Current Reading State\n\n"
            f"- current_book: {args.book}\n"
            "- current_position: not_started\n"
            f"- source_mode: {source_mode}\n",
            encoding="utf-8",
        )
        config = build_frontend_config(args.book, staged_source or source_path, source_mode)
        frontend_config = build_frontend_config(args.book, staged_source or source_path, source_mode, path_prefix="..")
        write_json(root / "frontend-config.json", config)
        write_json(root / "frontend" / "frontend-config.json", frontend_config)

        dashboard_path = root / "dashboard-data.json"
        dashboard = json.loads(dashboard_path.read_text(encoding="utf-8")) if dashboard_path.exists() else {}
        dashboard["books"] = [b for b in dashboard.get("books", []) if b.get("title") != args.book]
        dashboard["books"].insert(0, {
            "title": args.book,
            "status": "active",
            "source_mode": source_mode,
            "source_path": str(source_path) if source_path else None,
            "workspace_source_path": str(staged_source) if staged_source else None,
            "current_position": "not_started",
        })
        dashboard["updated_at"] = date.today().isoformat()
        write_json(dashboard_path, dashboard)

    if args.book and args.book_dir and not args.source_path:
        source_path = find_source(args.book, args.book_dir)
        if source_path:
            print(f"Resolved source: {source_path}")
        else:
            print("No matching source found; initialized user-input-driven mode.")

    print(f"Initialized reading workspace: {root}")


if __name__ == "__main__":
    main()
