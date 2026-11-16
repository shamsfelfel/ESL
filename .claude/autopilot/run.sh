#!/usr/bin/env bash
# Phase runner for the Lessons 10-12 build.
#
#   .claude/autopilot/run.sh [first] [last]      default: 0 6
#
# One headless claude session per phase, each starting from a clean context and
# re-reading docs/LESSONS-10-12-PROGRESS.md for state. That is deliberate: seven
# phases in one session would spend the run compacting, and a lesson written by
# an agent that has forgotten the brief is worse than one written from scratch.
#
# The phases alternate on purpose -- write a lesson, then build it in a fresh
# context. The second agent did not write what it is reading, which is how a
# stale word count gets caught instead of shipped.
#
# After each phase an INDEPENDENT gate (verify.sh) validates every lesson,
# counts the words in the passage, counts the questions and their types, checks
# the recall against the lesson two back, demands every file the lesson promises
# and drives the app in a browser. The agent's own PHASE_COMPLETE claim is
# necessary but not sufficient - the gate decides whether the run advances.
set -uo pipefail

export PATH="$HOME/.local/bin:$PATH"
REPO="${REPO:-$HOME/work/shams/esl}"
AP="$REPO/.claude/autopilot"
STATE="${STATE:-$AP/state}"
LOGS="${LOGS:-$AP/logs}"
# Which preamble to prepend. One pack here, so this is only ever the default;
# it stays an env var because run.sh is shared machinery, not this lane.
PREAMBLE="${PREAMBLE:-$AP/preamble.md}"
FIRST="${1:-0}"
LAST="${2:-6}"

# A build phase synthesises about 210 spoken segments and renders twelve sheets,
# so an hour is normal. Beyond two and a half, something is wrong.
PHASE_TIMEOUT="${PHASE_TIMEOUT:-9000}"
# Usage limits reset on a rolling window; wait rather than burn the night failing.
RATELIMIT_SLEEP="${RATELIMIT_SLEEP:-1800}"
MAX_RATELIMIT_WAITS="${MAX_RATELIMIT_WAITS:-8}"

mkdir -p "$STATE" "$LOGS"
cd "$REPO" || { echo "no repo at $REPO"; exit 90; }

HEARTBEAT="$STATE/HEARTBEAT.md"
say() { printf '%s  %s\n' "$(date '+%F %T')" "$*" | tee -a "$STATE/run.log"; }
beat() { { echo "# autopilot heartbeat"; echo; echo "updated: $(date '+%F %T %Z')"; echo;
           cat "$STATE/run.log" 2>/dev/null | tail -40; } > "$HEARTBEAT"; }

say "=== autopilot starting: phases $FIRST..$LAST ==="
say "repo $REPO on branch $(git rev-parse --abbrev-ref HEAD)"
say "claude $(claude --version 2>&1 | head -1)"

for n in $(seq "$FIRST" "$LAST"); do
  nn=$(printf '%02d' "$n")
  phase_file="$AP/phases/$nn.md"
  [ -f "$phase_file" ] || { say "phase $nn: no prompt file, stopping"; break; }

  if [ -f "$STATE/$nn.done" ]; then
    say "phase $nn: already done, skipping"
    continue
  fi

  # ---- build the prompt -----------------------------------------------------
  prompt_file="$STATE/$nn.prompt.md"
  {
    cat "$PREAMBLE"
    echo
    cat "$phase_file"
    echo
    echo "---"
    echo
    cat "$AP/phases/standing-rules.md"
  } > "$prompt_file"

  say "phase $nn: starting ($(wc -c <"$prompt_file") char prompt)"
  beat

  # ---- run it, retrying only on usage limits --------------------------------
  waits=0
  while :; do
    log="$LOGS/phase-$nn.jsonl"
    # Per-phase model, from $AP/models ("<phase> <model>" per line). Absent means
    # the CLI default. A cheap phase on a cheap model is not merely cheaper: it is
    # far less likely to exhaust the 5-hour window and stall everything behind it.
    model=$(awk -v p="$n" '$1==p {print $2}' "$AP/models" 2>/dev/null | head -1)
    effort=$(awk -v p="$n" '$1==p && $3 !~ /^#/ {print $3}' "$AP/models" 2>/dev/null | head -1)
    model_arg=()
    effort_arg=()
    if [ -n "$model" ]; then model_arg=(--model "$model"); say "phase $nn: model $model"; fi
    if [ -n "$effort" ]; then effort_arg=(--effort "$effort"); say "phase $nn: effort $effort"; fi
    # The guard reads this: only the last phase may edit the repository README,
    # which is rewritten once with all three lessons' real figures in hand.
    export ESL_PHASE="$n"
    timeout "$PHASE_TIMEOUT" claude -p "$(cat "$prompt_file")" \
        --output-format stream-json --verbose \
        --dangerously-skip-permissions \
        "${model_arg[@]}" "${effort_arg[@]}" \
        >"$log" 2>"$LOGS/phase-$nn.stderr"
    rc=$?

    # Pull the final result message out of the stream.
    result="$(python3 - "$log" <<'PY'
