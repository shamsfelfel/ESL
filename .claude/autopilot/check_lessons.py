#!/usr/bin/env python3
"""Structural gate for Lessons 10 to 12. Facts about the repository, not opinions.

Run by verify.sh after a phase, never by the authoring agent as its own proof.
Every check here is something an author can get wrong while believing the
lesson is finished, and that the build itself will not notice:

  * a fifteenth key word, or a thirteenth part;
  * a word this course already taught in Lesson 4;
  * `recall` taken from the wrong lesson, which silently breaks the two-lesson
    spacing the whole course rests on;
  * a passage that grew to 600 words while the heading still says 520 — the
    number is printed in three places and only one of them regenerates;
  * nine comprehension questions instead of ten, or seven types instead of
    eight.

    python .claude/autopilot/check_lessons.py              structure only
    python .claude/autopilot/check_lessons.py --built       also demand the media
    python .claude/autopilot/check_lessons.py --require 10 11 12

Exit status is 0 only if every check passed.
"""
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
NEW = (10, 11, 12)

PART_SLUGS = {
    1: "passage", 2: "listening-questions", 3: "vocabulary",
    6: "comprehension", 7: "true-false", 8: "speaking", 9: "writing",
    10: "review", 11: "answer-key", 12: "passage-slow",
}
GAME_STYLES = ["crossword", "word-search", "memory", "criss-cross",
               "cryptogram"]
SKILLS = ("Listening → Reading → Vocabulary → Grammar → "
          "Comprehension → Speaking → Writing")
TYPES = ["Factual", "Negative factual", "Vocabulary in context", "Reference",
         "Inference", "Sentence insertion", "Purpose of a paragraph",
         "Purpose of the whole passage", "The writer's attitude"]
MAX_WORDS = 545          # 535 planned, plus the slack the counter itself has
MAX_FOLDER_MB = 20.5     # Lesson 9 is 17.9 MB; 8 is 20.2 MB

fails = []
notes = []


def fail(msg):
    fails.append(msg)


def ok(msg):
    notes.append(msg)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def words_in_passage(md):
    """Count the passage the way the course counts it, to within a word or two.

    Calibrated against Lessons 6 to 9, whose declared counts are 504, 510, 516
    and 532: this returns 504, 508, 515, 530. The declared figure is therefore
    checked with slack, while the figure printed in the heading is checked
    against `passage_words` exactly -- that one is a copy of a number and has
    no excuse to drift.
    """
    m = re.search(r"^###\s+Passage:.*$", md, re.M)
    if not m:
        return None
    rest = md[m.end():]
    nxt = re.search(r"^###\s", rest, re.M)
    if nxt:
        rest = rest[:nxt.start()]
    rest = re.sub(r"\[[A-D]\]", " ", rest)      # insertion markers are printed, not words
    rest = re.sub(r"[*_>`#]", "", rest)
    return len([w for w in rest.split() if re.search(r"[A-Za-z0-9]", w)])


def key_words_before(n):
    """Every key word taught in a lesson earlier than n, lower-cased."""
    seen = {}
    for path in sorted(ROOT.glob("lessons/lesson-*/lesson.json")):
        d = load(path)
        if d["lesson"] >= n:
            continue
        for v in d.get("vocabulary", []):
            seen.setdefault(v["word"].lower(), d["lesson"])
    return seen


