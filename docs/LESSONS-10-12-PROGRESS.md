# Lessons 10 to 12 — progress

What each phase actually did. The next phase starts from a clean context and
this file is all it knows; read it before `docs/LESSONS-10-12-BRIEF.md`'s
section for your lesson.

## Phase 00 — Write Lesson 10, *An Hour Too Late*

### What was built

- `lessons/lesson-10/lesson.json` — the whole lesson: 12 parts, 5 games
  (13–17), 14 key words, 5 recalled from Lesson 8, ten comprehension questions
  in Lesson 8's order of the eight types.
- `lessons/lesson-10/build.py` — `cp` of `lessons/lesson-09/build.py`,
  md5 `dcc39c1fe972293dce23d2296f5772da` for both.
- This file.

**Nothing was built.** No PDF, MP3, HTML or lesson `README.md` exists in
`lessons/lesson-10/`; that is phase 01's job. `app/catalog.json`, `sw.js`,
`icons.json` and the repository `README.md` were not touched.

### The lesson, in brief

| | |
|---|---|
| Passage | *An Hour Too Late*, **520 words** — the gate's counter, `passage_words` and the heading all say 520 |
| Grammar (04) | `grammar-past-perfect`: Come back to (L8 conditionals) → 3.1 two past actions in order, against the past simple → 3.2 form → 3.3 *by the time, already, just, never … before, when* against *after* → 3.4 the trap (three *hads*), with ✗/✓ sentences both ways → 3.5 table of the passage's 13 participles, 7 irregular marked ✱ → 3.6 the third conditional → 3.7 practice A–E |
| Pronunciation (05) | `had-and-would-have`, section 3.8: weak *had*, minimal pairs *she finished / she'd finished* (×4), strong *hadn't*, *would have → would've → woulda*, whole third conditional with stress; two listen-and-choose tests (6 *had / no had*, 4 *would / would have*), answers spoken and in the key |
| Key words | restore, overwrite, corrupt, retrieve, snapshot, invoice, delay, confirm (the brief's eight) + disk, spreadsheet, receipt, supplier, router, assume |
| Recall (L8) | uplink, latency, neighbour, afford, reliable — every one also appears in the passage |
| Drawings | restore→`refresh`, corrupt→`warning`, retrieve→`download`, router→`router`, uplink→`uplink`, neighbour→`houses` (6, the memory game's minimum) |
| Answer to Q1–10 | B C D B C B C B B B |
| `full_section` | 01, 02, 06, 07 |

The passage's past perfects: *had run, had never once looked, had not heard,
had gone, had assumed, had started, had finished, had begun, had sent, had
existed, had never done, had done, had thought*. Third conditionals, both in
the second movement: *If I had tested it even once, I would have known…* and
*If the copy had run an hour earlier, it would have saved the accounts…*. The
closing line is the brief's: *A backup nobody has ever restored from is not a
backup.*

Written, not reported: the shop, Huda, her uncle, the bakery, the pharmacy and
the times in the log are invented. No organisation, place, figure or link from
the real world.

### Verified, and how (real output)

`python build.py --check` in `lessons/lesson-10` — exit 0:

```
Lesson
  file         : lesson.json - valid
  title        : Lesson 10 — An Hour Too Late
  parts        : 12 (11 with a sheet, 9 with audio)
  games        : 5 (crossword, word-search, memory, criss-cross, cryptogram)
  words        : 19 for the games, 6 of them with a drawing

Ready. Run:  python build.py --plan
```

`python build.py --plan` — tail:

```
  00   whole lesson                      00-lesson.pdf (new)                00-full-section.mp3        16m 34.3s  ~  5.7 MB  parts 01, 02, 06, 07

  9 parts with audio: 36.8 minutes in the numbered parts.
  About 17,473 characters to synthesize; 244 spoken segments are not cached yet.
  Estimated folder size once built: ~18.3 MB.
```

`python .claude/autopilot/check_lessons.py` — exit 0:

```
      L10 passage 520 words (declared 520)
      L10 ten questions, eight types
      structure: every check passed (L10)
```

`python scripts/course_state.py` now reports `138 distinct key words` and
`collisions: none`.

Also checked: every key word and recall word occurs in the spoken passage (an
assert in the generator); the four markers are printed and never spoken
(`--check` enforces it); no string naming a model or vendor in `lesson.json`
(grep count 0).

**Calibration for phase 01.** `--plan` under-estimates a built folder: run
read-only on the shipped lessons it said ~20.7 MB for Lesson 8 (`du -sb`
21.3 MB) and ~18.2 MB for Lesson 9 (`du -sb` 19.0 MB). Expect Lesson 10 to land
at roughly 18.9–19.1 MB by `du`, under the gate's 20.5 MB.

### Decisions made under autonomy rule 1

1. **The size estimate was first ~21.7 MB, over the ~19 MB ceiling.** Silence
   costs the same bytes as speech (48 kbps), and parts 01, 02, 06 and 07 are
   paid for twice because they also make `00-full-section.mp3`. *Chose:* keep
   Lesson 8's printed shape everywhere, but take **Lesson 9's audio timing**
   for parts 06, 07, 08 and 10 — 8-second answer gaps (12 for the insertion
   question), no spoken 90-second summary task (Parts C and D stay on the
   sheet, and the track says so), a 5-second think instead of a 15-second
   prep block in speaking, and the review track carrying only the two
   listen-again questions (the mini-quiz is printed, as in Lesson 9). Part 05
   was **not** cut: it is the part this lesson leans on. Result ~18.3 MB.
   *Alternative:* Lesson 8's timings with a shorter part 05 — rejected, since
   the brief makes 05 the part that most needs its audio.
2. **Where the come-back goes.** The prompt says open part 04 with *Come back
   to*, as Lessons 6–9 do; but the third conditional is built from the past
   perfect, which has not been taught yet at the top of the part. *Chose:* the
   part opens with *Come back to*: a two-line reminder of the first and second
   conditionals, the third conditional shown in one example and named as the
   expansion, and a three-item revision exercise; the full treatment is 3.6,
   after the form, with a table putting all three conditionals side by side
   and a "one form, two jobs" table. *Alternative:* the whole third
   conditional at the top, which would teach *had* + participle before
   explaining it.
3. **No new icons.** The prompt allows two, but the acceptance criterion is a
   `git status` showing only `lesson.json`, `build.py` and this file, and a new
   icon means editing `icons.json`. Six words have existing drawings, which is
   exactly `MEMORY_MIN_ICONS`. *disk*, *invoice*, *receipt* and *spreadsheet*
   would draw well if a later decision adds icons.
4. **The six extra key words** — disk, spreadsheet, receipt, supplier, router,
   assume — were checked against `--words` and also against the brief's
   anchor lists for Lessons 11 and 12, so this lesson does not take a word
   those lessons are meant to teach. For the same reason *deny* (an L11
   anchor) is not used as the opposite of *confirm* in 2.2; *doubt* is.
5. **Recall choice.** Of Lesson 8's fourteen, the five that fit a shop sharing
   a line: *uplink, latency, neighbour, afford, reliable*. Meanings and icons
   copied from Lesson 8's `lesson.json` by the generator, not retyped.
6. **Answer key depth.** Lesson 8 explains questions 7–10 only; the phase
   prompt asks for why each wrong option is wrong. The key explains all ten,
   each distractor named.
7. **Writing (09)** is seven sentences, not Lesson 8's 14–16, because the
   brief sets the task: three in the past simple, the same three with one past
   perfect, one third conditional. Minutes set to 30.
8. **Part 05 minutes** set to 25 (Lesson 8: 20), because it is longer.

### For the next phases

- **Phase 01 (build Lesson 10):** 244 segments to synthesise, ~17,500
  characters. `full_section` is already 01, 02, 06, 07.
- **Lesson 12's recall** must come from the fourteen in
  `lessons/lesson-10/lesson.json` as committed: restore, overwrite, corrupt,
  retrieve, snapshot, invoice, delay, confirm, disk, spreadsheet, receipt,
  supplier, router, assume.
- Lesson 11's self-report should keep the length question; this lesson's says
  "five hundred words for five lessons now — should Lesson 11 be longer?".
- The lesson was written by a generator script kept outside the repository
  (it is not part of the deliverable). If you edit the passage by hand, the
  word count is printed in the heading and in `passage_words`, and the answer
  key's teacher notes also quote it ("The passage is 520 words") — move all
  three.

### Deferred

- Nothing in this phase's scope. The build, catalogue and service worker are
  phase 01's.
