#!/usr/bin/env bash
# Independent gate for the Lessons 10-12 build.
#
# Run AFTER a phase, by the runner, never by the agent. The agent grades its own
# homework; this does not. Everything here is a fact about the repository,
# checked by a command with an exit code. An agent that claims PHASE_COMPLETE
# with a fifteenth key word, a 600-word passage or a missing MP3 fails here and
# the run stops.
#
#   usage: verify.sh <phase-number>
#
# Env: REPO (the course), VENV (python with edge-tts, weasyprint, markdown),
#      E2E_FROM (first phase at which the browser suite must pass, default 0).
#
# Two things in this repository are NOT treated as failures, and both are
# line endings rather than mistakes. `app/catalog.json` and `sw.js` were last
# generated on Windows, where the generated game HTML carries CRLF; measured
# on Linux the same files are about 0.7% smaller, so a regeneration here moves
# forty byte figures that have nothing to do with the new lessons. The gate
# therefore regenerates both, requires the generators to succeed and to be
# deterministic, and checks the catalogue's CONTENT rather than diffing it.
set -uo pipefail

PHASE="${1:?usage: verify.sh <phase-number>}"
REPO="${REPO:-$HOME/work/shams/esl}"
VENV="${VENV:-$REPO/.venv}"
E2E_FROM="${E2E_FROM:-0}"

export PATH="$VENV/bin:$PATH"
PY="$VENV/bin/python"
cd "$REPO" || exit 90

fails=()
note() { printf '    %s\n' "$*"; }
check() {  # check <name> <command...>
  local name="$1"; shift
  if "$@" >/tmp/esl-verify.$$ 2>&1; then
    note "PASS  $name"
  else
    note "FAIL  $name"
    tail -30 /tmp/esl-verify.$$ | sed 's/^/          /'
    fails+=("$name")
  fi
  rm -f /tmp/esl-verify.$$
}

echo "==> verifying phase $PHASE in $REPO"

# --- every lesson's own data must be valid ------------------------------------
# build.py --check validates lesson.json, every icon name, every game's grid
# and the environment it needs. It is the cheapest real check in the repository
# and it runs on all twelve lessons, not just the new ones: a shared file edited
# by mistake shows up here.
for d in lessons/lesson-*/; do
  if [ -f "$d/lesson.json" ]; then
    if (cd "$d" && "$PY" build.py --check) >/tmp/esl-chk.$$ 2>&1; then
      note "PASS  build.py --check in $d"
    else
      note "FAIL  build.py --check in $d"
      tail -25 /tmp/esl-chk.$$ | sed 's/^/          /'
      fails+=("build.py --check $d")
    fi
    rm -f /tmp/esl-chk.$$
  fi
done

# build.py is byte-identical in every lesson and test folder, by design: a new
# lesson is made by copying a folder and editing the JSON. An edited copy is how
# two lessons quietly stop building the same way.
ref="$(md5sum lessons/lesson-09/build.py | cut -d' ' -f1)"
odd=""
for f in lessons/*/build.py tests/*/build.py; do
  [ -f "$f" ] || continue
  [ "$(md5sum "$f" | cut -d' ' -f1)" = "$ref" ] || odd="$odd $f"
done
if [ -n "$odd" ]; then
  note "FAIL  build.py is not byte-identical everywhere:$odd"
  fails+=("build.py copies differ")
else
  note "PASS  build.py byte-identical in every lesson and test folder"
fi

# --- the structural gate ------------------------------------------------------
# Parts, games, fourteen key words, the two-lesson recall, ten questions and
# eight types, and the word count in all three of the places it is printed.
require=()
[ "$PHASE" -ge 6 ] && require=(--require 10 11 12)
if "$PY" .claude/autopilot/check_lessons.py --built "${require[@]}" >/tmp/esl-str.$$ 2>&1; then
  note "PASS  lesson structure"
  sed 's/^/      /' /tmp/esl-str.$$ | tail -20
else
  note "FAIL  lesson structure"
  sed 's/^/      /' /tmp/esl-str.$$ | tail -40
  fails+=("lesson structure")
fi
rm -f /tmp/esl-str.$$

# --- the app's catalogue ------------------------------------------------------
check "make_catalog.py runs" "$PY" make_catalog.py

for n in 10 11 12; do
  if [ -f "lessons/lesson-$n/00-lesson.pdf" ]; then
    if "$PY" - "$n" <<'PY' >/tmp/esl-cat.$$ 2>&1
import json, sys
n = sys.argv[1]
cat = json.load(open("app/catalog.json", encoding="utf-8"))
blob = json.dumps(cat)
if ("lesson-%s" % n) not in blob:
    raise SystemExit("lesson-%s is built but not in app/catalog.json" % n)
PY
    then
      note "PASS  catalogue lists lesson-$n"
    else
      note "FAIL  catalogue does not list lesson-$n"
      sed 's/^/          /' /tmp/esl-cat.$$
      fails+=("catalogue missing lesson-$n")
    fi
    rm -f /tmp/esl-cat.$$
  fi
done

# --- the service worker -------------------------------------------------------
# scripts/build-sw.py is vendored byte-for-byte across the seven sibling apps on
# this origin. An edit here takes the siblings offline, so it is checked rather
# than trusted.
if git diff --quiet HEAD -- scripts/build-sw.py && \
   git diff --cached --quiet HEAD -- scripts/build-sw.py; then
  note "PASS  scripts/build-sw.py unmodified"