def check_structure(n, d, icons):
    tag = "L%d" % n
    parts = d.get("parts", [])

    if len(parts) != 12:
        fail("%s has %d parts, not 12 (Lesson 9's thirteen-part shape is not "
             "the new normal; there is no news session in this run)"
             % (tag, len(parts)))
    for i, p in enumerate(parts, start=1):
        if p.get("number") != "%02d" % i:
            fail("%s part %d is numbered %r, out of order"
                 % (tag, i, p.get("number")))
        want = PART_SLUGS.get(i)
        if want and p.get("slug") != want:
            fail("%s part %02d is %r, must be %r" % (tag, i, p.get("slug"), want))
    if len(parts) >= 5:
        if not parts[3].get("slug", "").startswith("grammar-"):
            fail("%s part 04 is %r, must be grammar-<topic>"
                 % (tag, parts[3].get("slug")))
        if parts[4].get("slug", "").startswith(("grammar", "comprehension")):
            fail("%s part 05 is %r, must be the pronunciation part"
                 % (tag, parts[4].get("slug")))

    games = d.get("games", [])
    if [g.get("style") for g in games] != GAME_STYLES:
        fail("%s games are %r, must be %r"
             % (tag, [g.get("style") for g in games], GAME_STYLES))
    if [g.get("number") for g in games] != ["%d" % i for i in range(13, 18)]:
        fail("%s games are numbered %r, must be 13 to 17 (a game is numbered "
             "after the lesson's last part, and the last part is 12)"
             % (tag, [g.get("number") for g in games]))

    vocab = d.get("vocabulary", [])
    if len(vocab) != 14:
        fail("%s has %d key words, must be 14" % (tag, len(vocab)))
    for v in vocab:
        for field in ("word", "answer", "meaning", "arabic"):
            if not v.get(field):
                fail("%s key word %r has no %s" % (tag, v.get("word"), field))
        if v.get("answer") and v["answer"] != re.sub(r"[^A-Za-z]", "", v["word"]).upper():
            # 'keep / kept' style entries are legitimate; only flag a mismatch
            # that is not explained by punctuation in the headword.
            if "/" not in v["word"] and " " not in v["word"]:
                fail("%s key word %r has answer %r"
                     % (tag, v["word"], v["answer"]))
        if v.get("icon") and v["icon"] not in icons:
            fail("%s key word %r names icon %r, which is not in icons.json"
                 % (tag, v["word"], v["icon"]))

    earlier = key_words_before(n)
    for v in vocab:
        w = v["word"].lower()
        if w in earlier:
            fail("%s teaches %r, already taught in Lesson %d. A key word is "
                 "taught once in this course." % (tag, v["word"], earlier[w]))

    recall = d.get("recall", [])
    if len(recall) != 5:
        fail("%s has %d recalled words, must be 5" % (tag, len(recall)))
    src = ROOT / ("lessons/lesson-%02d/lesson.json" % (n - 2))
    if src.exists():
        owed = {v["word"].lower() for v in load(src).get("vocabulary", [])}
        for r in recall:
            if r["word"].lower() not in owed:
                fail("%s recalls %r, which is not one of Lesson %d's fourteen. "
                     "Vocabulary comes back on a two-lesson gap and nothing "
                     "else." % (tag, r["word"], n - 2))
        for r in recall:
            if r.get("icon") and r["icon"] not in icons:
                fail("%s recalled word %r names a missing icon %r"
                     % (tag, r["word"], r["icon"]))
    else:
        fail("%s cannot be checked: lesson-%02d is missing" % (tag, n - 2))

    if d.get("skills") != SKILLS:
        fail("%s skills line is %r, must be the twelve-part line"
             % (tag, d.get("skills")))
    if d.get("footer") != d.get("title"):
        fail("%s footer %r does not match title %r"
             % (tag, d.get("footer"), d.get("title")))
    fs = (d.get("full_section") or {}).get("parts")
    if fs != ["01", "02", "06", "07"]:
        fail("%s full_section covers %r, must be 01, 02, 06, 07 in a "
             "twelve-part lesson" % (tag, fs))

    by_slug = {p.get("slug"): p for p in parts}

    md = (by_slug.get("passage") or {}).get("markdown", "")
    counted = words_in_passage(md)
    declared = d.get("passage_words")
    if counted is None:
        fail("%s part 01 has no '### Passage:' heading" % tag)
    else:
        heading = re.search(r"\((\d+)\s+words\)", md)
        if not heading:
            fail("%s passage heading does not print its word count" % tag)
        elif int(heading.group(1)) != declared:
            fail("%s heading says %s words, passage_words says %s. The count "
                 "is printed in three places and only the output blocks "
                 "regenerate." % (tag, heading.group(1), declared))
        if declared is None or abs(counted - declared) > 5:
            fail("%s declares %s words, counted %d" % (tag, declared, counted))
        if counted > MAX_WORDS:
            fail("%s passage is %d words. The length holds at about 500 from "
                 "Lesson 6 on; the ceiling for this run is %d."
                 % (tag, counted, MAX_WORDS))
        else:
            ok("%s passage %d words (declared %s)" % (tag, counted, declared))
    for marker in ("[A]", "[B]", "[C]", "[D]"):
        if marker not in md:
            fail("%s passage is missing insertion marker %s" % (tag, marker))

    comp = (by_slug.get("comprehension") or {}).get("markdown", "")
    numbered = re.findall(r"^\*\*(\d+)\.\s*\(([^)]+)\)\*\*", comp, re.M)
    if len(numbered) != 10:
        fail("%s comprehension has %d labelled questions, must be 10 — the "
             "size of a real TOEFL set, fixed since Lesson 5"
             % (tag, len(numbered)))
    if [k for k, _ in numbered] != [str(i) for i in range(1, 11)]:
        fail("%s comprehension questions are numbered %r"
             % (tag, [k for k, _ in numbered]))
    found = {t.strip().lower() for _, t in numbered}
    missing = [t for t in TYPES if t.lower() not in found]
    if len(numbered) == 10 and missing:
        fail("%s comprehension is missing the type(s) %s. Eight types, "
             "complete since Lesson 5, and the format never changes."
             % (tag, ", ".join(missing)))
    unknown = [t for t in found if t not in {x.lower() for x in TYPES}]
    if unknown:
        fail("%s comprehension uses unknown question type(s) %s"
             % (tag, ", ".join(sorted(unknown))))
    if not fails:
        ok("%s ten questions, eight types" % tag)


