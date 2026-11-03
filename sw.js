/* Service worker for the offline course app.
 *
 * Two caches, with different owners:
 *   esl-shell-v<n>    the app itself. This file fills it and clears it.
 *   esl-content-v1    the PDFs and MP3s the student chose to save. app.js owns
 *                     it; nothing here ever adds to or empties it, because a
 *                     file she paid data for must not disappear on an update.
 *
 * Audio is served with Range support. A phone player asks for byte ranges when
 * it seeks, and a plain cached Response answers the whole file with status 200,
 * which some players treat as unseekable or refuse outright. So a ranged
 * request against a cached file is answered here with a real 206 slice.
 */

var SHELL = "esl-shell-v1";
var CONTENT = "esl-content-v1";

var SHELL_FILES = [
  "./",
  "index.html",
  "app/app.css",
  "app/app.js",
  "app/catalog.json",
  "manifest.webmanifest",
  "app/icons/icon-192.png",
  "app/icons/icon-512.png"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(SHELL).then(function (cache) {
      // addAll fails the whole install if one file 404s, so add them singly
      return Promise.all(SHELL_FILES.map(function (f) {
        return cache.add(new Request(f, { cache: "reload" })).catch(function (e) {
          console.warn("shell: could not cache", f, e);
        });
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (names) {
      return Promise.all(names.map(function (n) {
        // keep the content cache across versions; only retire old shells
        if (n !== SHELL && n !== CONTENT) return caches.delete(n);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

/* Answer a ranged request from a cached full response. */
function rangeFrom(cached, rangeHeader) {
  return cached.arrayBuffer().then(function (buffer) {
    var size = buffer.byteLength;
    var m = /^bytes=(\d*)-(\d*)$/.exec(rangeHeader.trim());
    if (!m) {
      return new Response(buffer, { status: 200, headers: cached.headers });
    }
    var start, end;
    if (m[1] === "") {                       // bytes=-500, the last 500 bytes
      var suffix = parseInt(m[2], 10);
      if (!isFinite(suffix) || suffix <= 0) {
        return new Response(null, { status: 416 });
      }
      start = Math.max(0, size - suffix);
      end = size - 1;
    } else {
      start = parseInt(m[1], 10);
      end = m[2] === "" ? size - 1 : parseInt(m[2], 10);
    }
    if (!isFinite(start) || start >= size || start < 0) {
      return new Response(null, {
        status: 416,
        headers: { "Content-Range": "bytes */" + size }
      });
    }
    if (!isFinite(end) || end >= size) end = size - 1;

    var headers = new Headers();
    headers.set("Content-Type", cached.headers.get("Content-Type") ||
      "application/octet-stream");
    headers.set("Content-Length", String(end - start + 1));
    headers.set("Content-Range", "bytes " + start + "-" + end + "/" + size);
    headers.set("Accept-Ranges", "bytes");
    return new Response(buffer.slice(start, end + 1), {
      status: 206,
      statusText: "Partial Content",
      headers: headers
    });
  });
}

function fromCache(request) {
  var url = new URL(request.url);
  url.search = "";
  var key = url.href;
  return caches.open(CONTENT).then(function (c) {
    return c.match(key);
  }).then(function (hit) {
    if (hit) return hit;
    return caches.open(SHELL).then(function (c) { return c.match(key); });
  });
}

self.addEventListener("fetch", function (event) {
  var request = event.request;
  if (request.method !== "GET") return;

  var url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Any navigation lands on the app shell; the app routes on the hash itself.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(function () {
        return caches.open(SHELL).then(function (c) {
          return c.match("index.html") || c.match("./");
        });
      })
    );
    return;
  }

  // The catalogue changes whenever a lesson is rebuilt: prefer the network,
  // fall back to whatever was saved.
  if (url.pathname.endsWith("/app/catalog.json")) {
    event.respondWith(
      fetch(request).then(function (response) {
        if (response && response.ok) {
          var copy = response.clone();
          caches.open(SHELL).then(function (c) { c.put(request, copy); });
        }
        return response;
      }).catch(function () {
        return fromCache(request).then(function (hit) {
          return hit || Response.error();
        });
      })
    );
    return;
  }

  var range = request.headers.get("range");

  event.respondWith(
    fromCache(request).then(function (hit) {
      if (hit) {
        return range ? rangeFrom(hit.clone(), range) : hit;
      }
      return fetch(request).then(function (response) {
        // Only the shell is filled in automatically. Lesson files are saved
        // when the student asks for them, never behind her back.
        if (response && response.ok && response.type === "basic") {
          var path = url.pathname;
          var isShell = SHELL_FILES.some(function (f) {
            return path.endsWith(f.replace(/^\.\//, "/"));
          });
          if (isShell) {
            var copy = response.clone();
            caches.open(SHELL).then(function (c) { c.put(request, copy); });
          }
        }
        return response;
      });
    }).catch(function () {
      return fromCache(request).then(function (hit) {
        return hit || new Response(
          "This part has not been saved on this phone yet, and there is no " +
          "connection right now.",
          { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } }
        );
      });
    })
  );
});
