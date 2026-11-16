## Standing rules

- **Never push.** Commit locally on `main`. Raed reviews and pushes.
- **Never touch Lessons 1 to 9 or `tests/`.** Finished, committed, on her
  phone. Do not edit them and do not rebuild them.
- **Never edit a generated file.** Every `NN-*.pdf`, `NN-*.mp3`, `NN-*.html`, a
  lesson's own `README.md`, `app/catalog.json`, `sw.js`. Edit `lesson.json` and
  rebuild.
- **Never edit `build.py`** (byte-identical everywhere, holds no lesson text)
  **or `scripts/build-sw.py`** (vendored across seven sibling apps) **or
  `lesson.css`** (shared by nine shipped lessons).
- **Never widen the cache prefix past `esl-`**, and never clear
  `esl-content-v1` — it holds the files she paid data for.
- **Twelve parts, five games, fourteen key words, five recalled, ten questions,
  eight types, 500–535 words.** None of these moves. The course's promise is
  that only the text gets harder.
- **No real organisation, no real figure, no real link** in any of these three
  passages. They are written stories.
- **One network request at run time, and only the one.** The games open with
  no connection. The exception is the Cloudflare Web Analytics loader that
  `build.py` writes into every puzzle page: deliberate, upstream, exactly
  once per page. Do not remove it and do not report it as a fault.
- **Every number you print is one you counted.** Word counts, part counts,
  minute totals, folder sizes: run the command and paste what it said.
- **Do not weaken a check to make the gate green.** If something fails, say so
  and show the output.
- **Nothing the student sees identifies which AI model produced it.**
  Commit messages are the exception: end yours with the same
  `Co-Authored-By:` trailer the repository's history already uses.