else
  note "FAIL  scripts/build-sw.py has been modified — it is vendored across seven apps"
  fails+=("build-sw.py modified")
fi

check "service worker generates" "$PY" scripts/build-sw.py
before="$(md5sum sw.js | cut -d' ' -f1)"
"$PY" scripts/build-sw.py >/dev/null 2>&1
if [ "$(md5sum sw.js | cut -d' ' -f1)" = "$before" ]; then
  note "PASS  sw.js is deterministic"
else
  note "FAIL  sw.js changed on a second identical run"
  fails+=("sw.js not deterministic")
fi

# The worker may only ever delete caches it owns. Cache Storage is scoped to
# the origin, not the path: a greedy activate handler takes the six sibling
# courses offline.
if grep -q 'esl-' sw.js; then
  note "PASS  cache prefix still esl-"
else
  note "FAIL  sw.js no longer mentions the esl- prefix"
  fails+=("cache prefix")
fi

# --- the browser suite --------------------------------------------------------
if [ "$PHASE" -ge "$E2E_FROM" ] && [ -d node_modules/@playwright ]; then
  if timeout 1800 npx playwright test >/tmp/esl-pw1.$$ 2>&1; then
    note "PASS  playwright e2e (service-worker invariants)"
  elif timeout 1800 npx playwright test >/tmp/esl-pw2.$$ 2>&1; then
    note "PASS  playwright e2e (FLAKED once, green on retry)"
    grep -E 'failed|✘' /tmp/esl-pw1.$$ | head -10 | sed 's/^/          flaked: /'
    { date "+%F %T"; grep -E 'failed|✘' /tmp/esl-pw1.$$ | head -20; } \
      >> "$REPO/.claude/autopilot/state/flaky-retries.log"
  else
    note "FAIL  playwright e2e (failed twice — this is real)"
    tail -40 /tmp/esl-pw2.$$ | sed 's/^/          /'
    fails+=("playwright e2e")
  fi
  rm -f /tmp/esl-pw1.$$ /tmp/esl-pw2.$$
else
  note "SKIP  playwright e2e (phase $PHASE < $E2E_FROM, or node_modules absent)"
fi

# --- nothing in this course reaches the network -------------------------------
# The games are opened from a phone with no connection. A CDN or a web font in
# one of them is a game that does not work where it is needed.
if grep -rslE 'https?://(cdn|unpkg|fonts\.googleapis|fonts\.gstatic|ajax\.googleapis|www\.google-analytics)' \
     --include='*.html' --include='*.js' --include='*.css' \
     app index.html lessons tests 2>/dev/null > /tmp/esl-net.$$; then :; fi
if [ -s /tmp/esl-net.$$ ]; then
  note "FAIL  a built page references an external origin:"
  sed 's/^/          /' /tmp/esl-net.$$ | head -10
  fails+=("external origin referenced")
else
  note "PASS  no external origin referenced"
fi
rm -f /tmp/esl-net.$$

# --- repository hygiene -------------------------------------------------------
# The phase must have committed its work: an uncommitted file is work that does
# not survive the next phase. sw.js and app/catalog.json are exempt because the
# gate itself just regenerated them, for the line-ending reason in the header.
loose="$(git status --porcelain 2>/dev/null \
         | grep -vE ' (sw\.js|app/catalog\.json)$' | head -20)"
if [ -n "$loose" ]; then
  note "FAIL  uncommitted changes left behind:"
  printf '%s\n' "$loose" | sed 's/^/          /'
  fails+=("uncommitted changes")
else
  note "PASS  working tree clean (sw.js and catalog.json churn ignored)"
fi

if [ -n "$(git status --porcelain | grep -E '^\?\? .*(__pycache__|\.part)')" ]; then
  note "FAIL  build scratch left in the tree"
  fails+=("build scratch")
fi

# Lessons 1 to 9 are shipped and the student has them on her phone. Nothing in
# this run may change them. The comparison is against the commit the lane
# started from, recorded once in .claude/autopilot/baseline, because a phase
# makes any number of commits and HEAD~n is a guess.
if [ -f .claude/autopilot/baseline ]; then
  base="$(cat .claude/autopilot/baseline)"
  touched="$(git diff --name-only "$base" HEAD 2>/dev/null \
             | grep -E '^(lessons/lesson-0[1-9]|tests)/' | head -5)"
  if [ -n "$touched" ]; then
    note "FAIL  finished work was modified: $(echo "$touched" | tr '\n' ' ')"
    fails+=("finished lesson modified")
  else
    note "PASS  Lessons 1 to 9 and the test are untouched since $base"
  fi
else
  note "FAIL  .claude/autopilot/baseline is missing — cannot prove the shipped lessons are untouched"
  fails+=("baseline missing")
fi

# No phase may push. The remote is read-only as far as this lane is concerned.
if [ -n "$(git log --branches --not --remotes --oneline 2>/dev/null | head -1)" ]; then
  note "PASS  commits are local and unpushed (as required)"
fi

# --- verdict ------------------------------------------------------------------
echo
if [ ${#fails[@]} -eq 0 ]; then
  echo "==> phase $PHASE: GATE PASSED"
  exit 0
fi
echo "==> phase $PHASE: GATE FAILED — ${#fails[@]} check(s): ${fails[*]}"
exit 1
