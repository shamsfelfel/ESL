/* Offline course app.
 *
 * No framework and no build step: this file is served exactly as it is written.
 * Everything the app knows comes from app/catalog.json, which make_catalog.py
 * writes from the lesson files that were actually built.
 *
 * Saving is deliberate, never automatic. Data costs money and the connection
 * drops, so the student chooses each part she keeps, and every button says what
 * it will cost before she presses it.
 */
(function () {
  "use strict";

  var BASE = new URL(".", location.href.split("#")[0]).href;
  var CONTENT_CACHE = "esl-content-v1";
  var catalog = null;
  var installEvent = null;

  // ---------------------------------------------------------------- helpers

  function abs(rel) { return new URL(rel, BASE).href; }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fmtSize(bytes) {
    if (bytes == null) return "";
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return Math.round(bytes / 1024) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }

  function fmtTime(seconds) {
    if (seconds == null) return "";
    var m = Math.floor(seconds / 60), s = Math.round(seconds % 60);
    if (s === 60) { m += 1; s = 0; }
    return m + " min" + (s ? " " + s + " s" : "");
  }

  function partFiles(course, part) {
    var out = [];
    if (part.pdf) out.push(course.path + "/" + part.pdf.file);
    if (part.mp3) out.push(course.path + "/" + part.mp3.file);
    return out;
  }

  function partBytes(part) {
    return (part.pdf ? part.pdf.bytes : 0) + (part.mp3 ? part.mp3.bytes : 0);
  }

  // ------------------------------------------------------------ cache state

  function cacheOpen() {
    return ("caches" in window) ? caches.open(CONTENT_CACHE) : Promise.reject();
  }

  function isSaved(urls) {
    if (!urls.length || !("caches" in window)) return Promise.resolve(false);
    return cacheOpen().then(function (c) {
      return Promise.all(urls.map(function (u) { return c.match(abs(u)); }))
        .then(function (hits) { return hits.every(Boolean); });
    }).catch(function () { return false; });
  }

  function save(urls) {
    return cacheOpen().then(function (c) {
      return Promise.all(urls.map(function (u) {
        return fetch(abs(u), { cache: "reload" }).then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status + " for " + u);
          return c.put(abs(u), r);
        });
      }));
    });
  }

  function drop(urls) {
    return cacheOpen().then(function (c) {
      return Promise.all(urls.map(function (u) { return c.delete(abs(u)); }));
    });
  }

  // --------------------------------------------------------------- rendering

  var view = document.getElementById("view");

  function render(html) {
    view.innerHTML = html;
    view.focus();
    window.scrollTo(0, 0);
  }

  function courseBySlug(slug) {
    for (var i = 0; i < catalog.courses.length; i++) {
      if (catalog.courses[i].slug === slug) return catalog.courses[i];
    }
    return null;
  }

  function home() {
    var cards = catalog.courses.map(function (c) {
      var tag = c.kind === "test"
        ? '<span class="tag tag-test">Test</span>'
        : '<span class="tag">Lesson ' + c.number + "</span>";
      return '<a class="card" href="#/' + esc(c.slug) + '">' + tag +
        "<h3>" + esc(c.title) + "</h3>" +
        '<div class="meta">' + esc(c.level) + " &middot; " + esc(c.topic) + "</div>" +
        '<div class="meta">' + c.parts.length + " parts &middot; about " +
        c.minutes + " minutes &middot; " + fmtSize(c.bytes) + " in all</div></a>";
    }).join("");

    render("<h1>" + esc(catalog.title) + "</h1>" +
      '<p class="lede">' + esc(catalog.subtitle) + "</p>" +
      '<div class="note">Everything here works with no connection once you have ' +
      "saved it. Open a lesson, then save one part at a time &mdash; each part " +
      "is small, and the whole lesson is not.</div>" +
      cards +
      '<h2>How a lesson works</h2><p class="dim">Listen to the passage twice ' +
      "with no text in front of you, then read it. The question types are the " +
      "same in every lesson, so only the English gets harder, never the " +
      "format. Answer keys are always the last part, so you can work without " +
      "seeing them.</p>");
  }

  function lesson(c) {
    var steps = c.howToWork.map(function (s) {
      return "<li>" + inline(s) + "</li>";
    }).join("");

    var whole = "";
    if (c.whole.pdf || c.whole.mp3) {
      var bits = [];
      if (c.whole.pdf) {
        bits.push('<a class="btn btn-small" target="_blank" rel="noopener" href="' +
          esc(c.path + "/" + c.whole.pdf.file) + '">Whole ' +
          (c.kind === "test" ? "test" : "lesson") + " as one PDF &middot; " +
          (c.whole.pdf.pages ? c.whole.pdf.pages + " pages, " : "") +
          fmtSize(c.whole.pdf.bytes) + "</a>");
      }
      if (c.whole.mp3) {
        bits.push('<a class="btn btn-small" target="_blank" rel="noopener" href="' +
          esc(c.path + "/" + c.whole.mp3.file) + '">All question audio &middot; ' +
          fmtTime(c.whole.mp3.seconds) + ", " + fmtSize(c.whole.mp3.bytes) + "</a>");
      }
      whole = "<h2>The large option</h2>" +
        '<p class="dim">One big file instead of many small ones. Only worth it ' +
        'on a good connection.</p><div class="row">' + bits.join("") + "</div>";
    }

    var parts = c.parts.map(function (p, i) {
      var files = partFiles(c, p);
      var links = [];
      if (p.pdf) {
        links.push('<a class="btn btn-small" target="_blank" rel="noopener" href="' +
          esc(c.path + "/" + p.pdf.file) + '">Sheet &middot; ' +
          (p.pdf.pages ? p.pdf.pages + (p.pdf.pages === 1 ? " page, " : " pages, ") : "") +
          fmtSize(p.pdf.bytes) + "</a>");
      }
      var audio = p.mp3
        ? '<audio controls preload="none" src="' +
          esc(c.path + "/" + p.mp3.file) + '"></audio>'
        : "";
      var cost = partBytes(p);
      var saveBtn = files.length
        ? '<button class="btn btn-small save" data-part="' + i + '">Save ' +
          fmtSize(cost) + "</button>"
        : "";

      return '<div class="part" id="p' + esc(p.number) + '">' +
        '<div class="part-head"><span class="part-no">' + esc(p.number) + "</span>" +
        '<span class="part-title">' + esc(p.title) + "</span>" +
        '<span class="part-min">' + p.minutes + " min</span></div>" +
        (p.mp3 ? '<div class="part-min dim">Audio ' + fmtTime(p.mp3.seconds) +
          " &middot; " + fmtSize(p.mp3.bytes) + "</div>" : "") +
        audio +
        '<div class="row">' + links.join("") + saveBtn + "</div></div>";
    }).join("");

    render('<a class="back" href="#/">All lessons</a>' +
      "<h1>" + esc(c.title) + "</h1>" +
      '<div class="facts">' +
      "<div><b>Level:</b> " + esc(c.level) + "</div>" +
      "<div><b>Topic:</b> " + esc(c.topic) + "</div>" +
      "<div><b>Time:</b> " + esc(c.time) + "</div>" +
      "<div><b>New here:</b> " + esc(c.new) + "</div>" +
      "</div>" +
      "<h2>How to work through this</h2><ol class=\"steps\">" + steps + "</ol>" +
      '<div class="row"><button class="btn btn-fill" id="saveAll">Save every part ' +
      "&middot; " + fmtSize(c.parts.reduce(function (t, p) { return t + partBytes(p); }, 0)) +
      '</button><button class="btn btn-small" id="dropAll">Remove saved</button></div>' +
      "<h2>The parts, in order</h2>" + parts + whole);

    wireLesson(c);
  }

  /* The lesson text uses a little Markdown for emphasis; render just that. */
  function inline(s) {
    return esc(s)
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
      .replace(/\*([^*]+)\*/g, "<i>$1</i>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  }

  function wireLesson(c) {
    var buttons = [].slice.call(view.querySelectorAll("button.save"));

    buttons.forEach(function (btn) {
      var part = c.parts[+btn.dataset.part];
      var files = partFiles(c, part);

      isSaved(files).then(function (saved) { mark(btn, saved, part); });

      btn.addEventListener("click", function () {
        btn.disabled = true;
        isSaved(files).then(function (saved) {
          var job = saved ? drop(files) : save(files);
          btn.textContent = saved ? "Removing…" : "Saving…";
          return job.then(function () {
            mark(btn, !saved, part);
            btn.disabled = false;
            storageLine();
          });
        }).catch(function (err) {
          btn.textContent = "Could not save — try again";
          btn.disabled = false;
          console.error(err);
        });
      });
    });

    var all = view.querySelector("#saveAll");
    if (all) {
      all.addEventListener("click", function () {
        all.disabled = true;
        all.textContent = "Saving every part…";
        var urls = c.parts.reduce(function (acc, p) {
          return acc.concat(partFiles(c, p));
        }, []);
        save(urls).then(function () {
          all.textContent = "Saved. This lesson works offline.";
          buttons.forEach(function (b) {
            mark(b, true, c.parts[+b.dataset.part]);
          });
          storageLine();
        }).catch(function (err) {
          all.textContent = "Some parts did not save — try again";
          all.disabled = false;
          console.error(err);
        });
      });
    }

    var none = view.querySelector("#dropAll");
    if (none) {
      none.addEventListener("click", function () {
        var urls = c.parts.reduce(function (acc, p) {
          return acc.concat(partFiles(c, p));
        }, []);
        if (c.whole.pdf) urls.push(c.path + "/" + c.whole.pdf.file);
        if (c.whole.mp3) urls.push(c.path + "/" + c.whole.mp3.file);
        drop(urls).then(function () {
          buttons.forEach(function (b) {
            mark(b, false, c.parts[+b.dataset.part]);
          });
          if (all) { all.disabled = false; }
          if (all) {
            all.textContent = "Save every part · " + fmtSize(
              c.parts.reduce(function (t, p) { return t + partBytes(p); }, 0));
          }
          storageLine();
        });
      });
    }
  }

  function mark(btn, saved, part) {
    btn.textContent = saved ? "Saved — remove" : "Save " + fmtSize(partBytes(part));
    btn.classList.toggle("btn-saved", saved);
  }

  // ------------------------------------------------------------------ routing

  function route() {
    if (!catalog) return;
    var slug = (location.hash || "#/").replace(/^#\/?/, "");
    if (!slug) { home(); return; }
    var c = courseBySlug(slug);
    if (c) { lesson(c); } else { home(); }
  }

  // ------------------------------------------------------------------- chrome

  function storageLine() {
    var el = document.getElementById("storage");
    if (!el || !navigator.storage || !navigator.storage.estimate) return;
    navigator.storage.estimate().then(function (e) {
      if (e && e.usage) {
        el.textContent = "Saved on this phone: " + fmtSize(e.usage) + ".";
      }
    }).catch(function () {});
  }

  function netLine() {
    var el = document.getElementById("net");
    if (el) el.hidden = navigator.onLine;
  }

  window.addEventListener("online", netLine);
  window.addEventListener("offline", netLine);
  window.addEventListener("hashchange", route);

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    installEvent = e;
    var b = document.getElementById("install");
    if (!b) return;
    b.hidden = false;
    b.addEventListener("click", function () {
      b.hidden = true;
      installEvent.prompt();
      installEvent = null;
    });
  });

  // --------------------------------------------------------------------- boot

  fetch("app/catalog.json", { cache: "no-cache" })
    .then(function (r) { return r.json(); })
    .then(function (data) { catalog = data; route(); })
    .catch(function () {
      // offline and never loaded: the service worker should have a copy
      return caches.match(abs("app/catalog.json")).then(function (r) {
        if (!r) throw new Error("no catalog");
        return r.json().then(function (data) { catalog = data; route(); });
      });
    })
    .catch(function () {
      render("<h1>Not loaded yet</h1><p>This app has not been opened online " +
        "yet, so there is nothing saved on the phone. Connect once, and after " +
        "that it works offline.</p>");
    });

  netLine();
  storageLine();

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("sw.js").catch(function (err) {
        console.warn("Service worker did not register:", err);
      });
    });
  }
})();
