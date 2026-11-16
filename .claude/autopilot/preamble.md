# Read this before anything else

You are writing **Lessons 10, 11 and 12 of an English course** in
`~/work/shams/esl`, one phase at a time, each phase starting from a clean
context. Raed is watching this run and will read what you produce, but he is
not answering questions inside a phase. Work carefully: a lesson that looks
finished and is wrong is worse than an honest stop.

The course is private teaching material written for **one student** — a
postgraduate at the University College of Applied Sciences in Gaza, applying to
an exchange programme in Spain that asks for CEFR B2. She studies on a phone,
on an unreliable connection, with the power on for part of the day. That is not
background colour. It is why every part is a separate small file, why the build
reports the size of everything it writes, and why nothing may grow without a
reason.

Nine lessons are finished, built and already on her phone. You are adding
three.

## Read first, in this order

1. `docs/LESSONS-10-12-BRIEF.md` — **what you are building**, lesson by lesson:
   the grammar, the passage, the vocabulary anchors, the writing task. This is
   your specification. Read all of it before you write a line.
2. `README.md` — the course's own account of itself: the four rules, the
   grammar spiral, the question set, why the length stopped climbing at Lesson
   6. It is the contract the three new lessons have to satisfy.
3. `python scripts/course_state.py` — every word she has met, the grammar she
   has had, and the five words your lesson owes back. Read out of the lessons
   themselves, so it cannot disagree with the course.
4. `lessons/lesson-08/lesson.json` — the twelve-part shape your lesson copies,
   end to end. `lessons/lesson-09/lesson.json` is the most recent and the
   best-written, but it has thirteen parts; yours has twelve.
5. `docs/LESSONS-10-12-PROGRESS.md` — what earlier phases actually did. **If it
   exists, read it before you start.** It is the state of the world and it is
   more reliable than your guess about what is finished. If it does not exist,
   you are the first phase.

## The environment

- Python is `~/work/shams/esl/.venv/bin/python` and has **edge-tts,
  weasyprint and markdown**. The system `python3` has none of them. Put
  `~/work/shams/esl/.venv/bin` on `PATH` first, which also gives you a working
  `python`, which `playwright.config.js` shells out to.
- Each lesson folder holds its own `build.py`, byte-identical everywhere:

      cd lessons/lesson-10
      python build.py --check     # validates lesson.json, icons, games, env
      python build.py --plan      # what it would write, with sizes, no writing
      python build.py --build     # sheets, audio, games, README

  `--only 01 04` builds selected parts, `--pdf-only` skips the audio,
  `--audio-only` skips the sheets.
- Then, from the repository root: `python make_catalog.py` and
  `python scripts/build-sw.py`.
- Every spoken segment is cached by its text in `.audio-cache/` at the root,
  shared by all lessons and never committed. A dropped connection costs only
  the segments that had not finished; run the same command again and it carries
  on.
- `npx playwright test` runs the shared service-worker suite. Chromium is
  already cached.
- A full lesson is about 210 spoken segments and 18 MB. Building one takes real
  minutes. Do not start a build you are not going to wait for.

## Standing rules — hard

- **Never push.** Commit locally on `main`. Raed reviews and pushes. The remote
  is read-only as far as this run is concerned.
- **Never touch Lessons 1 to 9 or Progress Test 1.** Their `lesson.json`, their
  PDFs, their MP3s, their `README.md`: all finished, all committed, all on her
  phone. Do not rebuild them either — a rebuild rewrites fifty files with fresh
  timestamps for no change in content. The gate compares against the commit the
  run started from and fails if anything under `lessons/lesson-0*/` or `tests/`
  has moved.
- **Never edit a generated file.** Everything `build.py` writes — every
  `NN-*.pdf`, `NN-*.mp3`, `NN-*.html`, the lesson's own `README.md` — plus
  `app/catalog.json` and `sw.js`. Edit `lesson.json` and rebuild. A hand-edited
  PDF is destroyed by the next build and nothing reports it.
- **Never edit `build.py`.** It is byte-identical in every lesson and test
  folder and holds no lesson text at all. A new lesson copies it unchanged.
- **Never edit `scripts/build-sw.py`.** It is vendored byte-for-byte across the
  seven sibling apps on this origin. Course-specific settings live in
  `sw.config.json`, which is data.
- **Never widen the cache prefix past `esl-`,** and never touch
  `esl-content-v1`. Cache Storage is scoped to the origin, not the path: a
  worker that deletes caches it does not recognise takes the six sibling
  courses offline, and `esl-content-v1` holds the files she paid data for.
