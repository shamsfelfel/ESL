# Lessons 10, 11 and 12 — the brief

Three lessons, written to the shape Lessons 6 to 8 already hold. This file is
the specification; the phase prompts in `.claude/autopilot/phases/` are how to
execute it. Where they disagree, this file wins.

Read `README.md` first — all of it. Then run

    python scripts/course_state.py

which prints, out of the lessons themselves, every word she has met, the
grammar she has had, and the five words each new lesson owes back. Trust it
over your memory of the README.

## What does not change

The course's promise is that only the text gets harder. Nothing in this list
moves in any of the three lessons:

| | |
|---|---|
| Parts | **12**, numbered 01–12, exactly the Lesson 6–8 skeleton below |
| Games | **5**, numbered 13–17: crossword, word-search, memory, criss-cross, cryptogram |
| Comprehension | **10 questions, the 8 fixed TOEFL types**, labelled `**1. (Factual)**` and so on, in the Lesson 8 order |
| Vocabulary | **14 key words** and **5 recalled** from two lessons earlier |
| Passage | **500–535 words.** Not one word over 540 |
| Skills line | `Listening → Reading → Vocabulary → Grammar → Comprehension → Speaking → Writing` |
| Voices | `en-GB-RyanNeural` reader, `en-GB-SoniaNeural` narrator, the slow reader at −25% |

The 12 parts, by slug:

    01-passage   02-listening-questions   03-vocabulary   04-grammar-<topic>
    05-<pronunciation>   06-comprehension   07-true-false   08-speaking
    09-writing   10-review   11-answer-key   12-passage-slow

**There is no "news behind the passage" session in any of these three.** That
session is part 06 of Lesson 9 because its passage rests on real reporting, and
the README makes it conditional on exactly that: *whenever a passage rests on
real reporting*. These three passages are written stories with no borrowed
figures, so the session does not apply, and Lesson 9's thirteen-part shape is
not the new normal.

**The length does not climb.** 504, 510, 516, 532 is four lessons at one
length, and that was deliberate. These three hold it: 520, 525, 530. Difficulty
rises through the grammar step, denser vocabulary and text that argues rather
than narrates — not through size. A lesson folder that builds to more than
about 20 MB has gone wrong somewhere; Lesson 9 is 17.9 MB.

**Progress Test 2 is not in this run.** It covers Lessons 4 to 8 and it is
still owed, but it is not one of these three lessons and nothing here should
create it.

**Lessons 1 to 9 are finished and shipped.** Do not edit their `lesson.json`,
their built files or their `README.md`. The only existing files these phases
touch are the repository `README.md` (last phase only), `app/catalog.json` and
`sw.js` (both generated), and `docs/LESSONS-10-12-PROGRESS.md`.

## The grammar spiral, continued

Every lesson introduces one tense or structure and comes back to one from two
lessons earlier, expanded with something held back the first time. The gap of
two is the pattern from Lesson 6 on, and it is what makes these three a spiral
rather than three more lessons.

| Lesson | Introduces | Comes back to, and expands |
|---|---|---|
| 10 | The past perfect | Conditionals (L8) → **the third conditional**: the same *had* + participle, used for a past that did not happen |
| 11 | Reported speech | The passive (L9) → **impersonal reporting passives**: *it is said that*, *she is thought to have left* |
| 12 | Relative clauses | The past perfect (L10) → **the past perfect continuous**, against the simple |

The order is forced and not a preference. Reported speech needs the past
perfect for its backshift (*she said she **had** sent it*), so the past perfect
has to come first — it is the one tense the course has never taught, and
without it Lesson 11 cannot be written honestly. The third conditional needs
the same form, which is why it is Lesson 10's come-back rather than a lesson of
its own. And Lesson 12's non-defining clause is the structure that lets a B2
writer put a source inside a sentence (*the message, which came from a group of
forty people, said…*), which is where Lessons 9 and 11 were heading all along.

---

## Lesson 10 — *An Hour Too Late*

    level   B1+ (tenth step)
    topic   A shop's accounts, a disk that failed, and a backup that finished too late
    words   520
    recall  five of Lesson 8's fourteen (uplink, mesh, relay, antenna, signal,
            latency, reliable, tower, neighbour, roof, afford, apply,
            scholarship, requirement)

