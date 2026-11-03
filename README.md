# English, A1+ to B2 — a guided course for one student

This repository holds a complete English course written for one student: a
postgraduate at the University College of Applied Sciences in Gaza who is
applying for an exchange programme with a university in Spain, which asks for
CEFR B2. One teacher writes and runs the course, from original material and
free online resources. Every lesson is kept here as data, as printable sheets
and as audio, so that a lesson can be downloaded once and then worked through
with no connection at all.

## The course at a glance

| | |
|---|---|
| Entry level | A1+ |
| Target level | CEFR B2 |
| Shape | One lesson a week, split into five or six sessions of 45–55 minutes |
| Skills, in their fixed order | Listening → Reading → Speaking → Writing |
| Question types | TOEFL iBT types from Lesson 1 on |
| Offline | Every part is a separate small file, so one part can be downloaded at a time on a phone |

Power and connectivity in Gaza are both unreliable. That is the reason for the
file layout: many small numbered files instead of a few large ones, and a build
that reports the size of everything it writes, because size is what decides
whether a file can be downloaded at all.

## How a lesson works

The sessions always run in the same order:

listening → reading → vocabulary → grammar (from Lesson 2) → comprehension →
speaking → writing → review

Three rules hold for the whole course:

- **Listen twice with no text.** The student hears the passage twice with
  nothing in front of her before she reads it. Matching sound to text too early
  blocks real listening later.
- **The question types never change.** Comprehension questions follow TOEFL iBT
  types from Lesson 1 on: factual, negative factual, vocabulary in context,
  reference and inference, with sentence insertion added in Lesson 2. Only the
  text gets harder, so the exam format never becomes the obstacle.
- **Vocabulary comes back two lessons later.** Words from two lessons earlier
  are heard again inside each new lesson — spaced recall, not repetition inside
  one lesson.

Passage topics come mainly from information technology and everyday life.

## Lessons

| Lesson | Title | Level | Topic | New in this lesson | Status |
|---|---|---|---|---|---|
| [Lesson 1](lessons/lesson-01/README.md) | [A Day with a Phone](lessons/lesson-01/README.md) | A1+ | Daily routine and basic IT | Present simple, time expressions, the five core TOEFL question types. 185-word passage. | Complete |
| [Lesson 2](lessons/lesson-02/README.md) | [The Lost Photographs](lessons/lesson-02/README.md) | A1+ → A2 | Keeping files safe, student life | Past simple, the three sounds of `-ed`, sentence insertion, a two-sentence written summary, the first spaced recall of Lesson 1 vocabulary. 244-word passage. | Complete |

Lesson 3 is planned to move to a longer passage with the past continuous. Later
lessons are built at most four lessons ahead of the student, so that each one
can still answer the mistakes she is actually making.

## The plan

The planning documents are not in this repository yet. There is no `plan/`
folder; the course plan currently lives outside the repository, and the teacher
notes at the end of each lesson carry the reasoning for that lesson and the
decision about what comes next.

## How to use this repository

### For the student

Open the lesson you are working on — [Lesson 1](lessons/lesson-01/README.md) or
[Lesson 2](lessons/lesson-02/README.md) — and you will find a table of parts in
study order.

- **Download one numbered part at a time.** Each part is a few hundred KB. You
  do not need the whole folder, and you do not need a connection once a part is
  on your phone.
- **Play the MP3 before you open the PDF.** For part 01 that matters most:
  listen twice without reading anything.
- **The answer key is a separate file on purpose.** It is the last numbered
  part. Open it only when the parts before it are finished.

If your connection is good and you would rather have one file, each lesson also
offers `00-lesson.pdf` (the whole lesson printed) and `00-full-section.mp3` (the
question tracks end to end, like a real exam section). Both are marked as the
large option in the lesson's own table.

### For the teacher

All of a lesson lives in its `lesson.json`: the printed Markdown of every part,
and the spoken segments and silences of every track. `build.py` holds no lesson
text at all and is byte-identical in every lesson folder, so a new lesson is
made by copying a folder and editing the JSON.

```bash
pip install -r requirements.txt
```

```bash
cd lessons/lesson-01 && python build.py --check
```

```bash
cd lessons/lesson-01 && python build.py --plan
```

```bash
cd lessons/lesson-01 && python build.py --build
```

`--build` writes every sheet, every MP3 and that folder's `README.md`, then
reports each file with its length and size and the folder total. Use
`--only 01 04` for selected parts, `--pdf-only` when there is no connection, and
`--audio-only` to skip the sheets. Every spoken segment is cached by its text in
`.audio-cache/` at the repository root, shared by all lessons and never
committed, so a dropped connection costs only the segments that had not
finished: run the same command again and it carries on.

The generated PDFs and MP3s **are** committed, on purpose, so the student can
download a single file without running anything. One stylesheet,
[`lesson.css`](lesson.css), is used by every lesson; the page footer takes the
lesson name from the JSON rather than from the stylesheet.

On Windows, WeasyPrint also needs the GTK runtime libraries (libgobject, pango),
which `pip` does not install; `python build.py --check` says so plainly if they
are missing, and the MP3s build without them.

---

This is private teaching material, written for one student.
