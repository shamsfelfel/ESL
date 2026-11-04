#!/usr/bin/env python3
"""make_catalog.py - write app/catalog.json, the index the offline app reads.

Run it from the repository root after building any lesson:

    python make_catalog.py

It walks lessons/ and tests/, reads each lesson.json, measures the files that
were actually built, and writes one small JSON file. Nothing is invented here:
a part appears in the catalogue only if its file is on disk, so the app never
offers the student a download that does not exist.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "app" / "catalog.json"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):   # pragma: no cover
        pass


def load_build_helpers():
    """Reuse build.py's MP3 frame walker rather than writing a second one."""
    # importing build.py would otherwise drop a __pycache__ into a lesson folder
    sys.dont_write_bytecode = True
    for candidate in sorted(ROOT.glob("lessons/*/build.py")):
        spec = importlib.util.spec_from_file_location("_build", candidate)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    raise SystemExit("No lessons/*/build.py found; run this from the repo root.")


BUILD = load_build_helpers()


def pdf_pages(path: Path) -> int | None:
    hits = len(re.findall(rb"/Type\s*/Page[^s]", path.read_bytes()))
    return hits or None


def describe(folder: Path, name: str, audio: bool) -> dict | None:
    f = folder / name
    if not f.is_file():
        return None
    item = {"file": name, "bytes": f.stat().st_size}
    if audio:
        item["seconds"] = round(BUILD.mp3_duration(f), 1)
    else:
        pages = pdf_pages(f)
        if pages:
            item["pages"] = pages
    return item


def collect(folder: Path, kind: str) -> dict | None:
    meta_file = folder / "lesson.json"
    if not meta_file.is_file():
        return None
    meta = json.loads(meta_file.read_text(encoding="utf-8"))

    parts = []
    for p in meta["parts"]:
        entry = {
            "number": p["number"],
            "slug": p["slug"],
            "title": p["title"],
            "minutes": p["minutes"],
        }
        if p.get("sheet"):
            entry["pdf"] = describe(folder, f"{p['number']}-{p['slug']}.pdf", False)
        if p.get("audio"):
            entry["mp3"] = describe(folder, f"{p['number']}-{p['slug']}.mp3", True)
        # drop keys whose file is missing, so the app never links to nothing
        entry = {k: v for k, v in entry.items() if v is not None}
        parts.append(entry)

    games = []
    for g in meta.get("games", []):
        f = folder / f"{g['number']}-{g['slug']}.html"
        if f.is_file():
            games.append({"number": g["number"], "slug": g["slug"],
                          "title": g["title"], "minutes": g["minutes"],
                          "file": f.name, "bytes": f.stat().st_size})

    built = [f for f in folder.iterdir() if f.is_file()
             and f.suffix.lower() in (".pdf", ".mp3", ".html")]
    return {
        "kind": kind,
        "slug": meta["slug"],
        "path": folder.relative_to(ROOT).as_posix(),
        "number": meta["lesson"],
        "title": meta["title"],
        "level": meta["level"],
        "topic": meta["topic"],
        "time": meta["time"],
        "skills": meta["skills"],
        "new": meta["new_in_this_lesson"],
        "minutes": sum(p["minutes"] for p in meta["parts"]),
        "bytes": sum(f.stat().st_size for f in built),
        "howToWork": meta.get("how_to_work", []),
        "games": games,
        "whole": {k: v for k, v in (
            ("pdf", describe(folder, "00-lesson.pdf", False)),
            ("mp3", describe(folder, "00-full-section.mp3", True)),
        ) if v is not None},
        "parts": parts,
    }


def main() -> int:
    courses = []
    for folder in sorted(ROOT.glob("lessons/*/")):
        entry = collect(folder, "lesson")
        if entry:
            courses.append(entry)
    for folder in sorted(ROOT.glob("tests/*/")):
        entry = collect(folder, "test")
        if entry:
            courses.append(entry)

    if not courses:
        raise SystemExit("No lessons or tests found.")

    catalog = {
        "title": "English, A1+ to B2",
        "subtitle": "A guided course for one student, built to work offline.",
        "generated": date.today().isoformat(),
        "courses": courses,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")

    total = sum(c["bytes"] for c in courses)
    files = sum(len([p for p in c["parts"] if "pdf" in p])
                + len([p for p in c["parts"] if "mp3" in p]) for c in courses)
    games = sum(len(c["games"]) for c in courses)
    print(f"{OUT.relative_to(ROOT).as_posix()}: {len(courses)} entries, "
          f"{files} part files, {games} games, {total / 1048576:.1f} MB of content")
    for c in courses:
        missing = [f"{p['number']}-{p['slug']}" for p in c["parts"]
                   if "pdf" not in p and "mp3" not in p]
        print(f"  {c['slug']:<10} {len(c['parts']):>2} parts  "
              f"{c['bytes'] / 1048576:>5.1f} MB"
              + (f"   NOT BUILT: {', '.join(missing)}" if missing else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