- **One network request at run time, and only the one.** The games open from a
  phone with no connection, so no CDN, no web font, nothing a lesson needs in
  order to work. The single exception arrived upstream on 16 Nov 2026 and is
  deliberate: every generated puzzle page carries a Cloudflare Web Analytics
  loader, written by `_game_page` in `build.py`, which fires only on
  `shamsfelfel.github.io` and only outside an iframe. **Do not remove it, do
  not add a second one, and do not report it as a fault** -- it is counted, and
  the gate checks that each new game page carries exactly one. `edge-tts`
  reaching Microsoft's voice endpoint at build time is the only other network
  call anything here makes.
- **Nothing in a lesson is borrowed from the real world.** These three passages
  are written stories: no real organisation, no real figure, no real link, no
  date lifted from reporting. Lesson 9 is the one lesson built on real
  reporting and it carries a whole session tracing its figures to their
  sources; you are not writing that session, so you are not writing those
  figures either. An invented statistic with a real-sounding source in a
  teaching passage is the one mistake in this run that could actually harm
  somebody.
- **Nothing the student sees identifies which AI model produced it.** Not in a
  sheet, not in a game, not in a comment in `lesson.json`. Commit messages are
  the exception, and they are not hers: this repository's history ends every
  message with a `Co-Authored-By:` trailer, and yours does too. Copy the exact
  line from `git log`.

## Things that have actually gone wrong on this course

- **The word count is printed in three places** — `passage_words`, the passage
  heading `### Passage: *Title* (520 words)`, and often a sentence in the
  review or the answer key. Change the passage and all three have to move. The
  gate counts the words itself and fails if they disagree.
- **Numbers in prose do not regenerate; numbers in output blocks do.** The same
  trap in a different repository cost four stale figures in one lesson. Here it
  is word counts, part numbers, minute totals and "ten questions" claims. If
  you change one, sweep the prose for it.
- **An invented icon name is a game that comes out short.** `icons.json` has 40
  drawings and a vocabulary entry asks for one by name. `build.py --check`
  reports a name that is not there — but only if you run it before you build.
- **Author against a finished dependency, never a guessed one.** Lesson 12
  recalls five of Lesson 10's fourteen words. Take them from Lesson 10's
  committed `lesson.json`, not from the brief's anchor list, which is eight
  suggestions and not the final fourteen.
- **A word taught twice breaks the spacing rule.** 124 key words are already
  spoken for across nine lessons, with no collisions. Check
  `python scripts/course_state.py --words` before you settle a vocabulary list.

## Autonomy rules — these replace "stop and ask"

1. On a genuine ambiguity, pick **the option most faithful to the brief and to
   what the first nine lessons already do**, then record it in
   `docs/LESSONS-10-12-PROGRESS.md`: the question, what you chose, why, and the
   alternative. Then carry on.
2. If you genuinely cannot continue — the brief and the repository contradict
   each other on something load-bearing, or a decision is Raed's to make —
   write `docs/LESSONS-10-12-BLOCKED.md` saying exactly what is needed and what
   you already tried, commit it, and stop. A clean stop is a good outcome. A
   guess that corrupts the next two lessons is not.
3. **Nothing irreversible outside this repository.** No pushes, no deleting
   anyone's work, nothing outside `~/work/shams/esl`.

## Definition of done for every phase

1. The commands your phase ran, with their **real** output pasted — not
   described, not summarised, not predicted.
2. A section appended to `docs/LESSONS-10-12-PROGRESS.md`, headed
   `## Phase N — <name>`, covering: what you built, the files you touched, what
   you verified and how, anything you deferred, and every decision you made
   under autonomy rule 1. The next phase starts from a clean context and this
   file is all it knows.
3. Committed on `main`, with a real message in the house style — a sentence
   that says what changed and why. Read `git log` for the voice: "Add Lesson 5,
   which completes the question set", "Spiral the grammar through Lessons 1
   to 4", "Stop make_catalog.py leaving __pycache__ in lesson folders". Never
   "Phase 3". **Do not push.**
4. End your final message with a line that is exactly `PHASE_COMPLETE` if every
   acceptance criterion in the phase is met, or exactly `PHASE_INCOMPLETE` if
   it is not. That line is read by a script. Do not write it unless it is true:
   an independent gate runs after you — it validates every lesson, counts the
   words in the passage, counts the questions and their types, checks the
   recall against the lesson two back, checks no key word is taught twice,
   demands every file the lesson promises, weighs the folder, and drives the
   app in a browser. It will catch a false claim.

---
