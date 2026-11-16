#!/usr/bin/env python3
"""Structural gate for Progress Test 2. Facts about the repository, not opinions.

A test can go wrong in ways a lesson cannot, and two of them are quiet:

  * the marks stop adding up to 100, because a question's label says 4 and the
    section heading still says 30;
  * `in_whole` is not false on the answer key, so `00-lesson.pdf` -- the one
    file a teacher prints to hand out -- carries the answers to the test being
    sat.

It also checks the thing a test exists for: that both texts are ones she has
never read. A passage lifted from a lesson makes the whole test worthless, and
an eight-word run shared with any of the twelve lessons is the signature.

    python .claude/autopilot/check_test.py            structure only
    python .claude/autopilot/check_test.py --built     also demand the files

Exit status is 0 only if every check passed.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TEST = "test-02"

SLUGS = ["listening", "reading", "vocabulary-and-grammar", "writing",
         "speaking", "answer-key"]
SECTION_MARKS = {"listening": 20, "reading": 30, "vocabulary-and-grammar": 30,
                 "writing": 10, "speaking": 10}
TYPES = {"factual", "negative factual", "vocabulary in context", "reference",
         "inference", "sentence insertion", "purpose of a paragraph",
         "purpose of the whole passage", "the writer's attitude"}
PASSAGE_MIN, PASSAGE_MAX = 540, 600
MAX_FOLDER_MB = 10.0

fails, notes = [], []


def fail(m):
    fails.append(m)


def ok(m):
    notes.append(m)


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def words(text):
    text = re.sub(r"\[[A-D]\]", " ", text)
    text = re.sub(r"[*_>`#]", "", text)
    return [w for w in text.split() if re.search(r"[A-Za-z0-9]", w)]


def passage_body(md):
    m = re.search(r"^###\s+Passage:.*$", md, re.M)
    if not m:
        return None
    rest = md[m.end():]
    nxt = re.search(r"^###\s", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def shingles(text, n=8):
    w = [re.sub(r"[^a-z0-9]", "", x.lower()) for x in words(text)]
    w = [x for x in w if x]
    return {" ".join(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def lesson_texts():
    """Every passage in the course, so the test's texts can be checked as new."""
    out = {}
    for p in sorted(ROOT.glob("lessons/lesson-*/lesson.json")):
        d = load(p)
        for part in d["parts"]:
            if part.get("slug") == "passage":
                body = passage_body(part.get("markdown") or "")
                if body:
                    out["Lesson %d" % d["lesson"]] = body
    t1 = ROOT / "tests/test-01/lesson.json"
    if t1.exists():
        d = load(t1)
        for part in d["parts"]:
            md = part.get("markdown") or ""
            body = passage_body(md)
            if body:
                out["Progress Test 1"] = body
            for seg in part.get("segments") or []:
                if isinstance(seg, dict) and seg.get("say"):
                    out.setdefault("Progress Test 1 audio", "")
                    out["Progress Test 1 audio"] += " " + seg["say"]
    return out


def labelled(md):
    """[(number, type, marks)] from '**1. (Factual, 3 marks)**'."""
    out = []
    for m in re.finditer(r"\*\*(\d+)\.\s*\(([^)]*?)\)\*\*", md):
        body = m.group(2)
        mk = re.search(r"(\d+)\s*marks?", body)
        kind = re.sub(r",?\s*\d+\s*marks?", "", body).strip()
        out.append((int(m.group(1)), kind, int(mk.group(1)) if mk else None))
    return out


def stated_total(md):
    m = re.search(r"\((\d+)\s*marks?", md)
    return int(m.group(1)) if m else None