**The grammar — part 04.** The past perfect: *had* + past participle, for the
earlier of two past actions. *By the time she opened the laptop, the disk had
already stopped.* Teach it against the past simple she has had since Lesson 2,
because the only reason the form exists is to put two past actions in order.
Include: *already*, *just*, *never before*, *by the time*, *when* against
*after*, and the contraction *'d*. Then the come-back: the third conditional,
*if the backup had finished, the file would have survived* — one form, two
jobs, and the second job is regret.

Teach the trap explicitly: a sequence told in the order it happened needs no
past perfect at all. *She arrived, opened the laptop and saw the error* is
correct, and better English than three *hads*. The past perfect is for when the
order of telling and the order of happening disagree.

**The pronunciation — part 05, `05-had-and-would-have`.** The weak *had*
(*she'd finished* is not *she finished* with a longer vowel), and *would have*
said as *would've* and heard as *woulda*. This is the part that needs its audio
most: a third conditional is four words long in speech and she will not hear
three of them unless she is told what to listen for.

**The passage.** A woman keeps the accounts for a small shop on a laptop. The
backup runs at midnight, over a connection that is only good late. One morning
the disk makes a noise and stops; she takes it to a repair bench; the log shows
the backup had started at ten past midnight and had finished at ten past one —
an hour after the disk had already begun to fail, so the last thing it copied
was the damage, not the accounts. Written, not reported: no real figures, no
named organisation, and the four insertion markers `[A] [B] [C] [D]` placed as
in Lesson 8.

Give it a second movement: what she changes afterwards. A backup nobody has
ever restored from is not a backup, and that is the sentence the lesson is
built towards. It is also the lesson's argument against itself — the shop had
done the right thing and still lost the week.

**Anchor vocabulary**, all new to the course: *restore, overwrite, corrupt,
retrieve, snapshot, invoice, delay, confirm*. Complete the fourteen yourself
from the passage, and check every one against `python scripts/course_state.py
--words` before you commit to it: a word taught twice breaks the course's
spacing rule, and 124 words are already spoken for.

**Writing — part 09.** A short account of something that went wrong, in an
order she chooses: three sentences in the past simple, then the same three with
one past perfect that makes the order unambiguous. Then one third-conditional
sentence about it. Not an essay; the point is the contrast.

**Review — part 10.** Keep Lesson 9's self-report question about length, and
add the one this lesson needs: *when you read a sentence with "had" in it, do
you know which thing happened first without stopping?* Her answer is what
decides whether a later lesson raises the length.

---

## Lesson 11 — *The Message That Changed Twice*

    level   B1+ (eleventh step)
    topic   A claim about a deadline, three groups it travelled through, and who said it first
    words   525
    recall  five of Lesson 9's fourteen (flood, severe, soak, shelter,
            tarpaulin, drain, pump, sandbag, displaced, relief, estimate,
            verify, source, headline)

**The grammar — part 04.** Reported speech. *say* against *tell* (*tell* needs
a person), the backshift — present to past, past simple to past perfect, *will*
to *would*, *can* to *could* — the shifts of time and place (*yesterday* to
*the day before*, *here* to *there*, *this* to *that*), reported questions with
the question word order undone (*she asked when the form closed*, not *when did
the form close*), *if/whether* for a yes-or-no question, and *told me to* and
*asked me not to* for an instruction. Then the come-back: the passive from
Lesson 9, expanded into the impersonal reporting passive — *it is said that*,
*it was reported that*, *she is thought to have left already*.

That come-back is the whole reason these two things share a lesson. Reported
speech names the source; the reporting passive deletes it. *The deadline was
said to have moved* is grammatical, fluent, and tells you nothing about who
said it — which is the skill Lesson 9's part 06 asked for, arriving this time
as grammar rather than as a table of figures. Make that link to Lesson 9
explicitly in part 04.

Teach the trap: the backshift is not automatic. Something still true can stay
in the present (*she said the office closes at two*), and a reported *that* is
usually dropped in speech, which is why she will not hear it.

**The pronunciation — part 05, `05-said-told-and-that`.** The weak *said*, the
*told her* that runs together as *told'er*, the *that* that disappears
entirely, and the stress landing on the thing claimed rather than on the
reporting verb.

**The passage.** A claim about a scholarship deadline moves through three
groups on a phone: a screenshot of a screenshot, a date that gains a day, and a
*they said* that nobody can trace. One student checks the university's own page
and finds the original. Written, not reported: invent the university, the
groups and the date, and use **no real organisation, no real figure and no real
link**. The subject is how a claim travels, and the passage must not itself be
a claim about anything real.

