#!/usr/bin/env python3
"""What the student has already met, read out of the lessons themselves.

Nine lessons are about a megabyte of JSON. An author who has to open all of
them to find out whether *restore* has been taught, or which five words the
next lesson owes back, will not do it every time -- and the two rules that
hold this course together are exactly the ones that break quietly:

  * a key word is taught in one lesson and never again;
  * lesson N hands back five of lesson N-2's words as `recall`.

    python scripts/course_state.py            the whole course
    python scripts/course_state.py --words    just the key-word index
    python scripts/course_state.py --recall 11   what lesson 11 owes back

Run from the repository root. It reads lessons/*/lesson.json and nothing else,
so it cannot disagree with the course.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def lessons():
    for path in sorted(ROOT.glob("lessons/lesson-*/lesson.json")):
        with path.open(encoding="utf-8") as fh:
            yield json.load(fh)


def key_index():
    """word (lower-cased) -> the lesson that taught it."""
    index = {}
    for d in lessons():
        for v in d.get("vocabulary", []):
            index.setdefault(v["word"].lower(), d["lesson"])
    return index


def main():
    argv = sys.argv[1:]

    if argv and argv[0] == "--recall":
        want = int(argv[1]) - 2
        for d in lessons():
            if d["lesson"] == want:
                print("Lesson %d must recall five of Lesson %d's fourteen:"
                      % (want + 2, want))
                for v in d["vocabulary"]:
                    icon = "  (icon: %s)" % v["icon"] if v.get("icon") else ""
                    print("  %-14s %-10s %s%s"
                          % (v["word"], v.get("type", ""), v["meaning"], icon))
                return 0
        print("no lesson %d" % want, file=sys.stderr)
        return 1

    index = key_index()

    if argv and argv[0] == "--words":
        for word in sorted(index):
            print("%-14s L%d" % (word, index[word]))
        print("\n%d key words across %d lessons."
              % (len(index), len(set(index.values()))))
        return 0

    for d in lessons():
        parts = [p["slug"] for p in d["parts"]]
        grammar = [p for p in parts if p.startswith("grammar")]
        print("Lesson %-2d %s" % (d["lesson"], d["title"]))
        print("  level      %s" % d["level"])
        print("  topic      %s" % d["topic"])
        print("  passage    %s words" % d.get("passage_words", "?"))
        print("  new        %s" % d.get("new_in_this_lesson", ""))
        print("  parts      %d: %s" % (len(parts), ", ".join(
            "%s-%s" % (p["number"], p["slug"]) for p in d["parts"])))
        print("  grammar    %s" % (grammar[0] if grammar else "-"))
        print("  pronounce  %s" % (parts[4] if len(parts) > 4 else "-"))
        print("  games      %s" % ", ".join(
            "%s:%s" % (g["number"], g["style"]) for g in d.get("games", [])))
        print("  key (%2d)   %s" % (len(d.get("vocabulary", [])), ", ".join(
            v["word"] for v in d.get("vocabulary", []))))
        print("  recall(%d)  %s" % (len(d.get("recall", [])), ", ".join(
            r["word"] for r in d.get("recall", [])) or "-"))
        print()

    print("%d distinct key words. No word may be taught twice; "
          "--words is the index." % len(index))
    collisions = {}
    for d in lessons():
        for v in d.get("vocabulary", []):
            collisions.setdefault(v["word"].lower(), []).append(d["lesson"])
    bad = {w: ls for w, ls in collisions.items() if len(ls) > 1}
    print("collisions: %s" % (bad if bad else "none"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
