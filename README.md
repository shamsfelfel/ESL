# English, A1+ to B2 — a guided course for one student

This repository holds a complete English course written for one student: a
postgraduate at the University College of Applied Sciences in Gaza who is
applying for an exchange programme with a university in Spain, which asks for
CEFR B2. One teacher writes and runs the course, from original material and
free online resources. Every lesson is kept here as data, as printable sheets
and as audio, so that a lesson can be downloaded once and then worked through
with no connection at all.

**The course as an app: <https://shamsfelfel.github.io/ESL/>** — installable,
and it works offline once a lesson has been saved.

## The course at a glance

| | |
|---|---|
| Entry level | A1+ |
| Target level | CEFR B2 |
| Exam | TOEFL iBT (B2 ≈ 72–94) |
| Shape | One lesson a week, split into five or six sessions of 45–55 minutes |
| Skills, in their fixed order | Listening → Reading → Speaking → Writing |
| Question types | TOEFL iBT types from Lesson 1 on |
| Subject matter | Mainly information technology and computing, plus everyday life |
| Offline | Every part is a separate small file, so one part can be downloaded at a time on a phone |

Power and connectivity in Gaza are both unreliable. That is the reason for the
file layout: many small numbered files instead of a few large ones, and a build
that reports the size of everything it writes, because size is what decides
whether a file can be downloaded at all.

## How a lesson works

The sessions always run in the same order:

listening → reading → vocabulary → grammar (from Lesson 2) → comprehension →
speaking → writing → review

Four rules hold for the whole course:

- **Listen twice with no text.** The student hears the passage twice with
  nothing in front of her before she reads it. Matching sound to text too early
  blocks real listening later.
- **The question types never change.** Comprehension questions follow TOEFL iBT
  types from Lesson 1 on: factual, negative factual, vocabulary in context,
  reference and inference, with sentence insertion added in Lesson 2, purpose
  of a paragraph in Lesson 3 and the purpose of the whole passage in Lesson 4.
  Only the text gets harder, so the exam format never becomes the obstacle.
- **Vocabulary comes back two lessons later.** Words from two lessons earlier
  are heard again inside each new lesson — spaced recall, not repetition inside
  one lesson.
- **One new thing at a time.** Each lesson changes the tense, or the question
  set, or the length — not all three.

## Lessons

| Lesson | Title | Level | Topic | New in this lesson | Status |
|---|---|---|---|---|---|
| [Lesson 1](lessons/lesson-01/README.md) | [A Day with a Phone](lessons/lesson-01/README.md) | A1+ | Daily routine and basic IT | Present simple, time expressions, the five core TOEFL question types. 185-word passage. | Complete |
| [Lesson 2](lessons/lesson-02/README.md) | [The Lost Photographs](lessons/lesson-02/README.md) | A1+ → A2 | Keeping files safe, student life | Past simple, the three sounds of `-ed`, sentence insertion, a two-sentence written summary, the first spaced recall of Lesson 1 vocabulary. 244-word passage. | Complete |
| [Lesson 3](lessons/lesson-03/README.md) | [The Night the Network Failed](lessons/lesson-03/README.md) | A2 | Computing and student life: files, servers and backups | Past continuous, the weak sounds of *was* and *were*, purpose of a paragraph. 320-word passage. | Complete |
| [Lesson 4](lessons/lesson-04/README.md) | [One Small Thing, Many Times](lessons/lesson-04/README.md) | A2+ | Web design, online learning and a small shop | Present perfect with *for*, *since*, *never*, *already* and *yet*, the short forms of *have* and *has*, purpose of the whole passage, the first spaced recall of Lesson 2 vocabulary. 400-word passage. | Complete |

Lesson 5 is planned to go to roughly 480 words and add the present perfect
continuous, with a second whole-passage question about the writer's attitude.
Later lessons are built at most four lessons ahead of the student, so each one
can still answer the mistakes she is actually making.

## Tests

| Test | Covers | Length | Marks | Status |
|---|---|---|---|---|
| [Progress Test 1](tests/test-01/README.md) | Lessons 1 to 3 | About 90 minutes | 100 | Complete |

Both of the test's texts are ones she has never seen, so nothing in it can be
answered from memory of the lessons. It is a **progress test against this
course**, not a TOEFL score: it says whether the first three lessons have stuck
and which lesson to go back to. Its answer key carries the marking tables and a
section that maps each weak section to the lesson that fixes it. The key is the
last part, and it is deliberately left out of the combined `00-lesson.pdf`, so
the whole test can be printed without printing its own answers.

