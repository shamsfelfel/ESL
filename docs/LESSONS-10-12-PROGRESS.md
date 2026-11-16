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

## Phase 01 — Build Lesson 10 and read what came out

### What was built

`python build.py --build` in `lessons/lesson-10` (665 s, exit 0): 11 sheets
plus `00-lesson.pdf`, 9 part MP3s plus `00-full-section.mp3`, five games
(13–17) and the lesson's generated `README.md`. 30 files, 18.1 MB by the
build's own count (`du -sb` 18,999,658 bytes); the check script reports
19.0 MB, under its ceiling. `make_catalog.py` and `scripts/build-sw.py` ran
clean (sw: 10 entries, cache `esl-b68aac1ea4cd`); the catalogue lists
`lesson-10`, 12 parts, 17.9 MB. `npx playwright test`: 22 passed.
`check_lessons.py --built`: passes (L10 passage 520 words, ten questions
eight types, folder 19.0 MB).

### Audit of `lesson.json` against the brief — changes made

1. **Part 04 §3.3, example for *just*** contradicted the story: *The copy had
   just finished when the disk stopped* (the copy finished at 01:10, the disk
   stopped next morning). Now *She had just sat down when the screen froze.*
2. **Stray asterisks in the PDFs** (found by reading the render, not by
   `--check`). Nested emphasis the Markdown renderer mis-parses printed
   literal `*` in 04 and 11 (and so in `00-lesson.pdf`): the *by the time*
   example, three participle-table rows (*had sent, had never done, had
   existed*) and the `*Why N is **X***:` lead-ins in the answer key (10 of
   them). Rewritten without nesting; rebuilt with `--pdf-only`; every PDF
   then grepped clean of `*`.

Verified and found sound: passage is 520 words by my own count, equal to
`passage_words` and the heading; all 14 key words and all 5 recalled words
occur in the passage; part 04 opens with the come-back and teaches the trap in
3.4; the past perfect is in the passage before part 04 names it; part 06 has
ten questions in the eight types with each distractor named in the key.

### What I looked at

PDFs: 03 vocabulary p1 (Arabic reads correctly, right-to-left, not reversed),
04 grammar p2, 06 comprehension p1 (no question split across a page; footer
carries "Lesson 10 — An Hour Too Late · page n of N"); 11 answer key and 04
checked as text. Games, rendered in headless Chromium at 420 px: crossword
(19 words, clues in order), word search (all 19 listed, grid built), memory (24
cards, 6 drawings in the source), criss-cross and cryptogram (14 key words
each, by design). No page error and no non-file request. Audio: pauses are
10 s in part 02, 8 s (12 s for insertion) in 06, 7 s in 07, 45 s in 08 —
all well over five seconds.

### Notes