def check_built(n, d):
    tag = "L%d" % n
    folder = ROOT / ("lessons/lesson-%02d" % n)
    present = list(folder.glob("0*.pdf")) + list(folder.glob("0*.mp3"))
    if not present:
        ok("%s not built yet (no media in the folder) — skipping media checks"
           % tag)
        return

    want = []
    for p in d.get("parts", []):
        if p.get("sheet"):
            want.append("%s-%s.pdf" % (p["number"], p["slug"]))
        if p.get("audio"):
            want.append("%s-%s.mp3" % (p["number"], p["slug"]))
    for g in d.get("games", []):
        want.append("%s-%s.html" % (g["number"], g["slug"]))
    want += ["00-lesson.pdf", "00-full-section.mp3", "README.md"]

    for name in want:
        f = folder / name
        if not f.exists():
            fail("%s is missing %s" % (tag, name))
        elif f.stat().st_size == 0:
            fail("%s has an empty %s" % (tag, name))

    strays = [p.name for p in folder.iterdir()
              if p.name not in want
              and p.name not in ("lesson.json", "build.py")
              and not p.name.startswith(".")]
    if strays:
        fail("%s has files nothing asked for: %s" % (tag, ", ".join(sorted(strays))))

    total = sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
    mb = total / 1e6
    if mb > MAX_FOLDER_MB:
        fail("%s folder is %.1f MB, over the %.1f MB ceiling. Every part is a "
             "download she pays for." % (tag, mb, MAX_FOLDER_MB))
    else:
        ok("%s folder %.1f MB" % (tag, mb))

    if (folder / "__pycache__").exists():
        fail("%s left a __pycache__ in the lesson folder" % tag)


def main():
    argv = sys.argv[1:]
    want_built = "--built" in argv
    require = []
    if "--require" in argv:
        require = [int(a) for a in argv[argv.index("--require") + 1:]
                   if a.isdigit()]

    icons = load(ROOT / "icons.json").get("icons", {})

    checked = []
    for n in NEW:
        path = ROOT / ("lessons/lesson-%02d/lesson.json" % n)
        if not path.exists():
            if n in require:
                fail("L%d does not exist, and this phase requires it" % n)
            continue
        try:
            d = load(path)
        except Exception as exc:
            fail("L%d lesson.json will not parse: %s" % (n, exc))
            continue
        if d.get("lesson") != n:
            fail("lessons/lesson-%02d declares lesson %r" % (n, d.get("lesson")))
        checked.append(n)
        check_structure(n, d, icons)
        if want_built or n in require:
            check_built(n, d)

    if require:
        for n in require:
            folder = ROOT / ("lessons/lesson-%02d" % n)
            if not (folder / "00-lesson.pdf").exists():
                fail("L%d is not built: no 00-lesson.pdf" % n)

    for line in notes:
        print("      %s" % line)
    if not checked and not require:
        print("      no new lesson folders yet")
    if fails:
        print()
        for line in fails:
            print("      FAIL  %s" % line)
        print("\n      %d structural check(s) failed" % len(fails))
        return 1
    print("      structure: every check passed (%s)"
          % (", ".join("L%d" % n for n in checked) or "nothing to check"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
