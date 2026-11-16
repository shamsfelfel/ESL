#!/usr/bin/env python3
"""PreToolUse hook for the Lessons 10-12 build.

The agent runs with --dangerously-skip-permissions, so nothing else stands
between it and the repository. Hooks still fire in that mode, which is the
point: the standing rules in the preamble are advice until something enforces
them, and an agent with a failing gate in front of it is exactly when advice
loses.

What this repository has to lose is unusual and worth being explicit about. Nine
lessons are finished, committed as PDFs and MP3s, and already on a student's
phone. The expensive mistake here is not a broken build -- it is a rebuild of
Lesson 4 that rewrites fifty files she has already paid data for, or a hand-
edited PDF that the next build silently throws away.

Reads the hook payload on stdin, writes a permission decision on stdout.
Fails OPEN on an unexpected payload (a crashed hook must not wedge the run),
fails CLOSED on anything it actually recognises.
"""
import json
import os
import re
import sys

ALLOW = {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                "permissionDecision": "allow"}}


def deny(reason):
    json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                      "permissionDecision": "deny",
                                      "permissionDecisionReason": reason}},
              sys.stdout)
    sys.exit(0)


NEVER_PUSH = (
    "Standing rule: this run does not push, to any branch or remote. Commit "
    "locally on main; Raed reviews the lessons and pushes them himself."
)
SHIPPED = (
    "Lessons 1 to 9 and Progress Test 1 are finished, committed and on the "
    "student's phone. This run adds Lessons 10, 11 and 12 and changes nothing "
    "else. If you believe a shipped lesson is wrong, write it up in "
    "docs/LESSONS-10-12-PROGRESS.md and leave it alone."
)
GENERATED = (
    "%s is written by build.py from lesson.json. A hand edit here is destroyed "
    "by the next build, which is how a night's work disappears with nothing "
    "reporting a failure. Edit lesson.json and rebuild."
)

BASH_RULES = [
    (r"\bgit\s+push\b(?!.*--dry-run)", NEVER_PUSH),
    (r"\bgit\s+(reset\s+--hard|clean\s+-[a-zA-Z]*f)\b",
     "Destructive to uncommitted work, including an earlier phase's. If you "
     "need to undo something, commit first and revert deliberately."),
    (r"\bgit\s+(rebase|filter-branch|push\s+--force|commit\s+--amend)\b",
     "Do not rewrite history during this run. Each phase's commits are the "
     "record of what happened and Raed reads them afterwards."),
    (r"\bgit\s+checkout\s+(-b\s+)?(?!--)\S",
     "Stay on main. The phase pack assumes one linear branch and the gate "
     "checks the working tree against it. `git checkout -- <path>` to discard "
     "a change is fine."),
    # Both orders, and across `&&` -- which is how the command is actually
    # written (`cd lessons/lesson-04 && python build.py --build`), so the gap
    # cannot exclude the shell separators.
    (r"(?s)\blessons/lesson-0[1-9]\b.*(--build|--pdf-only|--audio-only|--only)"
     r"|(--build|--pdf-only|--audio-only|--only).*\blessons/lesson-0[1-9]\b",
     SHIPPED + " Rebuilding one rewrites every PDF and MP3 in it with fresh "
     "timestamps, for no change in content."),
    (r"\brm\b[^|;&]*\blessons/lesson-0[1-9]\b",
     SHIPPED),
    (r"\brm\b[^|;&]*\btests/test-01\b",
     SHIPPED),
    (r">\s*scripts/build-sw\.py|\b(sed|tee|cp|mv)\b[^|;&]*scripts/build-sw\.py",
     "scripts/build-sw.py is vendored byte-for-byte across the seven sibling "
     "apps on this origin. Course-specific precaching belongs in "
     "sw.config.json. An edit here takes the sibling courses offline."),
    (r"\b(sed|tee|cp|mv|rm)\b[^|;&]*\.claude/autopilot",
     "The lane -- its phase prompts, its gate and this guard -- is not yours "
     "to edit. If the gate is wrong, say so in your closing message and stop."),
    (r"\brm\s+(-[a-zA-Z]*\s+)*(-rf|-fr)\b\s*(/|~|\$HOME)\s*(\s|$)",
     "Refusing a recursive delete of a home or root path."),
    (r"\bsudo\b",
     "Nothing in this build needs root. The venv at .venv already has "
     "edge-tts, weasyprint and markdown. If you believe root is needed, write "
     "docs/LESSONS-10-12-BLOCKED.md and stop."),
    (r"\b(shutdown|reboot|systemctl\s+(stop|restart|disable))\b",
     "Do not touch services on this machine."),
    (r"\bcurl\b[^|;&]*(\s-[a-zA-Z]*o\b|--output\b|>)|\bwget\b",
     "Do not download anything. The lessons are written here, not fetched, "
     "and nothing in this course may depend on a file that came from a URL. "
     "edge-tts reaching Microsoft's voice endpoint is the only network call "
     "this build makes."),
    (r"\bnpm\s+(publish|login|adduser)\b", "No."),
    (r"\brm\s+-[a-zA-Z]*\s*\.audio-cache|\brm\s+-[a-zA-Z]*r[a-zA-Z]*\s+\.audio-cache",
     "The audio cache is every spoken segment of twelve lessons, keyed by its "
     "text. Deleting it costs an hour of synthesis to get back exactly what "
     "was there."),
]