def main():
    want_built = "--built" in sys.argv[1:]
    path = ROOT / ("tests/%s/lesson.json" % TEST)
    if not path.exists():
        print("      %s does not exist yet" % TEST)
        return 0
    try:
        d = load(path)
    except Exception as exc:
        print("      FAIL  %s/lesson.json will not parse: %s" % (TEST, exc))
        return 1

    parts = d.get("parts", [])
    if [p.get("slug") for p in parts] != SLUGS:
        fail("parts are %r, must be %r" % ([p.get("slug") for p in parts], SLUGS))
    for i, p in enumerate(parts, start=1):
        if p.get("number") != "%02d" % i:
            fail("part %d is numbered %r" % (i, p.get("number")))
    by = {p.get("slug"): p for p in parts}

    key = by.get("answer-key")
    if key is None:
        fail("there is no answer-key part")
    elif key.get("in_whole") is not False:
        fail("the answer key has in_whole=%r, must be false — otherwise "
             "00-lesson.pdf prints the answers to the test being sat"
             % key.get("in_whole"))
    else:
        ok("the answer key is kept out of 00-lesson.pdf (in_whole: false)")

    fs = (d.get("full_section") or {}).get("parts")
    if fs != ["01", "05"]:
        fail("full_section covers %r, must be 01 and 05 (listening and "
             "speaking are the parts with audio)" % fs)
    for slug in ("listening", "speaking"):
        if by.get(slug) and not by[slug].get("audio"):
            fail("part %s has no audio" % slug)

    # --- the marks, which must still add to 100 -------------------------------
    total = 0
    for slug, want in SECTION_MARKS.items():
        p = by.get(slug)
        if not p:
            continue
        md = p.get("markdown") or ""
        said = stated_total(md)
        if said != want:
            fail("%s heading states %r marks, must be %d" % (slug, said, want))
        total += want
        qs = labelled(md)
        if slug in ("listening", "reading"):
            summed = sum(m for _, _, m in qs if m)
            if any(m is None for _, _, m in qs):
                fail("%s has a question label with no marks in it" % slug)
            if summed != want:
                fail("%s questions add up to %d, not %d" % (slug, summed, want))
            else:
                ok("%s: %d questions adding to %d" % (slug, len(qs), want))
            if [n for n, _, _ in qs] != list(range(1, len(qs) + 1)):
                fail("%s questions are numbered %r" % (slug, [n for n, _, _ in qs]))
        if slug == "vocabulary-and-grammar":
            pm = [int(x) for x in re.findall(r"Part [A-D][^(]*\((\d+)\s*marks?", md)]
            if len(pm) != 4:
                fail("section 3 has %d marked parts, must be four (A to D)" % len(pm))
            elif sum(pm) != 30:
                fail("section 3's parts add up to %d, not 30: %r" % (sum(pm), pm))
            else:
                ok("section 3: four parts adding to 30 %r" % pm)
    if total != 100:
        fail("the five sections add up to %d, not 100" % total)
    else:
        ok("the five sections add up to 100")

    # --- the reading passage --------------------------------------------------
    rd = (by.get("reading") or {}).get("markdown", "")
    body = passage_body(rd)
    if body is None:
        fail("the reading section has no '### Passage:' heading")
    else:
        counted = len(words(body))
        declared = d.get("passage_words")
        head = re.search(r"\((\d+)\s+words\)", rd)
        if not head:
            fail("the passage heading does not print its word count")
        elif declared is not None and int(head.group(1)) != declared:
            fail("the heading says %s words and passage_words says %s"
                 % (head.group(1), declared))
        if declared is None or abs(counted - declared) > 6:
            fail("passage_words is %s, counted %d" % (declared, counted))
        if not (PASSAGE_MIN <= counted <= PASSAGE_MAX):
            fail("the passage is %d words; this test is where the reading goes "
                 "long, so %d to %d" % (counted, PASSAGE_MIN, PASSAGE_MAX))
        else:
            ok("reading passage %d words (declared %s)" % (counted, declared))
        for mk in ("[A]", "[B]", "[C]", "[D]"):
            if mk not in rd:
                fail("the passage is missing insertion marker %s" % mk)
        kinds = {k.lower() for _, k, _ in labelled(rd)}
        unknown = kinds - TYPES
        if unknown:
            fail("the reading uses unknown question type(s): %s"
                 % ", ".join(sorted(unknown)))
        elif len(kinds) < 7:
            fail("the reading uses only %d distinct question types; the eight "
                 "are complete from Lesson 5 and this test should cover them"
                 % len(kinds))
        else:
            ok("reading: %d distinct question types" % len(kinds))

    # --- both texts must be ones she has never read ---------------------------
    spoken = " ".join(s.get("say", "") for s in
                      (by.get("listening", {}).get("segments") or [])
                      if isinstance(s, dict))
    seen = lesson_texts()
    for name, text in (("the reading passage", body or ""),
                       ("the listening text", spoken)):
        mine = shingles(text)
        for src, other in seen.items():
            shared = mine & shingles(other)
            if shared:
                fail("%s shares wording with %s (%r) — both texts must be ones "
                     "she has never read" % (name, src, sorted(shared)[0][:60]))
                break
        else:
            if mine:
                ok("%s shares no eight-word run with any lesson or Test 1" % name)

    # --- Part A must examine Lessons 4 to 8's own words -----------------------
    taught = {}
    for n in range(4, 9):
        p = ROOT / ("lessons/lesson-%02d/lesson.json" % n)
        if p.exists():
            for v in load(p).get("vocabulary", []):
                taught[v["word"].lower()] = n
    keymd = (key or {}).get("markdown", "")
    m = re.search(r"\*\*Part A:?\*\*[:\s]*(.+)", keymd)
    if not m:
        fail("the key has no '**Part A:**' line of answers")
    else:
        answers = [a.strip(" .*") for a in re.split(r"·|·", m.group(1))]
        answers = [re.sub(r"^\d+\.\s*", "", a).strip() for a in answers if a.strip()]
        if len(answers) != 10:
            fail("Part A has %d answers, must be 10: %r" % (len(answers), answers))
        bad = [a for a in answers if a.lower() not in taught]
        if bad:
            fail("Part A answers that Lessons 4 to 8 never taught: %s"
                 % ", ".join(bad))
        else:
            spread = sorted({taught[a.lower()] for a in answers})
            if len(spread) < 4:
                fail("Part A's ten answers come from only %d of Lessons 4 to 8 "
                     "(%r); spread them" % (len(spread), spread))
            else:
                ok("Part A: ten words, all taught in Lessons %s"
                   % ", ".join(str(x) for x in spread))

    # --- every question answered ---------------------------------------------
    # One marking row per question in sections 1 and 2, so a question cannot
    # exist with nothing to mark it against.
    asked = sum(len(labelled((by.get(s) or {}).get("markdown") or ""))
                for s in ("listening", "reading"))
    rows = len(re.findall(r"^\|\s*\d+\s*\|", keymd, re.M))
    if asked and rows < asked:
        fail("sections 1 and 2 ask %d questions but the key has %d marking "
             "rows" % (asked, rows))
    elif asked:
        ok("the key has a marking row for each of the %d questions" % asked)

    # --- built files ----------------------------------------------------------
    folder = ROOT / ("tests/%s" % TEST)
    if want_built and (folder / "00-lesson.pdf").exists():
        wanted = ["00-lesson.pdf", "00-full-section.mp3", "README.md"]
        for p in parts:
            if p.get("sheet"):
                wanted.append("%s-%s.pdf" % (p["number"], p["slug"]))
            if p.get("audio"):
                wanted.append("%s-%s.mp3" % (p["number"], p["slug"]))
        for name in wanted:
            f = folder / name
            if not f.exists():
                fail("missing %s" % name)
            elif f.stat().st_size == 0:
                fail("empty %s" % name)
        mb = sum(f.stat().st_size for f in folder.iterdir() if f.is_file()) / 1e6
        if mb > MAX_FOLDER_MB:
            fail("the folder is %.1f MB, over the %.1f MB ceiling for a test"
                 % (mb, MAX_FOLDER_MB))
        else:
            ok("folder %.1f MB" % mb)
    elif want_built:
        ok("not built yet — skipping the file checks")

    for line in notes:
        print("      %s" % line)
    if fails:
        print()
        for line in fails:
            print("      FAIL  %s" % line)
        print("\n      %d check(s) failed" % len(fails))
        return 1
    print("      Progress Test 2: every check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