## Word games

Every lesson ends with two games, numbered after its last part. Both are built
from that lesson's own vocabulary, so nothing in them is new, and both are a
single HTML file with no libraries — they open from the app, from the folder or
from a phone with no connection, and they remember where you stopped.

| Game | What it drills | Direction |
|---|---|---|
| Crossword | The 14 key words and the 5 recalled ones, clued by their English meaning | Meaning → word, which is the harder way round and the one that matters for writing |
| Word search | The same words, with the Arabic beside each | Recognition and spelling: a gentler warm-up before the crossword |

They are generated by `build.py` from the `vocabulary` block in `lesson.json`,
never written by hand, so a game cannot drill a word the lesson does not teach.
If a word will not fit the crossword grid the build says so rather than dropping
it quietly.

## The app

[`https://shamsfelfel.github.io/ESL/`](https://shamsfelfel.github.io/ESL/) serves
this repository as an installable offline app, from the files in this repository
— there is no separate copy of the course to keep in step.

- It lists every lesson and the test, and inside each one every numbered part.
- Each part has a **Save** button that states its size before she presses it.
  Saving is always a choice: nothing downloads on its own, because data costs
  money.
- Saved parts work with no connection, audio included. Saved audio can still be
  seeked, because the service worker answers byte-range requests from the cache.
- It can be installed to the home screen and opened like an app.

The app is built from four files at the root — `index.html`, `sw.js`,
`manifest.webmanifest`, `.nojekyll` — plus `app/`. Its catalogue,
`app/catalog.json`, is generated by [`make_catalog.py`](make_catalog.py), which
measures the files that were actually built; a part that has not been built does
not appear, so the app never offers a download that does not exist.

## How to use this repository

### For the student

Open the app at <https://shamsfelfel.github.io/ESL/>, or go straight to a
lesson folder: [Lesson 1](lessons/lesson-01/README.md),
[Lesson 2](lessons/lesson-02/README.md),
[Lesson 3](lessons/lesson-03/README.md),
[Lesson 4](lessons/lesson-04/README.md),
[Progress Test 1](tests/test-01/README.md). Each one has a table of parts in
study order.

- **Download one numbered part at a time.** Each part is a few hundred KB. You
  do not need the whole folder, and you do not need a connection once a part is
  on your phone.
- **Play the MP3 before you open the PDF.** For part 01 that matters most:
  listen twice without reading anything.
- **The answer key is a separate file on purpose.** It is the last numbered
  part. Open it only when the parts before it are finished.
- **The two games come after the answer key.** Play them a few days later, not
  the same evening: the gap is what moves a word into memory.

If your connection is good and you would rather have one file, each lesson also
offers `00-lesson.pdf` (the whole lesson printed) and `00-full-section.mp3` (the
question tracks end to end, like a real exam section). Both are marked as the
large option in the lesson's own table.

### For the teacher

All of a lesson lives in its `lesson.json`: the printed Markdown of every part,
and the spoken segments and silences of every track. `build.py` holds no lesson
text at all and is byte-identical in every lesson and test folder, so a new
lesson is made by copying a folder and editing the JSON.

```bash
pip install -r requirements.txt
```

```bash
cd lessons/lesson-03 && python build.py --check
```

```bash
cd lessons/lesson-03 && python build.py --plan
```

```bash
cd lessons/lesson-03 && python build.py --build
```

Then refresh the app's catalogue from the repository root:

```bash
python make_catalog.py
```

`--build` writes every sheet, every MP3, both games and that folder's
`README.md`, then
reports each file with its length and size and the folder total. Use
`--only 01 04` for selected parts, `--pdf-only` when there is no connection, and
`--audio-only` to skip the sheets. Every spoken segment is cached by its text in
`.audio-cache/` at the repository root, shared by all lessons and never
committed, so a dropped connection costs only the segments that had not
finished: run the same command again and it carries on.

The generated PDFs and MP3s **are** committed, on purpose, so the student can
download a single file without running anything. One stylesheet,
[`lesson.css`](lesson.css), is used by every lesson; the page footer takes the
lesson name from the JSON rather than from the stylesheet. A part may set
`"in_whole": false` to stay out of the combined PDF, which is how the test keeps
its answer key off the printed paper.

On Windows, WeasyPrint also needs the GTK runtime libraries (libgobject, pango),
which `pip` does not install; `python build.py --check` says so plainly if they
are missing, and the MP3s build without them.

---

This is private teaching material, written for one student.