# Written by build.py inside a lesson folder, or by a generator at the root.
GENERATED_RE = (
    re.compile(r"lessons/[^/]+/\d\d-[^/]+\.(pdf|mp3|html)$"),
    re.compile(r"lessons/[^/]+/00-(lesson\.pdf|full-section\.mp3)$"),
    re.compile(r"lessons/[^/]+/README\.md$"),
    re.compile(r"tests/[^/]+/\d\d-[^/]+\.(pdf|mp3|html)$"),
)
GENERATED_FILES = ("app/catalog.json", "sw.js")

# Shared by every lesson, or part of the app shell. Adding three lessons needs
# none of them: the app's lesson list comes from the generated catalogue.
SHARED_FILES = ("lesson.css", "app/app.js", "app/app.css", "index.html",
                "manifest.webmanifest", "sw.config.json", "make_catalog.py",
                "playwright.config.js", "package.json", "requirements.txt")


def norm(path):
    return path.replace("\\", "/").lstrip("./")


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        json.dump(ALLOW, sys.stdout)       # fail open on a malformed payload
        return

    tool = payload.get("tool_name") or payload.get("toolName") or ""
    args = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(args, dict):
        json.dump(ALLOW, sys.stdout)
        return

    if tool == "Bash":
        cmd = str(args.get("command", ""))
        for pattern, reason in BASH_RULES:
            if re.search(pattern, cmd):
                deny(reason)
        # A build must name the lesson it is building, in the same command.
        # The guard cannot see the working directory, so `cd lessons/lesson-04`
        # in one call and `python build.py --build` in the next would otherwise
        # rebuild a shipped lesson with nothing to stop it. The phase prompts
        # already write it as one command.
        if re.search(r"build\.py\b.*(--build|--pdf-only|--audio-only|--only)",
                     cmd, re.S) and not re.search(r"lesson-1[0-2]|test-02", cmd):
            deny("Name what you are building in the same command, so this "
                 "hook can see which one it is: `cd lessons/lesson-10 && "
                 "python build.py --build`, or `cd tests/test-02 && ...`. Nine "
                 "lessons and one test are finished and built, and a rebuild "
                 "of any of them rewrites files she has already downloaded.")

    if tool in ("Write", "Edit", "NotebookEdit"):
        raw = str(args.get("file_path") or args.get("path") or "")
        path = norm(raw)
        if path:
            if re.search(r"(^|/)\.claude/", path + "/"):
                deny("The lane -- phase prompts, gate, guard -- is not yours "
                     "to edit. If the gate is wrong, say so in your closing "
                     "message and stop.")
            if re.search(r"(^|/)lessons/lesson-0[1-9]/", "/" + path):
                deny(SHIPPED)
            # Progress Test 1 is finished and sat. Progress Test 2 is being
            # written, so tests/test-02 is the one place under tests/ that is
            # open -- and only its source, never what build.py writes.
            if re.search(r"(^|/)tests/test-01/", "/" + path):
                deny(SHIPPED)
            for rx in GENERATED_RE:
                if rx.search(path):
                    deny(GENERATED % path)
            for f in GENERATED_FILES:
                if path == f or path.endswith("/" + f):
                    deny("%s is generated: make_catalog.py writes the "
                         "catalogue and scripts/build-sw.py writes the worker. "
                         "Run them; do not edit their output." % path)
            if re.search(r"(^|/)build\.py$", path):
                deny("build.py is byte-identical in every lesson and test "
                     "folder, and holds no lesson text at all. A new lesson "
                     "copies it unchanged. If a lesson needs something build.py "
                     "cannot do, write docs/LESSONS-10-12-BLOCKED.md and stop.")
            if path.endswith("scripts/build-sw.py"):
                deny("scripts/build-sw.py is vendored byte-for-byte across "
                     "seven sibling apps on this origin. Course-specific "
                     "precaching belongs in sw.config.json.")
            for f in SHARED_FILES:
                if path == f:
                    deny("%s is shared by the whole course and by nine shipped "
                         "lessons. Adding three lessons does not need it: the "
                         "app's lesson list comes from the generated "
                         "catalogue. If you are certain it does, write "
                         "docs/LESSONS-10-12-BLOCKED.md and stop." % path)
            # The repository README is the course's front page, and the last
            # phase rewrites its tables once, with all three lessons in hand.
            if path == "README.md" and os.environ.get("ESL_PHASE") not in ("6", "8"):
                deny("README.md is rewritten once, by the last phase, when all "
                     "three lessons exist and their real word counts and sizes "
                     "are known. Put what you want it to say in "
                     "docs/LESSONS-10-12-PROGRESS.md instead.")

            # Nothing outside the repository, and nothing outside the sandbox.
            repo = os.environ.get("CLAUDE_PROJECT_DIR", "")
            if repo and os.path.isabs(raw):
                try:
                    inside = os.path.commonpath(
                        [os.path.realpath(raw), os.path.realpath(repo)]
                    ) == os.path.realpath(repo)
                except ValueError:
                    inside = False
                if not inside and not raw.startswith(("/tmp/", "/var/tmp/")):
                    deny("Writes are confined to this repository (and /tmp for "
                         "scratch). %s is outside it." % raw)

    json.dump(ALLOW, sys.stdout)


if __name__ == "__main__":
    main()