Second movement: what checking actually costs. Two minutes and one page — and
the reason nobody does it is that forwarding feels like helping. The argument
against itself is that the first person to forward it was trying to be useful,
and was.

**Anchor vocabulary**, all new: *rumour, claim, deny, admit, announce, forward,
screenshot, official*. Complete to fourteen from the passage; check the index.

**Writing — part 09.** Four lines of direct speech she invents, reported twice:
once naming who said it, once with the reporting passive. Then one sentence
saying which of the two she would rather read in a message from a friend, and
why.

---

## Lesson 12 — *The Room That Keeps the Light*

    level   B1+ → B2 (twelfth step)
    topic   A computer room that opens on the hours there is power, and the people in it
    words   530
    recall  five of Lesson 10's fourteen — choose them once Lesson 10 is final,
            from its committed `lesson.json`, not from this brief's anchor list,
            which is not the final fourteen

**The grammar — part 04.** Relative clauses. Defining, with
*who / which / that / whose / where*, and the object pronoun she can drop (*the
charger (that) she borrowed*). Non-defining, with its two commas, and the rule
that *that* cannot introduce one. Then the use that makes this a B2 structure
rather than a B1 one: *which* commenting on a whole clause — *the generator
stopped at eleven, which meant the last hour was on battery*. Then the
come-back: the past perfect continuous, *had been running for three hours*,
against the simple *had run* — the length of an action against its completion.

Teach the trap: the two commas change the meaning, they do not decorate it.
*The student who keeps the list* picks one student out of many; *the student,
who keeps the list,* says there is one student and adds a fact about her. Make
her write both and say what each one claims.

**The pronunciation — part 05, `05-commas-and-had-been`.** The pause and the
fall that a non-defining clause is said with, against the unbroken defining
clause — the one place in this course where punctuation is audible. And the
weak *had been*: *she'd been waiting* is three syllables in speech.

**The passage.** A university computer room with a rota on the door, open on
the hours the electricity is on. Describe it through its people and its
objects, which is what forces the relative clauses: the woman who keeps the
list, the socket that only works if you lean on the plug, the room where
everyone ends up, the student whose laptop charges fastest and who therefore
goes last. Keep it warm and specific, and let the non-defining clauses carry
the asides. Written, not reported.

Second movement: the rota itself — why a list on a door works better than
goodwill, and what it costs the person who keeps it. The argument against
itself: the rota is also a small unfairness, because it rewards whoever is
nearest the door at eight.

**Anchor vocabulary**, all new: *corridor, volunteer, borrow, lend, charger,
shelf, maintain, arrange*. Complete to fourteen; check the index. This lesson
is the course's first reaching towards B2, so two or three of the fourteen may
be abstract (*arrange*, *maintain*) and will have no drawing — that is
expected, and the memory game's *mixed* setting handles it.

**Writing — part 09.** A description of a room she knows in five sentences,
each carrying one relative clause, at least one of them non-defining. Then one
sentence using *which* to comment on the whole of the sentence before it.

**Review — part 10.** This is the twelfth lesson and the last of this run. Its
self-report asks the two questions the next run needs answered: whether the
length should finally rise, and which of the twelve grammar points she would
want taught again before a test.

---

## How a lesson is actually written

`lessons/lesson-09/lesson.json` is the worked example and
`lessons/lesson-08/lesson.json` is the twelve-part shape these three follow.
Read one of them end to end before writing a line. In particular:

- Every part is `{number, slug, title, minutes, sheet, audio, markdown}` and,
  where it has audio, `segments` — a list of `{say, voice}` and `{pause}`. The
  narrator sets up and asks; the reader reads the passage. The pauses are real
  seconds of silence, and they are the difference between a track she can work
  with and one she has to keep stopping.
- `print_only` on part 01 carries the insertion markers, which are printed and
  never spoken.
- `full_section` lists the parts that make `00-full-section.mp3` — `01, 02, 06,
  07` in a twelve-part lesson, since comprehension is 06 and true-or-false
  is 07.
- The vocabulary block drives all five games. A word gets a drawing by naming
  one that already exists in `icons.json` — there are 40. **Never invent an
  icon name.** `--check` reports it by name, but only if you run it.
- `build.py` is byte-identical in every lesson folder. Copy it; never edit it.

And the trap this course has already fallen into once: **the word count is
printed in three places** — `passage_words`, the passage heading
`### Passage: *Title* (520 words)`, and often a sentence in the review or the
answer key. Change the passage and all three have to move. The gate counts the
words itself and fails if they disagree, which is the only reason this is
survivable.