import json, sys
last = ""
try:
    for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "result":
            last = str(o.get("result", ""))
except FileNotFoundError:
    pass
print(last)
PY
)"

    if [ $rc -eq 124 ]; then
      say "phase $nn: TIMED OUT after ${PHASE_TIMEOUT}s"
      break
    fi

    if printf '%s' "$result" | grep -qiE 'usage limit|session limit|rate limit|quota|resets at|resets [0-9]|too many requests'; then
      waits=$((waits + 1))
      if [ "$waits" -gt "$MAX_RATELIMIT_WAITS" ]; then
        say "phase $nn: still rate-limited after $MAX_RATELIMIT_WAITS waits, stopping"
        rc=99
        break
      fi
      say "phase $nn: usage limit hit, sleeping ${RATELIMIT_SLEEP}s (wait $waits/$MAX_RATELIMIT_WAITS)"
      beat
      sleep "$RATELIMIT_SLEEP"
      continue
    fi
    break
  done

  claimed=no
  printf '%s' "$result" | grep -q 'PHASE_COMPLETE' && claimed=yes
  say "phase $nn: agent exited rc=$rc, claims complete=$claimed"

  # ---- independent gate -----------------------------------------------------
  gate_log="$LOGS/verify-$nn.log"
  bash "$AP/verify.sh" "$n" >"$gate_log" 2>&1
  gate=$?
  sed 's/^/    /' "$gate_log" | tail -30 | tee -a "$STATE/run.log"

  if [ "$gate" -ne 0 ] || [ "$claimed" != yes ]; then
    say "phase $nn: NOT VERIFIED (gate=$gate, claimed=$claimed) - stopping the run"
    {
      echo "# Autopilot stopped at phase $nn"
      echo
      echo "- time: $(date '+%F %T %Z')"
      echo "- agent exit code: $rc"
      echo "- agent claimed complete: $claimed"
      echo "- independent gate: $([ $gate -eq 0 ] && echo passed || echo FAILED)"
      echo
      echo "## Gate output"; echo; echo '```'; cat "$gate_log"; echo '```'
      echo
      echo "## Agent's closing message"; echo; echo '```'; printf '%s\n' "$result"; echo '```'
      echo
      echo "Full transcript: \`$log\`"
      echo "Resume with: \`.claude/autopilot/run.sh $n $LAST\`"
    } > "$STATE/STOPPED.md"
    beat
    exit 1
  fi

  touch "$STATE/$nn.done"
  say "phase $nn: VERIFIED"

  beat
done

say "=== autopilot finished: phases $FIRST..$LAST ==="
{
  echo "# Autopilot run finished"
  echo
  echo "- finished: $(date '+%F %T %Z')"
  echo "- phases completed: $(ls "$STATE"/*.done 2>/dev/null | wc -l)"
  echo
  echo "## Commits made"; echo; git log --oneline "$(cat "$AP/baseline")"..HEAD 2>/dev/null | head -30
  echo
  echo "## Run log"; echo; echo '```'; cat "$STATE/run.log"; echo '```'
} > "$STATE/FINISHED.md"
beat