- `make_catalog.py` moved the byte figures of lessons 1–9 (Linux vs the
  Windows working copy's CRLF), as predicted; left as is. No file under
  `lessons/lesson-0*` or `tests/` changed.
- `app/catalog.json` and `sw.js` were already modified in the working tree
  when this phase began; they were regenerated here.
- Games 16 and 17 use the 14 key words, not the 19; crossword, word search
  and memory use 19.

### Deferred

Nothing.

## Phase 02 — Write Lesson 11, *The Message That Changed Twice*

### What was built

- `lessons/lesson-11/lesson.json` — 12 parts, 5 games (13–17), 14 key words,
  5 recalled from Lesson 9, ten comprehension questions in Lesson 8's order.
- `lessons/lesson-11/build.py` — `cp` of `lessons/lesson-10/build.py`, md5
  `dcc39c1fe972293dce23d2296f5772da` for both.
- This section.

**Nothing was built.** `lessons/lesson-11/` holds only `lesson.json` and
`build.py`. No change to `icons.json`, `app/catalog.json`, `sw.js`, the
repository `README.md`, or anything under `lessons/lesson-0*` or `tests/`.

### The lesson, in brief

| | |
|---|---|
| Passage | *The Message That Changed Twice*, **525 words**: the gate's counter, `passage_words` and the heading all say 525. The teacher notes in part 11 also quote it, interpolated from the same count |
| Grammar (04) | `grammar-reported-speech`. Come back to (L9 passive) → the reporting passive (*it is said that*, *is said to*, *was said to have*). The link is stated outright: reported speech names the source and the reporting passive deletes it, tied by name to Lesson 9 part 06, 4.3 (*has anybody checked it…*). Then 3.1 direct vs reported → 3.2 *say/tell* → 3.3 backshift, with the past perfect credited to Lesson 10 → 3.4 time, place and person → 3.5 reported questions, *if/whether* → 3.6 *told me to / asked me not to* → 3.7 the trap (still-true present; dropped *that*), with a ✗/✓ table → 3.8 practice A–F |
| Pronunciation (05) | `said-told-and-that`, section 3.9: quick *said* with stress on the claim; *said/says* minimal pairs; *told her/told him* pairs (*told'er*); *that* with and without; contrastive stress (*she SAID it had moved*) on the sheet only. Two tests: 6 *said/says*, 4 *her/him*, answers spoken and in the key |
| Key words | rumour, claim, deny, admit, announce, forward, screenshot, official (the brief's eight) + trace, original, crop, applicant, notice, extend |
| Recall (L9) | severe, estimate, verify, source, headline. Meanings and icons copied from Lesson 9's `lesson.json` by the generator. All five are in the passage |
| Drawings | rumour→`warning`, screenshot→`browser`, applicant→`person`, notice→`notebook`, extend→`calendar`, headline (recall)→`newspaper`: 6, the memory game's minimum |
| Answers Q1–10 | A B D B C B C D A C |
| `full_section` | 01, 02, 06, 07 |

Reported speech in the passage before part 04 names it: *somebody asked
whether…*, *somebody else said that it probably was*, *she asked the group who
had sent it first*, *admitted that he did not know*, *told her that a friend had
sent it*, *the friend said she had found it*, *denied that anyone had written*,
*it said that applications close… and that the deadline would not be extended*
(the still-true present that 3.7 points back to), *asked everyone not to
forward*. The reporting passive is in it once, at the turn: *the date was said
to have moved, and nobody could trace who had said so*.

The story: a screenshot of a screenshot reaches Lina's group of forty
with the headline *deadline extended to the fifteenth* and *they said the office
announced it this afternoon*. It had been cropped, so it has no name and no
time. Her cousin, his friend and the 300-applicant group's admin each pass it
back. The official notice says midnight on the fourteenth, will not be
extended, and is six weeks old. The original in the large group was right; one
person misread *midnight on the fourteenth* and another added *extended*. Second
movement: two minutes and one page; forwarding feels like helping; the first
person was useful, and was. Closing line: *A message does not need a liar to
become false. It needs only enough kind people, and nobody who checks.*

### Verified, and how (real output)

`python build.py --check` in `lessons/lesson-11`, exit 0:

```
Lesson
  file         : lesson.json - valid
  title        : Lesson 11 — The Message That Changed Twice
  parts        : 12 (11 with a sheet, 9 with audio)
  games        : 5 (crossword, word-search, memory, criss-cross, cryptogram)
  words        : 19 for the games, 6 of them with a drawing

Ready. Run:  python build.py --plan
```

`python build.py --plan`, tail:

```
  00   whole lesson                      00-lesson.pdf (new)                00-full-section.mp3        17m 04.0s  ~  5.9 MB  parts 01, 02, 06, 07

  9 parts with audio: 36.7 minutes in the numbered parts.
  About 18,184 characters to synthesize; 178 spoken segments are not cached yet.
  Estimated folder size once built: ~18.5 MB.
```

`python .claude/autopilot/check_lessons.py`, exit 0:

```
      L11 passage 525 words (declared 525)
      L11 ten questions, eight types
      structure: every check passed (L10, L11)
```

`python scripts/course_state.py`: `152 distinct key words`, `collisions: none`.

Also checked:
- Every key word and recall word occurs in the spoken passage (an assert in the generator).
- Every sheet rendered with the build's own Markdown settings (`tables`, `attr_list`, `sane_lists`) leaves no literal `*` and no `{:`. This is the stray-asterisk fault phase 01 found in Lesson 10.
- `lesson.json` contains no string naming a model or vendor, and no `http` (grep count 0).

**Calibration for phase 03.** Phase 01 found `--plan` under-estimates by
0.6–0.8 MB (Lesson 10: plan 18.3, `du` 19.0). Expect Lesson 11 at about
19.1–19.3 MB by `du`, under the gate's 20.5 MB. If that is too close to "about
19 MB", the first place to save is part 05's two *with that / without that*
blocks, then the 3 s gaps in part 03.

### Decisions made under autonomy rule 1

1. **The university has no name.** I invented a name, then searched the web for
   it. "Velmora University" turned up an English-diploma institute called
   *Velmora International Campus*. A second invention, "Arvendale", reads as a
   misspelling of the real Avondale University. In a passage about checking
   claims, a name that might belong to somebody real is the one mistake the
   brief warns about. *Chose:* "the exchange scholarship at a university
   abroad". It is plainly invented, and the teacher notes say the university is
   unnamed on purpose. *Alternative:* keep searching for a name with no hits.
   Rejected, because "no hits today" is weak proof, and the story needs no
   name.
2. **Only one inference question.** The prompt calls *who said it first* and
   *what the student actually verified* the best inference questions, but
   Lessons 6–10 all have exactly one Inference slot (Q6), and the gate wants
   Lesson 8's order. *Chose:* Q6 asks who said it first; the passage never
   says it in one sentence, so it has to be put together from the paragraphs
   after [C] and [D]. *What she verified* is True/False item 4 (*Lina found out
   who had changed the date* → F, with the key spelling out that she verified
   the date, not the person) and review question 6.1.1. *Alternative:* turn a
   Factual question into an inference. Rejected, because it would break the
   fixed order.
3. **The six extra key words**: trace, original, crop, applicant, notice,
   extend. All checked against `--words`, and none is a Lesson 12 anchor.
   *applicant* is derived from Lesson 8's *apply*. It is a different word
   (the gate's exact-match test passes), it is one she needs for her own
   application, and it reads as the spiral rather than a repeat. *Alternative:*
   *caption*, rejected as less useful to her. *deadline* (L6) and *scholarship*
   (L8) are in the passage as ordinary words, not key words.
4. **Recall**: severe, estimate, verify, source, headline. The prompt asked for
   *estimate*, *verify* and *source*. *headline* fits the story (the
   screenshot's capitals) and brings the one recalled drawing. *severe* is the
   cost to anyone who believed the fifteenth. *flood* was considered for a
   figurative use and rejected, because the recall audio speaks Lesson 9's
   literal meaning (*to cover with water*).
5. **No new icons**, for the same reason as phase 00: the acceptance criterion
   is a `git status` with only the lesson files and this doc. Four of the six
   drawings are close but not exact (*screenshot→browser*, *notice→notebook*,
   *rumour→warning*, *extend→calendar*). If drawings are added later,
   *screenshot* (a phone outline) and *forward* (a curved arrow) would be worth
   the most.
6. **Contrastive stress** (*she SAID it had moved*, meaning it isn't true) is
   on the sheet only, not in the audio. The neural voice cannot be trusted to
   put stress where the text asks, and a track that demonstrates the wrong
   stress is worse than none.
7. **Timing follows Lesson 10 (and so Lesson 9's leaner audio)**: 8 s answer
   gaps in 06 (12 s for insertion), Parts C and D on the sheet only, 5 s think
   time in speaking, two listen-again questions in 10. Part minutes copy Lesson
   10, with 04 at 50 and 05 at 25.
8. **The writing model (09) reports a question with the reporting passive**
   (*it was asked whether…*). It is correct but stiff, and the sheet says so.
   That stiffness is part of the lesson: a question is nearly always reported
   with the person who asked it.
9. **The printed headline** is bold capitals, *DEADLINE EXTENDED TO THE
   FIFTEENTH*. The spoken text has it in sentence case, so the voice does not
   spell out the capitals.

### For the next phases

- **Phase 03 (build Lesson 11):** 178 segments to synthesise, ~18,200
  characters. When reading the render, check part 05's IPA spans and the
  hard line breaks in the quoted examples in part 04 (the Come back to block and
  3.4).
- **Lesson 12's recall** comes from Lesson 10's committed fourteen (see Phase
  00). Lesson 11's words are due back in Lesson 13.
- Lesson 11's teacher notes offer Lesson 12 a link: if the reporting passive is
  deferred, the non-defining clause partners it (*the message, which nobody
  could trace, was said to have come from the office*).
- The self-report keeps the length question ("six lessons now — should Lesson
  12 be longer?") and adds *do you now ask who said it?*
- The lesson was written by a generator script outside the repository. If you
  edit the passage by hand, move the heading, `passage_words` and the teacher
  note's "The passage is 525 words" together.

### Deferred

Nothing in this phase's scope. The build, catalogue and service worker are
phase 03's.

## Phase 03 — Build Lesson 11 and read what came out

### What was built

`python build.py --build` in `lessons/lesson-11` (658 s, exit 0; 178 segments synthesised): 11 sheets plus `00-lesson.pdf`, 9 part MP3s plus `00-full-section.mp3` and `12-passage-slow.mp3`, five games (13–17) and the generated `README.md`. 30 files, 18.4 MB by the build's count; `du -sb` 19,331,573 bytes (check script: 19.3 MB, under the 20.5 MB ceiling). `make_catalog.py` lists `lesson-11  12 parts  18.3 MB`; `build-sw.py` wrote 10 entries, cache `esl-c2ba519fa9d5`. `check_lessons.py --built` passes (L11 passage 525 words declared 525, ten questions eight types, folder 19.3 MB).

### Audit — no changes needed to `lesson.json`

- Passage counted by me: 525 words; heading, `passage_words` agree; inside 500–535.
- **Is anything in it real?** No. Only invented Lina, her cousin, his friend, an admin, and "the exchange scholarship at a university abroad", unnamed on purpose. No organisation, figure (forty, three hundred, six weeks, two minutes are story numbers), link or reporting-derived date.
- 14 key words all in the passage; `course_state.py` reports 152 distinct words, collisions: none. Five recalled words (severe, estimate, verify, source, headline) are all from Lesson 9, in the passage and used in parts 02–11.
- Part 04 opens with the come-back to Lesson 9's passive, says reported speech names the source and the reporting passive deletes it, and credits Lesson 10 for the past perfect.
- Part 06: ten questions in the eight types; the key explains each distractor. Reported speech is in the passage before part 04 names it.

### What I looked at

PDFs rendered to PNG: 01 passage p1 (markers [A]–[C] printed, no stray `*`), 04 grammar p1 (come-back, tables, italics fine), 11 answer key p1. All 12 PDFs grep clean of `*`. Games in headless Chromium at 420 px: all five load with no page error and no non-file request; the crossword shows 19 numbered clues with Arabic glosses the right way round; memory shows 10 pairs, 6 drawings in the source. No grid-fit warning in the build log (the only grep hit was a quiz option, "could not show it"). I did not listen to the MP3s; the pauses are the timings set in phase 02 (8 s, 12 s for insertion), as in Lesson 10.

### Notes

- `npx playwright test` result is in the commit session output; no file under `lessons/lesson-0*` or `tests/` changed.
- Part 05 IPA spans and part 04 line breaks: part 04 p1 checked; part 05 not viewed.

### Deferred

Nothing.

## Phase 04 — Write Lesson 12, *The Room That Keeps the Light*

### What was built

- `lessons/lesson-12/lesson.json`: 12 parts, 5 games (13–17), 14 key words,
  5 recalled from Lesson 10, ten comprehension questions in Lesson 8's order.
- `lessons/lesson-12/build.py`: `cp` of `lessons/lesson-11/build.py`. All three
  new lessons' copies have md5 `6c5578ee6136be9016645a3452d527e8`. **Note:** this
  is not the `dcc39c1f…` recorded in Phases 00 and 02. Commit `23d4e92` (the
  page-view loader) changed `build.py` upstream after those phases, and Lessons
  10 and 11 were rebuilt on the new copy. Lesson 12 copies the current one.
- This section.

**Nothing was built.** `lessons/lesson-12/` holds only `lesson.json` and
`build.py`. No change to `icons.json`, `app/catalog.json`, `sw.js`, the
repository `README.md`, or anything under `lessons/lesson-0*` or `tests/`.

### The lesson, in brief

| | |
|---|---|
| Passage | *The Room That Keeps the Light*, **530 words**. The gate's counter, `passage_words`, the heading and the teacher notes ("The passage is 530 words", interpolated from the same count) all agree |
| Grammar (04) | `grammar-relative-clauses`. Come back to (L10 past perfect) → the past perfect continuous against the simple (*had charged / had been charging*), tied to L5's *have been -ing*, L6's *for/since* and L7's state verbs → 3.1 what a relative clause does, and not repeating the pronoun (the Arabic resumptive *ـه*) → 3.2 defining *who/which/that/whose/where* → 3.3 dropping the object pronoun (three examples from the passage) → 3.4 non-defining: two commas, never *that*, never dropped → 3.5 **the trap**: three defining/non-defining pairs with what each claims, then *Now you*, where she writes both and says what each claims → 3.6 *which* about a whole clause, against *which* = one noun → 3.7 practice A–G |
| Pronunciation (05) | `commas-and-had-been`, section 3.8: no stop in a defining clause; stop, fall and stop in a non-defining one; the same words both ways (*the students (,) who had been waiting (,)*; *my brother (,) who works in Spain (,)*); the stop before a comment-*which*; *she'd been waiting* /ʃid bɪn ˈweɪtɪŋ/; *she'd been waiting / she'd waited / she was waiting*. Two tests: 6 *commas / no commas*, 4 *had been / no had been*. Answers spoken and in the key |
| Key words | corridor, volunteer, borrow, lend, charger, shelf, maintain, arrange (the brief's eight) + rota, slot, lean, loose, reward, adapter |
| Recall (L10) | router, spreadsheet, delay, assume, retrieve. Meanings and icons copied from Lesson 10's `lesson.json` by the generator. All five are in the passage |
| Drawings | volunteer→`person`, charger→`plug`, rota→`notebook`, slot→`calendar`, plus the recalled router→`router` and retrieve→`download`: 6, the memory game's minimum. Abstract and undrawn: maintain, arrange, reward |
| Answers Q1–10 | A C D C B D B C B A |
| `full_section` | 01, 02, 06, 07 |

The five recalled words, and the lines of `lessons/lesson-10/lesson.json`
(as committed) they came from:

```
54:   "word": "retrieve",
76:   "word": "delay",
97:   "word": "spreadsheet",
118:   "word": "router",
126:   "word": "assume",
```

Relative clauses in the passage, before part 04 names them:
- **Defining:** *a pen that nobody has managed to take home*, *the woman who keeps the list*, *a student whose own laptop died*, *everyone who comes twice*, *the socket that only works if you lean on the plug*, *the room where everyone ends up*, *a lecturer whose flat has no power*, *a first-year who comes to charge a phone*, *students who had been waiting since eight*, *those who live closest*, *a list that nobody can read at a glance*.
- **Object pronoun dropped:** *an adapter he borrowed*, *the one everyone is cross with*, *the one thing the room is short of*.
- **Non-defining (four):** *the back wall, where the router sits*; *Karim, whose laptop charges faster*; *Karim, who could take the best slot of all,*; *electricity, which is the one thing the room is short of*.
- **Comment-*which* (two):** *goes last, which is why the final twenty minutes are always his*; *it stopped at eleven, which meant the last hour was on battery* (the brief's own example).
- **Past perfect continuous (two):** *had been waiting since eight*, *had been keeping the list for five months*.

The story: Room 14, at the end of a corridor, opens eight to noon and six to
ten. Reem, a volunteer whose own laptop died, keeps the rota. Socket seven only
works if you lean on the plug, number three is loose, and the back wall by the
router is best. Karim's laptop charges in twenty minutes, so he goes last;
*Nobody arranged that. The list simply made it obvious.* Second movement:
goodwill did not work, because everyone assumed someone else would stand up
first. A list makes the waiting visible. Reem refuses a spreadsheet because it
needs electricity. The cost: she settles every argument, and when the
generator stopped at eleven two students blamed her. The unfairness: the list
rewards whoever is nearest the door at eight. It closes: *Her own name is not on
it. The room keeps the light, and Reem keeps the room.*

### Verified, and how (real output)

`python build.py --check` in `lessons/lesson-12`, exit 0:

```
Lesson
  file         : lesson.json - valid
  title        : Lesson 12 — The Room That Keeps the Light
  parts        : 12 (11 with a sheet, 9 with audio)
  games        : 5 (crossword, word-search, memory, criss-cross, cryptogram)
  words        : 19 for the games, 6 of them with a drawing

Ready. Run:  python build.py --plan
```

`python build.py --plan`, tail:

```
  00   whole lesson                      00-lesson.pdf (new)                00-full-section.mp3        16m 49.5s  ~  5.8 MB  parts 01, 02, 06, 07

  9 parts with audio: 37.9 minutes in the numbered parts.
  About 18,887 characters to synthesize; 171 spoken segments are not cached yet.
  Estimated folder size once built: ~18.8 MB.
```

`md5sum`:

```
6c5578ee6136be9016645a3452d527e8  lessons/lesson-11/build.py
6c5578ee6136be9016645a3452d527e8  lessons/lesson-12/build.py
```

`python .claude/autopilot/check_lessons.py`, exit 0:

```
      L12 passage 530 words (declared 530)
      L12 ten questions, eight types
      structure: every check passed (L10, L11, L12)
```

`python scripts/course_state.py`: `166 distinct key words`, `collisions: none`.

Also checked:
- Every key word and recall word occurs in the spoken passage (an assert in the generator).
- Every sheet rendered with the build's Markdown settings leaves no literal `*`, `{:` or `\_` (count 0). The first draft had eight stray `*` in part 04 from italics wrapped around bold (`*…**clause***`). Those examples are now plain text with the clause in bold. The editor had also stripped the two-space line breaks from the quoted examples; the generator now adds them to consecutive `> ` lines.
- `lesson.json` has no string naming a model or vendor, and no `http` (grep count 0).

**Calibration for phase 05.** `--plan` under-estimated by 0.7 MB on Lesson 10 and
0.8 MB on Lesson 11. Expect Lesson 12 at about 19.5–19.6 MB by `du`, under the
gate's 20.5 MB. The first draft planned ~19.2 MB. Part 05 lost one line from
each of its demonstration blocks and one repeat, and the longest spoken options
in Q2 and Q9 were shortened, which brought it to 18.8 MB. Both tests in part 05
are whole.

### Decisions made under autonomy rule 1

1. **The six extra key words**: rota, slot, lean, loose, reward, adapter. All
   checked against `--words`. *charger* is the brief's anchor and a different
   word from L1's *charge*, as L11's *applicant* is from L8's *apply*. *socket*
   (L6), *generator* (L6), *battery* (L5), *laptop* (L6) and *queue* (L6) appear
   in the passage as ordinary words, not key words. *loose* sits next to L2's
   *lose*, and 2.2 teaches the difference (/luːs/ against /luːz/). I picked
   concrete words where I could, so only three of the fourteen are abstract
   (*maintain, arrange, reward*), as the brief allows.
   *Alternatives considered:* *goodwill* and *fair* (both abstract, which would
   make five) and *printer* (too easy).
2. **Recall**: router, spreadsheet, delay, assume, retrieve. Each one does work
   in the story: the router is why the back wall is best, Reem refuses a
   spreadsheet because it needs power, a late start is a delay to the first
   slot, everyone *assumed* somebody else would stand up, and Reem *retrieves*
   the chargers left under the desks. *retrieve* is used in its Lesson 10
   meaning (*to get something back from a place where it was lost or hard to
   reach*), so the recall audio's meaning fits. *restore* was rejected: its
   Lesson 10 meaning is about files, and the room has no use for it.
3. **No new icons**, as in Phases 00 and 02. Four key words have existing
   drawings that fit (person, plug, notebook for the list, calendar for the
   slot). With router and download from the recall, that makes six. *shelf*,
   *corridor* and *adapter* would draw well if icons are added later.
4. **The university and the place are unnamed.** Phase 02 found that invented
   university names collide with real ones. The room is "Room 14", and the
   people are Reem, Karim, an unnamed lecturer and a first-year. Exercise
   sentences that first named a real town (3.7 F, and a part 05 test sentence)
   now say "by the sea". *Spain* stays in *my brother who works in Spain*,
   because that is her own destination and makes no claim.
5. **The writing task's last sentence.** The brief says "one sentence using
   *which* to comment on the whole of the sentence before it". *Chose:* a sixth
   sentence ending in *, which …* that comments on the whole clause before the
   comma, which is the B2 use part 04 teaches. A *which* cannot reach back past
   a full stop in written English, and 3.6 says so. *Alternative:* a sentence
   starting *Which means…*, which part 04 itself marks as wrong in an essay.
6. **The trap exercise** (3.5 *Now you*) has three sentences. She writes each
   with and without commas, and writes what each version claims. The third,
   *my brother (,) who works in Spain (,)*, is the one where the difference is
   about her own life. It is also spoken both ways in part 05.
7. **Q7 answer is B, not C.** Lessons 10 and 11 both had C for sentence
   insertion. The inserted sentence (*Not everyone, though, needs the whole
   forty minutes.*) fits only after the forty-minute slot is explained and
   before Karim.
8. **Q10 asks about the writer's attitude towards Reem** (answer *respectful*),
   with *sorry for her* as the named trap, as the phase prompt suggests. Q8 asks
   about the goodwill paragraph, which exists to make the argument.
9. **The self-report (6.3 and a new 6.4)** keeps the usual table and adds the
   two questions the next run needs, written so the answers are usable. For
   length: her reading time in minutes, how many words she had to look up, and
   one choice from 530 / 600 / 700 / shorter. For grammar: a table of the
   twelve grammar points, two ticks, and **one sentence she is not sure of**
   for each tick. The teacher notes say to read the sentences before the
   ticks.
10. **Timing follows Lessons 10 and 11**: 8 s answer gaps in 06 (12 s for
    insertion), Parts C and D on the sheet only, 5 s think time in speaking,
    two listen-again questions in 10. Part minutes copy Lesson 11 (04 at 50,
    05 at 25).

### For the next phase

- **Phase 05 (build Lesson 12):** 171 segments to synthesise, ~18,900
  characters. When you read the render, check part 04's two-column tables in
  3.5 (long cells), the bold-only quoted examples in 3.3, 3.4 and 3.6, the IPA
  spans in parts 03 (2.2) and 05, and the Arabic phrase in 3.1. **Listen to
  part 05's first test**, sentences 1–6. It only works if the voice really
  pauses at the commas. If it does not, that is a finding to record, not a
  reason to edit `build.py`.
- The lesson was written by a generator script outside the repository. If you
  edit the passage by hand, move the heading, `passage_words` and the teacher
  note's "The passage is 530 words" together.
- Lesson 11's words are due back in Lesson 13.

### Deferred

Nothing in this phase's scope. The build, catalogue and service worker are
phase 05's.

## Phase 05 — Build Lesson 12, and read what came out

**Audit (no changes to `lesson.json` needed).** Passage 530 words in heading,
`passage_words` and the gate's own count. All five recalled words (router,
spreadsheet, delay, assume, retrieve) are in Lesson 10's committed fourteen.
Part 04 opens with the come-back to the past perfect, then the continuous.
The passage has non-defining clauses before part 04 names them (*where the
router sits*, *Karim, whose…*, *which is why*, *which is the one thing*).
Part 06 has ten questions in eight types. Part 10 asks for reading time, words
looked up, a length choice, and two grammar ticks with one unsure sentence each.

**Build.** The first `--build` hit the background time limit and was stopped
with an empty log; the second run finished from the audio cache (rc=0, 98 s,
30 files, 18.7 MB; `du` 19M). `check_lessons.py --built`: every check passed,
L12 folder 19.6 MB (under 20 MB).

**Seen.** PDFs: passage page 1, part 04 page 2, answer key page 1 (rendered at
low resolution; layout fine, the Arabic phrase in 3.1 renders). Games (from the
build report): crossword 19 words, grid 18x16; word search 19, 13x13; memory 19
words, 10 pairs a round, 6 drawn (the rest are the abstract words, which
*mixed* is for); criss-cross 14, 17x16; cryptogram 14. Nothing reported as not
fitting. Each game page carries exactly one Cloudflare loader.

**Not verified.** I did not listen to the audio, and cannot. For part 05 I read
the segment list: defining sentences are spoken straight through, the
non-defining ones keep their commas in the text sent to the voice, with
explicit pauses between lines. Whether the voice truly stops at each comma and
falls before it is unconfirmed. Raed should listen to the first test in
`05-commas-and-had-been.mp3`. If it does not pause, that is a finding, not a
reason to edit `build.py`.

**Catalogue and worker.** `make_catalog.py` lists lesson-10, lesson-11 and
lesson-12, each 12 parts. `build-sw.py`: 10 entries, cache `esl-b26ef84d7470`.
Playwright was not run in this phase.

**Deferred.** Playwright suite; listening to part 05.
