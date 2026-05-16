#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PROTECTED_PREFIXES = ("skills/",)


def run_git(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_protected(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(
        normalized == prefix.rstrip("/") or normalized.startswith(prefix)
        for prefix in PROTECTED_PREFIXES
    )


def unique_paths(paths: list[str]) -> list[str]:
    deduped = []
    seen = set()
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized not in seen and is_protected(normalized):
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


def get_pre_commit_changes() -> list[str]:
    changed: list[str] = []
    changed.extend(run_git(["diff", "--name-only", "--", *PROTECTED_PREFIXES]))
    changed.extend(run_git(["diff", "--cached", "--name-only", "--", *PROTECTED_PREFIXES]))
    changed.extend(
        run_git(
            [
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
                *PROTECTED_PREFIXES,
            ]
        )
    )
    return unique_paths(changed)


def get_range_changes(base: str, head: str) -> list[str]:
    changed = run_git(["diff", "--name-only", f"{base}..{head}", "--", *PROTECTED_PREFIXES])
    return unique_paths(changed)


def print_violation(paths: list[str], source: str) -> int:
    print("检测到受保护目录变更，已拒绝本次操作：", file=sys.stderr)
    print(f"- 检查来源：{source}", file=sys.stderr)
    for path in paths:
        print(f"- {path}", file=sys.stderr)
    print("", file=sys.stderr)
    print("`skills/` 是只读受保护目录。如需修改，请先获得用户明确授权。", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="检查受保护目录是否被改动")
    parser.add_argument(
        "--mode",
        choices=("pre-commit", "range"),
        required=True,
        help="检查模式：提交前检查工作区/暂存区，或检查某个提交区间",
    )
    parser.add_argument("--base", help="range 模式的起始提交")
    parser.add_argument("--head", help="range 模式的结束提交")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "pre-commit":
        changed = get_pre_commit_changes()
        if changed:
            return print_violation(changed, "pre-commit")
        return 0

    if not args.base or not args.head:
        parser.error("--mode range 时必须同时提供 --base 和 --head")

    changed = get_range_changes(args.base, args.head)
    if changed:
        return print_violation(changed, f"range {args.base}..{args.head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
