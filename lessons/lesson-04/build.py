#!/usr/bin/env python3
"""build.py - build one lesson of the course from lesson.json.

Run it from inside a lesson folder. Everything it needs is in lesson.json
beside it; this script holds no lesson text at all, which is why the same
file sits in every lesson folder without a single edit.

  python build.py --check                 dependencies and connection, build nothing
  python build.py --plan                  print the parts, lengths and sizes it would make
  python build.py --build                 build every PDF, every MP3, and this README
  python build.py --build --only 01 04    build selected parts only
  python build.py --build --pdf-only      sheets only, no network needed
  python build.py --build --audio-only    MP3s only

Install once, for the whole repository:

  pip install -r ../../requirements.txt

Audio comes from edge-tts (free Microsoft neural voices, no account). Every
spoken segment is cached by its text in <repo root>/.audio-cache/, shared by
all lessons, so a dropped connection costs only the segments that had not
finished. Run the same command again to carry on.

Sheets come from the Markdown in lesson.json, rendered with markdown and
weasyprint against the single stylesheet at the repository root. No pandoc.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import socket
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LESSON_FILE = HERE / "lesson.json"

# The lesson titles carry em dashes and arrows, and a Windows console is often
# still cp1252, which cannot encode them. Print UTF-8 and replace what the
# terminal cannot show, rather than stopping the build over an arrow.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):   # pragma: no cover
        pass

# Silence placed between two spoken segments that would otherwise be glued
# together. Two independently encoded MP3 streams joined back to back can
# click, because the second one expects a bit reservoir that is not there.
MIN_GAP = 0.15

# edge-tts returns audio-24khz-48kbitrate-mono-mp3: MPEG-2 Layer III, 24 kHz,
# 48 kbps, mono. One frame = 576 samples = 24 ms = 144 bytes. The header
# FF F3 64 C0 says sync, MPEG-2, Layer III, no CRC, 48 kbps, 24 kHz, mono; the
# other 140 bytes are zero, and zeroed side info means part2_3_length = 0,
# which every decoder renders as silence. No ffmpeg, no pydub.
_SILENT_FRAME = bytes([0xFF, 0xF3, 0x64, 0xC0]) + bytes(140)
_FRAME_MS = 24.0
BYTES_PER_SECOND = 6000.0          # 48 kbps constant bit rate

BASE_WPM = 150.0                   # speech rate used for the estimates


# ---------------------------------------------------------------------------
# Where the repository root is
# ---------------------------------------------------------------------------

def repo_root() -> Path:
    """The folder holding lesson.css and lessons/. Walk up from here."""
    for folder in [HERE, *HERE.parents]:
        if (folder / "lesson.css").is_file() and (folder / "lessons").is_dir():
            return folder
    raise SystemExit(
        "Cannot find the repository root: no parent folder of\n"
        f"  {HERE}\n"
        "holds both lesson.css and lessons/. Run this script from inside a\n"
        "lesson folder of the course repository."
    )


# ---------------------------------------------------------------------------
# Silent MP3 frames and frame-header walking - pure Python
# ---------------------------------------------------------------------------

def silence_mp3(seconds: float) -> bytes:
    frames = max(1, int(round(seconds * 1000.0 / _FRAME_MS)))
    return _SILENT_FRAME * frames


_V2_L3_BITRATES = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
_V1_L3_BITRATES = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
_RATES = {0: {0: 44100, 1: 48000, 2: 32000}, 2: {0: 22050, 1: 24000, 2: 16000}}


def _frame_len(data: bytes, i: int) -> int | None:
    """Byte length of the MPEG audio frame starting at i, or None if not a frame."""
    if i + 4 > len(data) or data[i] != 0xFF or (data[i + 1] & 0xE0) != 0xE0:
        return None
    mpeg1 = ((data[i + 1] >> 3) & 0x03) == 3
    br_idx = (data[i + 2] >> 4) & 0x0F
    sr_idx = (data[i + 2] >> 2) & 0x03
    pad = (data[i + 2] >> 1) & 0x01
    if br_idx in (0, 15) or sr_idx == 3:
        return None
    bitrate = (_V1_L3_BITRATES if mpeg1 else _V2_L3_BITRATES)[br_idx] * 1000
    sr = _RATES[0 if mpeg1 else 2][sr_idx]
    samples = 1152 if mpeg1 else 576
    length = (samples // 8 * bitrate // sr) + pad
    return length if length > 4 else None


def _frame_samples(data: bytes, i: int) -> int:
    return 1152 if ((data[i + 1] >> 3) & 0x03) == 3 else 576


def _frame_rate(data: bytes, i: int) -> int:
    mpeg1 = ((data[i + 1] >> 3) & 0x03) == 3
    return _RATES[0 if mpeg1 else 2][(data[i + 2] >> 2) & 0x03]


def strip_tags(data: bytes) -> bytes:
    """Keep audio frames only: drop ID3 tags and any Xing/Info/VBRI header frame.

    Several of those headers inside one file make players report the wrong
    length, and some phone players then refuse to seek. edge-tts does not write
    them, but a hand-made or re-encoded segment might, so they go on the way in.
    """
    if len(data) > 10 and data[:3] == b"ID3":
        size = 0
        for b in data[6:10]:
            size = (size << 7) | (b & 0x7F)
        data = data[10 + size:]
    if len(data) > 128 and data[-128:-125] == b"TAG":
        data = data[:-128]
    length = _frame_len(data, 0)
    if length and any(tag in data[:min(length, len(data))]
                      for tag in (b"Xing", b"Info", b"VBRI")):
        data = data[length:]
    return data


def mp3_duration(path: Path) -> float:
    data = path.read_bytes()
    i, total, n = 0, 0.0, len(data)
    if data[:3] == b"ID3":
        size = 0
        for b in data[6:10]:
            size = (size << 7) | (b & 0x7F)
        i = 10 + size
    while i + 4 <= n:
        length = _frame_len(data, i)
        if length is None:
            i += 1
            continue
        total += _frame_samples(data, i) / _frame_rate(data, i)
        i += length
    return total


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------

def normalize_segments(segments: list[dict]) -> list[dict]:
    """Never glue two spoken segments directly together.

    A few silent frames absorb the join, and a short breath before the voice
    changes is what the TOEFL narration sounds like anyway.
    """
    out: list[dict] = []
    prev_say = False
    for seg in segments:
        is_say = "say" in seg
        if is_say and prev_say:
            out.append({"pause": MIN_GAP})
        out.append(seg)
        prev_say = is_say
    return out


def estimate(seg: dict, voices: dict) -> float:
    if "pause" in seg:
        return float(seg["pause"])
    cfg = voices[seg.get("voice", "narrator")]
    factor = 1.0 + int(cfg["rate"].rstrip("%")) / 100.0
    return len(seg["say"].split()) / (BASE_WPM * factor) * 60.0


def estimate_part(segments: list[dict], voices: dict) -> float:
    return sum(estimate(s, voices) for s in normalize_segments(segments))


def fmt_time(seconds: float) -> str:
    # round first, or 179.96 s prints as "2m 60.0s"
    tenths = int(round(seconds * 10))
    return f"{tenths // 600}m {tenths % 600 / 10:04.1f}s"


def fmt_size(nbytes: float) -> str:
    return f"{nbytes / 1024:.0f} KB" if nbytes < 1024 * 1024 else f"{nbytes / 1048576:.1f} MB"


# ---------------------------------------------------------------------------
# The lesson file
# ---------------------------------------------------------------------------

def load_lesson() -> dict:
    if not LESSON_FILE.is_file():
        raise SystemExit(f"No lesson.json beside this script ({LESSON_FILE}).")
    try:
        lesson = json.loads(LESSON_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"lesson.json is not valid JSON: {exc}") from exc
    validate(lesson)
    return lesson


def validate(lesson: dict) -> None:
    """Refuse to build from a lesson file that cannot be right."""
    problems: list[str] = []
    for field in ("lesson", "slug", "title", "level", "topic", "time", "skills",
                  "new_in_this_lesson", "footer", "voices", "parts"):
        if field not in lesson:
            problems.append(f"missing top-level field: {field}")
    for name in ("reader", "narrator", "slow"):
        if name not in lesson.get("voices", {}):
            problems.append(f"missing voice: {name}")

    seen: set[str] = set()
    for part in lesson.get("parts", []):
        num, slug = part.get("number"), part.get("slug", "?")
        where = f"part {num} ({slug})"
        if not isinstance(num, str) or not re.fullmatch(r"\d{2}", num) or num == "00":
            problems.append(f"{where}: number must be two digits, 01 upwards")
        if num in seen:
            problems.append(f"{where}: duplicate number")
        seen.add(num)
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
            problems.append(f"{where}: slug must be lower case with hyphens only")
        if not part.get("sheet") and not part.get("audio"):
            problems.append(f"{where}: has neither a sheet nor audio")
        if part.get("sheet") and not part.get("markdown", "").strip():
            problems.append(f"{where}: marked as a sheet but has no markdown")
        if part.get("audio") and not part.get("segments"):
            problems.append(f"{where}: marked as audio but has no segments")
        for seg in part.get("segments", []):
            if ("say" in seg) == ("pause" in seg):
                problems.append(f"{where}: a segment must be either say or pause")
            elif "say" in seg and seg.get("voice", "narrator") not in lesson.get("voices", {}):
                problems.append(f"{where}: unknown voice {seg.get('voice')!r}")
        # printed-only text must never reach the voices
        markers = (part.get("print_only") or {}).get("markers", [])
        spoken = " ".join(s["say"] for s in part.get("segments", []) if "say" in s)
        for marker in markers:
            if marker in spoken:
                problems.append(f"{where}: {marker} is marked print-only but is spoken")
            if part.get("sheet") and marker not in part.get("markdown", ""):
                problems.append(f"{where}: {marker} is marked print-only but is not printed")

    numbers = [p["number"] for p in lesson.get("parts", []) if isinstance(p.get("number"), str)]
    if numbers != sorted(numbers):
        problems.append("parts are not in study order")

    for entry in lesson.get("vocabulary", []):
        word = entry.get("word", "?")
        if not re.fullmatch(r"[A-Z]{3,}", entry.get("answer", "")):
            problems.append(f"vocabulary {word!r}: answer must be 3+ letters, A-Z")
        if not entry.get("meaning", "").strip():
            problems.append(f"vocabulary {word!r}: no meaning to use as a clue")
    for game in lesson.get("games", []):
        where = f"game {game.get('number')} ({game.get('slug', '?')})"
        if game.get("style") not in ("crossword", "word-search"):
            problems.append(f"{where}: unknown style {game.get('style')!r}")
        if not re.fullmatch(r"\d{2}", str(game.get("number", ""))):
            problems.append(f"{where}: number must be two digits")
        if game.get("number") in seen:
            problems.append(f"{where}: number collides with a part")
        if not lesson.get("vocabulary"):
            problems.append(f"{where}: needs a vocabulary block to build from")
    for num in (lesson.get("full_section") or {}).get("parts", []):
        if num not in seen:
            problems.append(f"full_section lists part {num}, which does not exist")

    if problems:
        # the same fault usually fires once per segment; say it once
        seen_problems = list(dict.fromkeys(problems))
        raise SystemExit("lesson.json will not build:\n  - "
                         + "\n  - ".join(seen_problems))


def parts_with_sheet(lesson: dict) -> list[dict]:
    return [p for p in lesson["parts"] if p.get("sheet")]


def parts_with_audio(lesson: dict) -> list[dict]:
    return [p for p in lesson["parts"] if p.get("audio")]


def pdf_name(part: dict) -> str:
    return f"{part['number']}-{part['slug']}.pdf"


def mp3_name(part: dict) -> str:
    return f"{part['number']}-{part['slug']}.mp3"


# ---------------------------------------------------------------------------
# Sheets: Markdown -> HTML -> PDF
# ---------------------------------------------------------------------------

def _markdown_engine():
    import markdown
    return markdown.Markdown(extensions=["tables", "attr_list", "sane_lists"])


def _to_html(engine, text: str) -> str:
    engine.reset()
    html = engine.convert(text)
    # python-markdown leaves "- [ ] item" as a literal "[ ]"; make it a drawn box
    return re.sub(r"<li>\[ \]\s*", '<li class="check">', html)


def meta_block(lesson: dict, part: dict) -> str:
    total = len(lesson["parts"])
    carries = " and ".join(
        bit for bit in ("a sheet" if part.get("sheet") else "",
                        "audio" if part.get("audio") else "") if bit)
    return (
        f'<p><strong>Part {int(part["number"])} of {total}:</strong> {part["title"]}<br>'
        f'<strong>Level:</strong> {lesson["level"]}<br>'
        f'<strong>About</strong> {part["minutes"]} minutes · this part carries {carries}</p>'
    )


def lesson_meta_block(lesson: dict) -> str:
    return (
        f'<p><strong>Level:</strong> {lesson["level"]}<br>'
        f'<strong>Theme:</strong> {lesson["topic"]}<br>'
        f'<strong>Time:</strong> {lesson["time"]}<br>'
        f'<strong>Skills:</strong> {lesson["skills"]}<br>'
        f'<strong>New in this lesson:</strong> {lesson["new_in_this_lesson"]}</p>'
    )


def html_document(title: str, body: str) -> str:
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{title}</title></head><body>{body}</body></html>"
    )


def stylesheets(lesson: dict):
    from weasyprint import CSS
    footer = lesson["footer"].replace('"', "'")
    return [
        CSS(filename=str(repo_root() / "lesson.css")),
        CSS(string='@page { @bottom-center { content: "%s   ·   page " '
                   'counter(page) " of " counter(pages); } }' % footer),
    ]


def render_pdf(title: str, body: str, out: Path, sheets) -> int:
    from weasyprint import HTML
    doc = HTML(string=html_document(title, body), base_url=str(HERE)).render(
        stylesheets=sheets)
    doc.write_pdf(target=str(out))
    return len(doc.pages)


def build_sheets(lesson: dict, wanted: list[dict], whole: bool) -> dict[str, int]:
    """Render one PDF per part, then the whole lesson as one document.

    Returns the page count of each file written, so the README does not have to
    read the page count back out of the PDF.
    """
    engine = _markdown_engine()
    sheets = stylesheets(lesson)
    written: dict[str, int] = {}

    for part in wanted:
        body = (f'<h1>{lesson["title"]}</h1>' + meta_block(lesson, part)
                + "<hr>" + _to_html(engine, part["markdown"]))
        out = HERE / pdf_name(part)
        pages = render_pdf(f'{lesson["title"]} - {part["title"]}', body, out, sheets)
        size = out.stat().st_size
        print(f"  {out.name:<32} {pages:>2} page{'s' if pages != 1 else ' '}  "
              f"{fmt_size(size):>9}"
              f"{'   CHECK: longer than two pages' if pages > 2 else ''}")
        written[out.name] = pages

    if whole:
        body = [f'<h1>{lesson["title"]}</h1>', lesson_meta_block(lesson)]
        # a part may keep itself out of the combined document: a test paper
        # should not carry its own answer key
        for part in [p for p in parts_with_sheet(lesson) if p.get("in_whole", True)]:
            ident = f' id="{part["css_id"]}"' if part.get("css_id") else ""
            body.append(f'<h2{ident}>{part["number"]} &middot; {part["title"]}</h2>')
            body.append(_to_html(engine, part["markdown"]))
        out = HERE / "00-lesson.pdf"
        pages = render_pdf(lesson["title"], "".join(body), out, sheets)
        size = out.stat().st_size
        left_out = [p for p in parts_with_sheet(lesson) if not p.get("in_whole", True)]
        note = ("every sheet, answer key last" if not left_out else
                "every sheet except " + ", ".join(p["slug"] for p in left_out))
        print(f"  {out.name:<32} {pages:>2} pages  {fmt_size(size):>9}   {note}")
        written[out.name] = pages

    return written


# ---------------------------------------------------------------------------
# Audio: edge-tts
# ---------------------------------------------------------------------------

def cache_dir() -> Path:
    return repo_root() / ".audio-cache"


def cache_key(text: str, cfg: dict) -> str:
    raw = "|".join([text, cfg["voice"], cfg["rate"], cfg.get("pitch", "+0Hz")])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


class Offline(RuntimeError):
    """edge-tts could not be reached."""


async def synth_one(text: str, cfg: dict, out: Path, attempts: int = 4) -> None:
    """Synthesize one segment, retrying the dropped connections you get in Gaza."""
    import edge_tts

    last: Exception | None = None
    for n in range(1, attempts + 1):
        try:
            comm = edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"],
                                        pitch=cfg.get("pitch", "+0Hz"))
            tmp = out.with_suffix(".part")
            with tmp.open("wb") as fh:
                async for piece in comm.stream():
                    if piece["type"] == "audio":
                        fh.write(piece["data"])
            if tmp.stat().st_size < 400:
                raise RuntimeError("suspiciously small output")
            tmp.replace(out)
            return
        except Exception as exc:                      # noqa: BLE001
            last = exc
            if out.with_suffix(".part").exists():
                out.with_suffix(".part").unlink()
            if n < attempts:
                wait = 2 ** n
                print(f"      retry {n}/{attempts - 1} in {wait}s ({type(exc).__name__})")
                await asyncio.sleep(wait)
    raise Offline(f"failed after {attempts} attempts: {last}")


async def segments_to_mp3(segments: list[dict], voices: dict, out: Path,
                          force: bool) -> None:
    cache = cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    pieces: list[bytes] = []
    for seg in normalize_segments(segments):
        if "pause" in seg:
            pieces.append(silence_mp3(float(seg["pause"])))
            continue
        cfg = voices[seg.get("voice", "narrator")]
        cached = cache / f"{cache_key(seg['say'], cfg)}.mp3"
        if force or not cached.exists() or cached.stat().st_size < 400:
            preview = " ".join(seg["say"].split())[:52]
            print(f"        synth: {preview}{'...' if len(preview) == 52 else ''}")
            await synth_one(seg["say"], cfg, cached)
        pieces.append(strip_tags(cached.read_bytes()))
    out.write_bytes(b"".join(pieces))


def full_section_segments(lesson: dict) -> list[dict]:
    """The question tracks end to end, like a real exam section."""
    spec = lesson.get("full_section") or {}
    by_number = {p["number"]: p for p in lesson["parts"]}
    out: list[dict] = []
    for i, num in enumerate(spec.get("parts", [])):
        if i:
            out.append({"pause": spec.get("gap", 3)})
        out += list(by_number[num]["segments"])
    return out + list(spec.get("closing", [])) if out else []


async def build_audio(lesson: dict, wanted: list[dict], whole: bool,
                      force: bool) -> list[tuple[str, float, int]]:
    voices = lesson["voices"]
    written: list[tuple[str, float, int]] = []

    jobs: list[tuple[str, list[dict]]] = [(mp3_name(p), p["segments"]) for p in wanted]
    if whole and (lesson.get("full_section") or {}).get("parts"):
        jobs.append(("00-full-section.mp3", full_section_segments(lesson)))

    for name, segments in jobs:
        print(f"  {name}")
        out = HERE / name
        await segments_to_mp3(segments, voices, out, force)
        actual = mp3_duration(out)
        planned = estimate_part(segments, voices)
        flag = ("   CHECK: far from the estimate"
                if planned and abs(actual - planned) / planned > 0.25 else "")
        size = out.stat().st_size
        print(f"        -> {fmt_time(actual):>12}  {fmt_size(size):>9}{flag}")
        written.append((name, actual, size))

    return written


# ---------------------------------------------------------------------------
# Word games
#
# Two styles, built from the lesson's own vocabulary block, so a game can never
# drill a word the lesson does not teach. Each game is one self-contained HTML
# file with its CSS and JavaScript inline and no libraries at all: it opens from
# the app, from the folder, or from a phone with no connection.
# ---------------------------------------------------------------------------

def game_words(lesson: dict) -> list[dict]:
    """Every word a game may use: the key words, then the recalled ones.

    `answer` is what goes in the grid (letters only, one alternative of a
    "keep / kept" pair). `word` is how it is written in the lesson, which is
    what the student is shown.
    """
    out = []
    for v in lesson.get("vocabulary", []):
        out.append({"answer": v["answer"], "word": v["word"],
                    "clue": v["meaning"], "arabic": v.get("arabic", "")})
    for r in lesson.get("recall", []):
        out.append({"answer": r["answer"], "word": r["word"],
                    "clue": r["meaning"], "arabic": ""})
    seen, unique = set(), []
    for w in out:
        # a grid needs letters, and three is the shortest that can cross anything
        if len(w["answer"]) >= 3 and w["answer"] not in seen:
            seen.add(w["answer"])
            unique.append(w)
    return unique


def _crossword_fit(grid, word, r, c, dr, dc):
    """Crossings if the word fits here, else None."""
    if (r - dr, c - dc) in grid or (r + dr * len(word), c + dc * len(word)) in grid:
        return None
    crossings = 0
    for i, ch in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        here = grid.get((rr, cc))
        if here is not None:
            if here != ch:
                return None
            crossings += 1
        else:
            # nothing may touch the sides, or we invent words by accident
            if (rr + dc, cc + dr) in grid or (rr - dc, cc - dr) in grid:
                return None
    return crossings


def _lay_one(order: list[dict]):
    """One greedy pass in the given order. Returns (grid, placed, skipped)."""
    grid: dict[tuple[int, int], str] = {}
    placed, skipped = [], []

    first = order[0]
    for i, ch in enumerate(first["answer"]):
        grid[(0, i)] = ch
    placed.append(dict(first, r=0, c=0, dir="across"))

    for entry in order[1:]:
        word = entry["answer"]
        best = None
        for (gr, gc), gch in list(grid.items()):
            for i, ch in enumerate(word):
                if ch != gch:
                    continue
                for dr, dc in ((0, 1), (1, 0)):
                    r, c = gr - dr * i, gc - dc * i
                    crossings = _crossword_fit(grid, word, r, c, dr, dc)
                    if crossings:
                        score = (crossings, -(abs(r) + abs(c)))
                        if best is None or score > best[0]:
                            best = (score, r, c, dr, dc)
        if best is None:
            skipped.append(entry)
            continue
        _score, r, c, dr, dc = best
        for i, ch in enumerate(word):
            grid[(r + dr * i, c + dc * i)] = ch
        placed.append(dict(entry, r=r, c=c, dir="across" if dc else "down"))
    return grid, placed, skipped


def layout_crossword(words: list[dict]):
    """Try many orderings and keep the best grid.

    One greedy pass leaves a word or two unplaceable, and a vocabulary game
    that silently drops words is worse than useless. So the pass is repeated
    with different orderings, each anchored on a long word, and the attempt
    that places the most words wins; a tie goes to the tighter grid. The
    orderings are seeded, so a rebuild produces the identical puzzle.
    """
    import random
    base = sorted(words, key=lambda w: (-len(w["answer"]), w["answer"]))
    orders = [base]
    rng = random.Random("crossword:" + "".join(w["answer"] for w in base))
    for _ in range(150):
        order = base[:]
        rng.shuffle(order)
        longest = max(range(len(order)), key=lambda i: len(order[i]["answer"]))
        order.insert(0, order.pop(longest))
        orders.append(order)

    best = None
    for order in orders:
        grid, placed, skipped = _lay_one(order)
        rows = [r for r, _ in grid]
        cols = [c for _, c in grid]
        height = max(rows) - min(rows) + 1
        width = max(cols) - min(cols) + 1
        # The long side is what matters: cell size on a phone is the viewport
        # divided by the number of columns, so a 26-wide grid is unusable even
        # if its area is small. Squarer beats smaller.
        score = (len(placed), -max(width, height), -(width * height))
        if best is None or score > best[0]:
            best = (score, grid, placed, skipped)
        if len(placed) == len(words) and max(width, height) <= 17:
            break                      # every word in, and it fits a phone
    _score, grid, placed, skipped = best

    rows = [r for r, _ in grid]
    cols = [c for _, c in grid]
    r0, c0 = min(rows), min(cols)
    height, width = max(rows) - r0 + 1, max(cols) - c0 + 1
    for p in placed:
        p["r"] -= r0
        p["c"] -= c0

    numbers = {}
    for n, pos in enumerate(sorted({(p["r"], p["c"]) for p in placed}), 1):
        numbers[pos] = n
    for p in placed:
        p["num"] = numbers[(p["r"], p["c"])]

    cells = [[None] * width for _ in range(height)]
    for (r, c), ch in grid.items():
        cells[r - r0][c - c0] = ch
    return cells, sorted(placed, key=lambda p: (p["num"], p["dir"])), skipped


def layout_word_search(words: list[dict], seed: str):
    """Eight directions, seeded so a rebuild produces the very same puzzle."""
    import random
    rng = random.Random(seed)
    longest = max(len(w["answer"]) for w in words)
    size = max(13, longest + 2)
    directions = [(0, 1), (1, 0), (1, 1), (-1, 1), (0, -1), (-1, 0), (-1, -1), (1, -1)]

    for _attempt in range(300):
        grid = [[None] * size for _ in range(size)]
        placements, ok = [], True
        for entry in sorted(words, key=lambda w: (-len(w["answer"]), w["answer"])):
            word = entry["answer"]
            spots = [(r, c) for r in range(size) for c in range(size)]
            rng.shuffle(spots)
            dirs = directions[:]
            rng.shuffle(dirs)
            done = False
            for dr, dc in dirs:
                for r, c in spots:
                    er, ec = r + dr * (len(word) - 1), c + dc * (len(word) - 1)
                    if not (0 <= er < size and 0 <= ec < size):
                        continue
                    if all(grid[r + dr * i][c + dc * i] in (None, word[i])
                           for i in range(len(word))):
                        for i, ch in enumerate(word):
                            grid[r + dr * i][c + dc * i] = ch
                        placements.append({"word": word, "display": entry["word"],
                                           "r": r, "c": c, "dr": dr, "dc": dc,
                                           "clue": entry["clue"],
                                           "arabic": entry["arabic"]})
                        done = True
                        break
                if done:
                    break
            if not done:
                ok = False
                break
        if ok:
            pool = "".join(w["answer"] for w in words)   # letters that look native
            for r in range(size):
                for c in range(size):
                    if grid[r][c] is None:
                        grid[r][c] = rng.choice(pool)
            return grid, sorted(placements, key=lambda p: p["display"].lower())
    raise RuntimeError("could not lay out the word search in 300 attempts")


GAME_CSS = """
:root{--ink:#1a1d21;--muted:#5d646e;--rule:#dfe3e8;--accent:#15607a;
--wash:#f1f6f8;--bg:#fff;--ok:#1d6b45;--bad:#a4302a}
@media(prefers-color-scheme:dark){:root{--ink:#e9edf1;--muted:#9aa4b0;
--rule:#2b3138;--accent:#6fc2de;--wash:#1a2026;--bg:#10151a;--ok:#6fd19d;--bad:#e8857f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);padding:16px;
font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:46rem;margin:0 auto}
h1{font-size:20px;margin:0 0 2px;color:var(--accent)}
.sub{color:var(--muted);font-size:14px;margin:0 0 14px}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
button{font:inherit;font-size:14px;padding:7px 14px;border-radius:99px;
border:1px solid var(--accent);background:transparent;color:var(--accent);cursor:pointer;min-height:38px}
button.primary{background:var(--accent);color:#fff}
.msg{min-height:22px;font-size:14px;font-weight:600;margin-bottom:6px}
.msg.good{color:var(--ok)}.msg.bad{color:var(--bad)}
table.grid{border-collapse:collapse;margin:0 auto 6px}
table.grid td{padding:0;border:0}
.cell{width:var(--sq);height:var(--sq);position:relative;border:1px solid var(--rule);
background:var(--wash)}
.cell.block{border:0;background:transparent}
.cell input{width:100%;height:100%;border:0;background:transparent;text-align:center;
font:600 calc(var(--sq)*0.52)/1 inherit;color:var(--ink);text-transform:uppercase;padding:0}
.cell input:focus{outline:2px solid var(--accent);outline-offset:-2px}
.cell.right input{color:var(--ok)}
.cell.wrong input{color:var(--bad)}
.num{position:absolute;top:1px;left:2px;font-size:calc(var(--sq)*0.28);color:var(--muted);
pointer-events:none}
.clues{display:grid;grid-template-columns:1fr;gap:18px;margin-top:18px}
@media(min-width:620px){.clues{grid-template-columns:1fr 1fr}}
.clues h2{font-size:14px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
margin:0 0 6px}
ol.clue{margin:0;padding-left:0;list-style:none}
ol.clue li{margin-bottom:6px;font-size:14.5px;display:flex;gap:7px}
ol.clue b{color:var(--accent);min-width:1.6em;text-align:right}
ol.clue li.done{color:var(--muted);text-decoration:line-through}
.ar{font-size:13px;color:var(--muted)}
.ws td{border:0}
.ws .cell{background:transparent;border:0;display:flex;align-items:center;
justify-content:center;font-weight:600;font-size:calc(var(--sq)*0.5);cursor:pointer;
user-select:none;-webkit-user-select:none;border-radius:4px}
.ws .cell.sel{background:var(--accent);color:#fff}
.ws .cell.found{background:var(--wash);color:var(--ok)}
.words{display:flex;flex-wrap:wrap;gap:6px 14px;margin-top:14px}
.words span{font-size:14.5px}
.words span.found{color:var(--muted);text-decoration:line-through}
.foot{margin-top:26px;border-top:1px solid var(--rule);padding-top:10px;
font-size:13px;color:var(--muted)}
.foot a{color:var(--accent)}
"""


def _game_page(title: str, lesson: dict, subtitle: str, body: str, script: str,
               square: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} - {lesson["title"]}</title>
<meta name="theme-color" content="#15607a">
<style>{GAME_CSS}
:root{{--sq:{square}}}</style>
</head>
<body><div class="wrap">
<h1>{title}</h1>
<p class="sub">{lesson["title"]} &middot; {subtitle}</p>
{body}
<p class="foot">Every word here is from this lesson. &nbsp;
<a href="README.md">Back to the lesson</a></p>
</div>
<script>{script}</script>
</body>
</html>
"""


def build_crossword(lesson: dict, out: Path) -> dict:
    cells, placed, skipped = layout_crossword(game_words(lesson))
    height, width = len(cells), len(cells[0])

    rows = []
    for r in range(height):
        tds = []
        for c in range(width):
            ch = cells[r][c]
            if ch is None:
                tds.append('<td><div class="cell block"></div></td>')
                continue
            num = next((p["num"] for p in placed
                        if p["r"] == r and p["c"] == c), None)
            label = f'<span class="num">{num}</span>' if num else ""
            tds.append(
                f'<td><div class="cell" data-r="{r}" data-c="{c}">{label}'
                f'<input maxlength="1" inputmode="latin" autocomplete="off" '
                f'aria-label="row {r + 1} column {c + 1}"></div></td>')
        rows.append("<tr>" + "".join(tds) + "</tr>")

    def clue_list(direction):
        items = []
        for p in placed:
            if p["dir"] != direction:
                continue
            arabic = f' <span class="ar">{p["arabic"]}</span>' if p["arabic"] else ""
            # "wake up" and "memory card" go in as one run of letters
            joined = (" <i>(two words, written as one)</i>"
                      if " " in p["word"].split("/")[0].strip() else "")
            items.append(f'<li data-num="{p["num"]}" data-dir="{direction}">'
                         f'<b>{p["num"]}</b><span>{p["clue"]}{joined}{arabic}'
                         f' <span class="ar">({len(p["answer"])})</span></span></li>')
        return "\n".join(items)

    body = f"""<div class="msg" id="msg"></div>
<table class="grid"><tbody>
{chr(10).join(rows)}
</tbody></table>
<div class="bar">
  <button class="primary" id="check">Check</button>
  <button id="reveal">Show a letter</button>
  <button id="clear">Clear</button>
</div>
<div class="clues">
  <div><h2>Across</h2><ol class="clue" id="across">{clue_list("across")}</ol></div>
  <div><h2>Down</h2><ol class="clue" id="down">{clue_list("down")}</ol></div>
</div>"""

    solution = {f"{r},{c}": cells[r][c]
                for r in range(height) for c in range(width) if cells[r][c]}

    script = """
const SOL = __SOL__, ENTRIES = __ENT__;
const cells = {};
document.querySelectorAll('.cell[data-r]').forEach(d => {
  cells[d.dataset.r + ',' + d.dataset.c] = d;
  const i = d.querySelector('input');
  i.addEventListener('input', () => {
    i.value = i.value.toUpperCase().replace(/[^A-Z]/g, '');
    d.classList.remove('right', 'wrong');
    if (i.value) move(+d.dataset.r, +d.dataset.c, 1);
    save();
  });
  i.addEventListener('keydown', e => {
    const r = +d.dataset.r, c = +d.dataset.c;
    if (e.key === 'Backspace' && !i.value) { move(r, c, -1); }
    else if (e.key === 'ArrowRight') { focus(r, c + 1); e.preventDefault(); }
    else if (e.key === 'ArrowLeft')  { focus(r, c - 1); e.preventDefault(); }
    else if (e.key === 'ArrowDown')  { focus(r + 1, c); e.preventDefault(); }
    else if (e.key === 'ArrowUp')    { focus(r - 1, c); e.preventDefault(); }
  });
});
let dir = 'across';
function focus(r, c) { const d = cells[r + ',' + c]; if (d) d.querySelector('input').focus(); }
function move(r, c, step) {
  if (dir === 'across') focus(r, c + step); else focus(r + step, c);
}
document.querySelectorAll('#across li, #down li').forEach(li => {
  li.addEventListener('click', () => {
    dir = li.dataset.dir;
    const e = ENTRIES.find(x => x.num == li.dataset.num && x.dir === dir);
    if (e) focus(e.r, e.c);
  });
});
function save() {
  const v = {};
  for (const k in cells) { const t = cells[k].querySelector('input').value; if (t) v[k] = t; }
  try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) {}
}
const KEY = 'crossword:' + location.pathname;
try {
  const v = JSON.parse(localStorage.getItem(KEY) || '{}');
  for (const k in v) if (cells[k]) cells[k].querySelector('input').value = v[k];
} catch (e) {}
const msg = document.getElementById('msg');
document.getElementById('check').onclick = () => {
  let right = 0, wrong = 0, empty = 0;
  for (const k in cells) {
    const d = cells[k], i = d.querySelector('input');
    d.classList.remove('right', 'wrong');
    if (!i.value) { empty++; continue; }
    if (i.value === SOL[k]) { d.classList.add('right'); right++; }
    else { d.classList.add('wrong'); wrong++; }
  }
  markDone();
  msg.className = 'msg ' + (wrong ? 'bad' : (empty ? '' : 'good'));
  msg.textContent = wrong ? wrong + ' letter' + (wrong > 1 ? 's are' : ' is') + ' wrong.'
    : (empty ? right + ' right, ' + empty + ' still empty.' : 'All correct. Well done.');
};
document.getElementById('reveal').onclick = () => {
  const empty = Object.keys(cells).filter(k => !cells[k].querySelector('input').value);
  if (!empty.length) { msg.textContent = 'Nothing left to show.'; return; }
  const k = empty[Math.floor(Math.random() * empty.length)];
  cells[k].querySelector('input').value = SOL[k];
  save(); markDone();
  msg.className = 'msg'; msg.textContent = 'One letter filled in for you.';
};
document.getElementById('clear').onclick = () => {
  for (const k in cells) {
    cells[k].querySelector('input').value = '';
    cells[k].classList.remove('right', 'wrong');
  }
  document.querySelectorAll('li.done').forEach(li => li.classList.remove('done'));
  save(); msg.textContent = '';
};
function markDone() {
  ENTRIES.forEach(e => {
    let got = '';
    for (let i = 0; i < e.word.length; i++) {
      const k = e.dir === 'across' ? e.r + ',' + (e.c + i) : (e.r + i) + ',' + e.c;
      got += (cells[k] ? cells[k].querySelector('input').value : '') || ' ';
    }
    const li = document.querySelector('li[data-num="' + e.num + '"][data-dir="' + e.dir + '"]');
    if (li) li.classList.toggle('done', got === e.word);
  });
}
markDone();
"""
    entries = [{"word": p["answer"], "r": p["r"], "c": p["c"],
                "dir": p["dir"], "num": p["num"]} for p in placed]
    script = (script.replace("__SOL__", json.dumps(solution))
                    .replace("__ENT__", json.dumps(entries)))

    square = "min(8.6vw, 34px)" if width <= 11 else f"min({88 / width:.1f}vw, 32px)"
    out.write_text(_game_page(
        "Crossword", lesson,
        f"{len(placed)} words from this lesson. Read the meaning, write the word.",
        body, script, square), encoding="utf-8")
    return {"words": len(placed), "skipped": [s["word"] for s in skipped],
            "size": f"{width}x{height}"}


def build_word_search(lesson: dict, out: Path) -> dict:
    words = game_words(lesson)
    grid, placed = layout_word_search(words, lesson["slug"])
    size = len(grid)

    rows = []
    for r in range(size):
        tds = "".join(
            f'<td><div class="cell" data-r="{r}" data-c="{c}">{grid[r][c]}</div></td>'
            for c in range(size))
        rows.append(f"<tr>{tds}</tr>")

    listing = "\n".join(
        f'<span data-word="{p["word"]}">{p["display"]}'
        + (f' <span class="ar">{p["arabic"]}</span>' if p["arabic"] else "")
        + "</span>" for p in placed)

    body = f"""<div class="msg" id="msg"></div>
<table class="grid ws"><tbody>
{chr(10).join(rows)}
</tbody></table>
<div class="bar">
  <button id="reveal">Show one word</button>
  <button id="clear">Start again</button>
</div>
<div class="words" id="words">{listing}</div>
<p class="sub" style="margin-top:14px">Tap the first letter, then the last letter.
Words go in any direction, including backwards.</p>"""

    script = """
const WORDS = __WORDS__;
const size = __SIZE__;
const cellOf = {};
document.querySelectorAll('.ws .cell').forEach(d => cellOf[d.dataset.r + ',' + d.dataset.c] = d);
const KEY = 'wordsearch:' + location.pathname;
let found = [];
try { found = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) {}
let start = null;
const msg = document.getElementById('msg');

function paint() {
  WORDS.forEach(w => {
    if (!found.includes(w.word)) return;
    for (let i = 0; i < w.word.length; i++) {
      const d = cellOf[(w.r + w.dr * i) + ',' + (w.c + w.dc * i)];
      if (d) d.classList.add('found');
    }
    const s = document.querySelector('[data-word="' + w.word + '"]');
    if (s) s.classList.add('found');
  });
  const left = WORDS.length - found.length;
  if (!left) { msg.className = 'msg good'; msg.textContent = 'All found. Well done.'; }
}
function clearSel() {
  document.querySelectorAll('.ws .cell.sel').forEach(d => d.classList.remove('sel'));
}
document.querySelectorAll('.ws .cell').forEach(d => {
  d.addEventListener('click', () => {
    const r = +d.dataset.r, c = +d.dataset.c;
    if (!start) { clearSel(); start = [r, c]; d.classList.add('sel'); return; }
    const [sr, sc] = start;
    const dr = Math.sign(r - sr), dc = Math.sign(c - sc);
    const len = Math.max(Math.abs(r - sr), Math.abs(c - sc)) + 1;
    const straight = (r === sr || c === sc || Math.abs(r - sr) === Math.abs(c - sc));
    start = null; clearSel();
    if (!straight) { msg.className = 'msg bad'; msg.textContent = 'Lines only: across, down or corner to corner.'; return; }
    let got = '';
    for (let i = 0; i < len; i++) {
      const cell = cellOf[(sr + dr * i) + ',' + (sc + dc * i)];
      got += cell ? cell.textContent.trim() : '';
    }
    const hit = WORDS.find(w => w.word === got || w.word === got.split('').reverse().join(''));
    if (hit && !found.includes(hit.word)) {
      found.push(hit.word);
      try { localStorage.setItem(KEY, JSON.stringify(found)); } catch (e) {}
      msg.className = 'msg good';
      msg.textContent = hit.display + ' - ' + hit.clue;
      paint();
    } else if (hit) {
      msg.className = 'msg'; msg.textContent = 'Already found.';
    } else {
      msg.className = 'msg bad'; msg.textContent = 'Not one of the words.';
    }
  });
});
document.getElementById('reveal').onclick = () => {
  const left = WORDS.filter(w => !found.includes(w.word));
  if (!left.length) { msg.textContent = 'Nothing left to find.'; return; }
  const w = left[Math.floor(Math.random() * left.length)];
  found.push(w.word);
  try { localStorage.setItem(KEY, JSON.stringify(found)); } catch (e) {}
  msg.className = 'msg'; msg.textContent = 'Shown: ' + w.display;
  paint();
};
document.getElementById('clear').onclick = () => {
  found = [];
  try { localStorage.removeItem(KEY); } catch (e) {}
  document.querySelectorAll('.found').forEach(d => d.classList.remove('found'));
  msg.textContent = ''; msg.className = 'msg';
};
paint();
"""
    script = (script.replace("__WORDS__", json.dumps(placed))
                    .replace("__SIZE__", str(size)))

    out.write_text(_game_page(
        "Word search", lesson,
        f"{len(placed)} words from this lesson. Find them all.",
        body, script, f"min({86 / size:.1f}vw, 30px)"), encoding="utf-8")
    return {"words": len(placed), "size": f"{size}x{size}"}


def games_of(lesson: dict) -> list[dict]:
    return lesson.get("games", []) if lesson.get("vocabulary") else []


def game_name(game: dict) -> str:
    return f"{game['number']}-{game['slug']}.html"


def build_games(lesson: dict, wanted: list[dict]) -> dict[str, int]:
    written: dict[str, int] = {}
    for game in wanted:
        out = HERE / game_name(game)
        if game["style"] == "crossword":
            info = build_crossword(lesson, out)
        elif game["style"] == "word-search":
            info = build_word_search(lesson, out)
        else:
            raise SystemExit(f"unknown game style: {game['style']!r}")
        size = out.stat().st_size
        note = (f"   CHECK: {len(info['skipped'])} word(s) would not fit: "
                f"{', '.join(info['skipped'])}" if info.get("skipped") else "")
        print(f"  {out.name:<32} {info['words']:>2} words  {fmt_size(size):>9}   "
              f"grid {info['size']}{note}")
        written[out.name] = info["words"]
    return written


# ---------------------------------------------------------------------------
# The folder README
# ---------------------------------------------------------------------------

def pdf_pages(path: Path) -> int | None:
    """Page count read back out of a PDF.

    Only a fallback: a PDF that keeps its objects in compressed object streams
    hides the /Type /Page keys, and then this finds nothing. The page counts
    the renderer reported are used first.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return len(re.findall(rb"/Type\s*/Page[^s]", data)) or None


def write_readme(lesson: dict, pages: dict[str, int] | None = None) -> Path:
    pages = pages or {}
    rows = []
    audio_total = 0.0
    for part in lesson["parts"]:
        sheet_cell, audio_cell = "—", "—"
        if part.get("sheet"):
            f = HERE / pdf_name(part)
            sheet_cell = f"[PDF]({f.name})" if f.exists() else "not built yet"
        if part.get("audio"):
            f = HERE / mp3_name(part)
            if f.exists():
                audio_total += mp3_duration(f)
                audio_cell = f"[MP3]({f.name})"
            else:
                audio_cell = "not built yet"
        rows.append(f'| {part["number"]} | {part["title"]} | {sheet_cell} '
                    f'| {audio_cell} | {part["minutes"]} |')

    minutes = sum(p["minutes"] for p in lesson["parts"])
    total_bytes = sum(f.stat().st_size for f in HERE.iterdir() if f.is_file())

    big = []
    whole_pdf, whole_mp3 = HERE / "00-lesson.pdf", HERE / "00-full-section.mp3"
    left_out = [p for p in parts_with_sheet(lesson) if not p.get("in_whole", True)]
    if whole_pdf.exists():
        n = pages.get(whole_pdf.name) or pdf_pages(whole_pdf)
        covers = ("every part sheet in one printable document, answer key last"
                  if not left_out else
                  "every part sheet in one printable document, without "
                  + " or ".join(p["title"].lower() for p in left_out))
        big.append(
            f"- [00-lesson.pdf](00-lesson.pdf) — {covers}"
            f"{f', {n} pages' if n else ''}, "
            f"{fmt_size(whole_pdf.stat().st_size)}. **The large option.**")
    if whole_mp3.exists():
        seconds = mp3_duration(whole_mp3)
        big.append(
            "- [00-full-section.mp3](00-full-section.mp3) — the question tracks end to "
            f"end, like a real exam section, {int(round(seconds / 60))} minutes, "
            f"{fmt_size(whole_mp3.stat().st_size)}. **The large option.**")

    how = "\n".join(f"{i}. {line}"
                    for i, line in enumerate(lesson.get("how_to_work", []), 1))
    nl = "\n"

    games_block = ""
    built_games = [g for g in games_of(lesson) if (HERE / game_name(g)).exists()]
    if built_games:
        game_rows = "\n".join(
            f'| {g["number"]} | [{g["title"]}]({game_name(g)}) | {g["minutes"]} | '
            f'{fmt_size((HERE / game_name(g)).stat().st_size)} |'
            for g in built_games)
        games_block = f"""
## After the lesson: two word games

Both are built from this lesson's own words, so nothing in them is new. They
open in a browser, work with no connection, and remember what you have done.

| No. | Game | Minutes | Size |
|---|---|---|---|
{game_rows}
"""

    text = f"""# {lesson["title"]}

**Level:** {lesson["level"]}
**Topic:** {lesson["topic"]}
**Time:** {lesson["time"]} — about {minutes} minutes of work in all
**Skills:** {lesson["skills"]}
**New in this lesson:** {lesson["new_in_this_lesson"]}

## The parts, in study order

| No. | Part | Sheet | Audio | Minutes |
|---|---|---|---|---|
{nl.join(rows)}

Total audio in the numbered parts: **{int(audio_total // 60)} minutes \
{int(audio_total % 60)} seconds**. The whole folder is **{fmt_size(total_bytes)}** —
that is what downloading all of it costs.

## The whole lesson in one file

{nl.join(big) if big else "Not built yet."}
{games_block}
## How to work through this lesson

{how}

---

[Back to the course README](../../README.md) · This file is written by
`build.py` from `lesson.json`. Edit the lesson file, not this one.
"""
    out = HERE / "README.md"
    out.write_text(text, encoding="utf-8")
    print(f"  {out.name:<32}          {fmt_size(out.stat().st_size):>9}")
    return out


# ---------------------------------------------------------------------------
# --check and --plan
# ---------------------------------------------------------------------------

def check(lesson: dict) -> int:
    print("\nEnvironment")
    print(f"  python       : {sys.version.split()[0]}")
    bad = 0

    try:
        import edge_tts
        print(f"  edge-tts     : {getattr(edge_tts, '__version__', 'installed')}")
    except ImportError:
        print("  edge-tts     : NOT INSTALLED  ->  pip install -r ../../requirements.txt")
        bad = 1

    try:
        import markdown
        print(f"  markdown     : {markdown.__version__}")
    except ImportError:
        print("  markdown     : NOT INSTALLED  ->  pip install -r ../../requirements.txt")
        bad = 1

    try:
        import weasyprint
        print(f"  weasyprint   : {weasyprint.__version__}")
    except ImportError:
        print("  weasyprint   : NOT INSTALLED  ->  pip install -r ../../requirements.txt")
        bad = 1
    except OSError as exc:
        print(f"  weasyprint   : INSTALLED BUT CANNOT LOAD ITS LIBRARIES")
        print(f"                 {exc}")
        print("                 On Windows weasyprint needs the GTK runtime "
              "(libgobject, pango),")
        print("                 which pip does not install. See")
        print("                 https://doc.courtbouillon.org/weasyprint/stable/"
              "first_steps.html#windows")
        print("                 The MP3s do not need it: "
              "python build.py --build --audio-only")
        bad = 1

    host = "speech.platform.bing.com"
    try:
        t0 = time.perf_counter()
        socket.create_connection((host, 443), timeout=8).close()
        print(f"  connection   : {host} reachable "
              f"({(time.perf_counter() - t0) * 1000:.0f} ms)")
    except OSError as exc:
        print(f"  connection   : CANNOT REACH {host} ({exc})")
        print("                 Synthesis needs the internet. Every segment that")
        print("                 finished is cached, so run the same command again to")
        print("                 carry on. Sheets need no connection: --build --pdf-only")
        bad = 1

    print(f"  silence test : {len(silence_mp3(1.0))} bytes for 1.0 s  (expect 6048)")
    print(f"  cache        : {cache_dir()}")

    print("\nLesson")
    print(f"  file         : {LESSON_FILE.name} - valid")
    print(f"  title        : {lesson['title']}")
    print(f"  parts        : {len(lesson['parts'])} "
          f"({len(parts_with_sheet(lesson))} with a sheet, "
          f"{len(parts_with_audio(lesson))} with audio)")

    print("\nReady. Run:  python build.py --plan\n" if not bad else
          "\nFix the lines above, then run:  python build.py --check\n")
    return bad


def plan(lesson: dict) -> int:
    voices = lesson["voices"]
    print(f'\n{lesson["title"]}')
    print(f'{lesson["level"]} · {lesson["topic"]}\n')
    print(f"  {'No.':<4} {'Part':<26} {'min':>4}   {'sheet':<34} audio")
    print("  " + "-" * 104)

    audio_seconds = 0.0
    est_bytes = 0
    for part in lesson["parts"]:
        sheet = "—"
        if part.get("sheet"):
            f = HERE / pdf_name(part)
            if f.exists():
                sheet = f"{f.name} ({fmt_size(f.stat().st_size)})"
                est_bytes += f.stat().st_size
            else:
                sheet = f"{pdf_name(part)} (new)"
        audio = "—"
        if part.get("audio"):
            seconds = estimate_part(part["segments"], voices)
            audio_seconds += seconds
            est_bytes += int(seconds * BYTES_PER_SECOND)
            calls = len({(s["say"], s.get("voice", "narrator"))
                         for s in part["segments"] if "say" in s})
            audio = (f"{mp3_name(part):<26} {fmt_time(seconds):>9}  "
                     f"~{fmt_size(seconds * BYTES_PER_SECOND):>8}  {calls:>3} tts calls")
        print(f'  {part["number"]:<4} {part["title"][:26]:<26} {part["minutes"]:>4}   '
              f"{sheet:<34} {audio}")

    print("  " + "-" * 104)
    whole = HERE / "00-lesson.pdf"
    sheet = (f"00-lesson.pdf ({fmt_size(whole.stat().st_size)})" if whole.exists()
             else "00-lesson.pdf (new)")
    if whole.exists():
        est_bytes += whole.stat().st_size
    full = full_section_segments(lesson)
    audio = "—"
    if full:
        seconds = estimate_part(full, voices)
        est_bytes += int(seconds * BYTES_PER_SECOND)
        audio = (f"{'00-full-section.mp3':<26} {fmt_time(seconds):>9}  "
                 f"~{fmt_size(seconds * BYTES_PER_SECOND):>8}  parts "
                 f"{', '.join((lesson['full_section'] or {}).get('parts', []))}")
    print(f'  00   {"whole lesson":<26} {"":>4}   {sheet:<34} {audio}')

    chars = sum(len(s["say"]) for p in parts_with_audio(lesson)
                for s in p["segments"] if "say" in s)
    uncached = sum(
        1 for p in parts_with_audio(lesson) for s in p["segments"] if "say" in s
        and not (cache_dir()
                 / f"{cache_key(s['say'], voices[s.get('voice', 'narrator')])}.mp3").exists())
    print(f"\n  {len(parts_with_audio(lesson))} parts with audio: "
          f"{audio_seconds / 60:.1f} minutes in the numbered parts.")
    print(f"  About {chars:,} characters to synthesize; {uncached} spoken segments are "
          f"not cached yet.")
    print(f"  Estimated folder size once built: ~{fmt_size(est_bytes)}.")
    print("  Audio sizes come from the 48 kbps bit rate; PDF sizes are the files "
          "already on disk.\n")
    return 0


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true",
                      help="check dependencies and connection, build nothing")
    mode.add_argument("--plan", action="store_true",
                      help="print the parts, lengths and sizes it would make")
    mode.add_argument("--build", action="store_true",
                      help="build every PDF, every MP3, and this folder's README")

    ap.add_argument("--only", nargs="+", metavar="NN",
                    help="part numbers to build, e.g. --only 01 04; "
                         "the 00- files are then left alone")
    ap.add_argument("--pdf-only", action="store_true",
                    help="sheets and games only, no network")
    ap.add_argument("--audio-only", action="store_true", help="MP3s only")
    ap.add_argument("--force", action="store_true",
                    help="ignore the audio cache and synthesize again")
    args = ap.parse_args()

    lesson = load_lesson()

    if args.check:
        return check(lesson)
    if args.plan:
        return plan(lesson)

    if args.pdf_only and args.audio_only:
        print("--pdf-only and --audio-only cancel each other out.", file=sys.stderr)
        return 2

    page_counts: dict[str, int] = {}
    chosen, whole = lesson["parts"], True
    if args.only:
        wanted = set(args.only)
        chosen = [p for p in lesson["parts"] if p["number"] in wanted]
        whole = False
        known = {p["number"] for p in lesson["parts"]} | {
            g["number"] for g in games_of(lesson)}
        missing = wanted - known
        if missing:
            print(f"Nothing numbered {', '.join(sorted(missing))}. This lesson has "
                  f"{', '.join(sorted(known))}.", file=sys.stderr)
            return 1

    t0 = time.perf_counter()
    print(f'\nBuilding {lesson["title"]}  ->  {HERE}')

    if not args.audio_only:
        sheets = [p for p in chosen if p.get("sheet")]
        print(f"\nSheets ({len(sheets)}"
              f"{' + the whole lesson' if whole else ''})")
        try:
            page_counts = build_sheets(lesson, sheets, whole)
        except OSError as exc:
            print(f"\nStopped: weasyprint cannot load its libraries.\n  {exc}",
                  file=sys.stderr)
            print("On Windows it needs the GTK runtime (libgobject, pango), which pip\n"
                  "does not install. See https://doc.courtbouillon.org/weasyprint/"
                  "stable/first_steps.html#windows\n"
                  "The MP3s do not need it: python build.py --build --audio-only",
                  file=sys.stderr)
            return 1

    if not args.audio_only and games_of(lesson):
        wanted_games = games_of(lesson)
        if args.only:
            wanted_games = [g for g in wanted_games if g["number"] in set(args.only)]
        if wanted_games:
            print(f"\nGames ({len(wanted_games)})")
            build_games(lesson, wanted_games)

    if not args.pdf_only:
        audio = [p for p in chosen if p.get("audio")]
        print(f"\nAudio ({len(audio)}{' + the full section' if whole else ''})")
        try:
            asyncio.run(build_audio(lesson, audio, whole, args.force))
        except Offline as exc:
            print(f"\nStopped: edge-tts could not be reached.\n  {exc}", file=sys.stderr)
            print("Every segment that finished is cached in\n"
                  f"  {cache_dir()}\n"
                  "so run the same command again when the connection is back; it will\n"
                  "carry on from where it stopped and re-synthesize nothing.",
                  file=sys.stderr)
            return 1

    print("\nREADME")
    write_readme(lesson, page_counts)

    files = sorted(f for f in HERE.iterdir() if f.is_file())
    total = sum(f.stat().st_size for f in files)
    print(f"\nDone in {time.perf_counter() - t0:.0f}s. {len(files)} files in "
          f"{HERE.name}/, {fmt_size(total)} in all.")
    print("Size is what decides whether she can download it: one numbered part at a "
          "time costs a few hundred KB.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
