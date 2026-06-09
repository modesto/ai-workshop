#!/usr/bin/env python3
"""Read-only Git history analysis for hotspots and knowledge silos."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path


RECORD_SEPARATOR = chr(0x1E)
UNIT_SEPARATOR = chr(0x1F)
DEFAULT_MAX_COMMITS = 5000
IGNORED_PREFIXES = (
    "bin/",
    "obj/",
    "packages/",
    "node_modules/",
    "dist/",
    "build/",
    "coverage/",
    "TestResults/",
    "artifacts/",
)
NOISY_SUFFIXES = (
    ".Designer.cs",
    ".Designer.vb",
    ".g.cs",
    ".g.vb",
    ".generated.cs",
    ".generated.vb",
)


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def normalize(path: str) -> str:
    path = path.strip().replace("\\", "/")
    if " => " in path:
        # Handle common rename display: old/name => new/name
        path = path.split(" => ", 1)[1]
        path = path.replace("{", "").replace("}", "")
    return path


def area_for(path: str) -> str:
    parts = [p for p in path.split("/") if p]
    if not parts:
        return "<root>"
    if len(parts) == 1:
        return "<root>"
    return parts[0]


def is_ignored(path: str) -> bool:
    lower = path.lower()
    return any(lower.startswith(prefix.lower()) for prefix in IGNORED_PREFIXES)


def is_noise(path: str) -> bool:
    return path.endswith(NOISY_SUFFIXES) or "/migrations/" in path.lower() or path.lower().endswith(".lock.json")


def parse_log(output: str) -> list[dict]:
    commits = []
    current = None

    for raw_line in output.split("\n"):
        raw_line = raw_line.rstrip("\r")
        if raw_line.startswith(RECORD_SEPARATOR):
            fields = raw_line[1:].split(UNIT_SEPARATOR)
            if len(fields) >= 5:
                current = {
                    "hash": fields[0],
                    "author_name": fields[1],
                    "author_email": fields[2],
                    "date": fields[3],
                    "subject": fields[4],
                    "files": [],
                }
                commits.append(current)
            continue

        if not current or not raw_line.strip():
            continue

        parts = raw_line.split("\t")
        if len(parts) < 3:
            continue

        added_raw, deleted_raw, path_raw = parts[0], parts[1], parts[2]
        path = normalize(path_raw)
        if not path or is_ignored(path):
            continue

        try:
            added = int(added_raw)
        except ValueError:
            added = 0
        try:
            deleted = int(deleted_raw)
        except ValueError:
            deleted = 0

        current["files"].append({"path": path, "added": added, "deleted": deleted})

    return commits


def top_items(counter: Counter, limit: int) -> list[dict]:
    return [{"name": name, "value": value} for name, value in counter.most_common(limit)]


def contributor_share(counter: Counter) -> tuple[str | None, int, float]:
    total = sum(counter.values())
    if not total:
        return None, 0, 0.0
    name, count = counter.most_common(1)[0]
    return name, count, count / total


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Git hotspot and knowledge silo analysis.")
    parser.add_argument("repo", help="Git repository folder")
    parser.add_argument("--since", help="Optional history window, passed to git log --since")
    parser.add_argument("--max-commits", type=int, default=DEFAULT_MAX_COMMITS, help="Maximum commits to inspect")
    parser.add_argument("--top", type=int, default=25, help="Number of top items to return")
    parser.add_argument("--silo-threshold", type=float, default=0.75, help="Primary contributor share threshold")
    parser.add_argument("--min-touches", type=int, default=5, help="Minimum touches before reporting a silo")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.exists() or not repo.is_dir():
        print(f"Not a directory: {repo}", file=sys.stderr)
        return 2

    probe = run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        result = {"root": str(repo), "git_available": False, "error": "Not inside a Git work tree"}
        print(json.dumps(result, indent=2))
        return 0

    log_args = [
        "log",
        f"--max-count={args.max_commits}",
        "--date=short",
        "--numstat",
        "--format=%x1e%H%x1f%an%x1f%ae%x1f%ad%x1f%s",
        "--",
    ]
    if args.since:
        log_args.insert(1, f"--since={args.since}")
    log = run_git(repo, log_args)
    if log.returncode != 0:
        print(log.stderr.strip(), file=sys.stderr)
        return log.returncode

    commits = parse_log(log.stdout)
    file_touches = Counter()
    file_churn = Counter()
    file_authors: dict[str, Counter] = defaultdict(Counter)
    area_touches = Counter()
    area_churn = Counter()
    area_authors: dict[str, Counter] = defaultdict(Counter)
    author_touches = Counter()
    author_areas: dict[str, set[str]] = defaultdict(set)
    noisy_hotspots = []

    for commit in commits:
        author = commit["author_name"] or commit["author_email"] or "<unknown>"
        touched_in_commit = set()
        for change in commit["files"]:
            path = change["path"]
            churn = change["added"] + change["deleted"]
            area = area_for(path)
            touched_in_commit.add(path)
            file_churn[path] += churn
            area_churn[area] += churn
            file_authors[path][author] += 1
            area_authors[area][author] += 1
            area_touches[area] += 1
            author_touches[author] += 1
            author_areas[author].add(area)
        for path in touched_in_commit:
            file_touches[path] += 1

    hotspots = []
    for path, touches in file_touches.most_common(args.top * 3):
        item = {
            "path": path,
            "touches": touches,
            "churn": file_churn[path],
            "area": area_for(path),
            "noise_candidate": is_noise(path),
        }
        if item["noise_candidate"]:
            noisy_hotspots.append(item)
        else:
            hotspots.append(item)
        if len(hotspots) >= args.top:
            break

    file_silos = []
    for path, authors in file_authors.items():
        primary, count, share = contributor_share(authors)
        touches = sum(authors.values())
        if touches >= args.min_touches and share >= args.silo_threshold:
            file_silos.append(
                {
                    "path": path,
                    "primary_author": primary,
                    "primary_touches": count,
                    "total_touches": touches,
                    "share": round(share, 3),
                    "noise_candidate": is_noise(path),
                }
            )
    file_silos.sort(key=lambda x: (x["share"], x["total_touches"]), reverse=True)

    area_silos = []
    for area, authors in area_authors.items():
        primary, count, share = contributor_share(authors)
        touches = sum(authors.values())
        if touches >= args.min_touches and share >= args.silo_threshold:
            area_silos.append(
                {
                    "area": area,
                    "primary_author": primary,
                    "primary_touches": count,
                    "total_touches": touches,
                    "share": round(share, 3),
                }
            )
    area_silos.sort(key=lambda x: (x["share"], x["total_touches"]), reverse=True)

    authors = []
    for author, touches in author_touches.most_common(args.top):
        authors.append(
            {
                "author": author,
                "touches": touches,
                "areas_touched": len(author_areas[author]),
                "areas": sorted(author_areas[author])[:20],
            }
        )

    result = {
        "root": str(repo),
        "git_available": True,
        "limits": {"since": args.since, "max_commits": args.max_commits, "top": args.top},
        "commits_analyzed": len(commits),
        "hotspots": hotspots[: args.top],
        "area_hotspots_by_touches": top_items(area_touches, args.top),
        "area_hotspots_by_churn": top_items(area_churn, args.top),
        "knowledge_silos_by_file": file_silos[: args.top],
        "knowledge_silos_by_area": area_silos[: args.top],
        "top_authors": authors,
        "noisy_hotspots_sample": noisy_hotspots[: args.top],
    }

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + os.linesep, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
