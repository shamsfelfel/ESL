#!/usr/bin/env python3
"""Write sw.js for one of the apps on shamsfelfel.github.io.

This is the only service-worker generator in the family. It is authoritative
in this repository and vendored byte-for-byte into each course repository, so
that a course can be built and deployed with no other checkout present. What
differs between the seven apps is data, in `sw.config.json` at each repo root,
not code: there is one template and one implementation of the invariants.

    python scripts/build-sw.py            # write sw.js
    python scripts/build-sw.py --check    # verify sw.js, and this file
    python scripts/build-sw.py --list     # print the precache list and stop

Three things in here are load-bearing, and all three exist because of a bug
that reached the live site.

**The precache list comes from git, not from the filesystem.** What is
deployed is what is committed, so `git ls-files` is the source of truth. The
generators this replaced walked the directory tree, which swept the author's
uncommitted, in-progress lesson files into the list -- and on the deployed
site those are precache entries that 404 for every reader. An uncommitted file
is now invisible to this script by construction, not by a skip rule somebody
has to remember to write.

**The cache name is a content hash, and nothing in the generated file is a
timestamp.** A browser reinstalls a worker only when sw.js changes
byte-for-byte, and install re-adds every entry with `cache: 'reload'`, which
bypasses the HTTP cache. A build date in a comment would therefore make every
rebuild cost every installed reader a full re-download of the whole app. The
readers are students on metered connections in Gaza; a rebuild that changes
nothing must change nothing.

**`activate` deletes only caches whose name starts with this app's own
prefix.** The seven apps share one GitHub Pages origin, and Cache Storage is
scoped to an origin and not to a path: every app's `caches.keys()` lists all
seven apps' caches. Four of the workers this replaces deleted every cache that
was not their own, which took the other six apps offline on every deployment.
The guard is asserted here before the file is written, asserted again by
--check, and asserted behaviourally by `e2e/sw-invariants.spec.js`.

## sw.config.json

    prefix              required. Every cache this app owns starts with it.
                        Lowercase, ends with "-", unique across the family.
    precache            required. Ordered rules over the git file list, with
                        gitignore semantics: last match wins, "!" negates, "*"
                        does not cross "/", "**" does, a leading "/" anchors
                        at the repository root, and a pattern with no "/" at
                        all matches that basename at any depth.
    navigate_fallback   "redirect" (land the reader on the app's real home,
                        the right answer when pages live in subdirectories) or
                        {"shell": "index.html"} (answer every navigation with
                        one shell, for an app that routes on the hash).
    keep_caches         caches that match `prefix` but belong to the page
                        rather than to this worker: read from first, never
                        written to, never deleted. ESL's downloaded PDFs and
                        audio live in one of these.
    range_support       answer a ranged request against a cached file with a
                        real 206 slice. Phone audio players seek.
    runtime_cache       "any": a response fetched on a cache miss is kept.
                        "precache": only files the app ships are kept, so
                        nothing is saved to the reader's phone behind her back.
    network_first       paths that must be fresh when online, if they are
                        there at all -- a catalogue, an index.
    ignore_search       match cache entries ignoring the query string.
    offline_text        a sentence to answer with when a file is neither
                        cached nor reachable, instead of a browser error.
    passthrough_from    {"file", "regex"}: paths this worker must not touch,
                        read out of another file so the two cannot drift. The
                        hub's scope is "/", so it sits in front of every
                        course folder until that course registers its own
                        worker; those requests go straight to the network.
    note                a paragraph for the generated file's header.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "sw.config.json"
TARGET = ROOT / "sw.js"

# The two files every app shares unchanged: this generator, and the invariant
# suite that tests what it writes. Both hashes are stamped by the hub's
# scripts/vendor-sw.py, and --check recomputes both -- so a vendored copy that
# has been edited in place fails that repository's own test suite, with no hub
# checkout and no network needed. Drift cannot hide.
ENGINE_SHA256 = "c44e9706c9686379540ba81cc2dc28d178d812a530d5eb8dfab957ca881d1f77"
SPEC_SHA256 = "9318f75e2fa8df534b18841562c44724a345aa001bf65708e791f0a41733f9b4"

SPEC = "e2e/sw-invariants.spec.js"

_STAMP = re.compile(r'^ENGINE_SHA256 = ".*"$', re.M)

# How many hex characters of a file's sha256 go in HASHES. 48 bits, compared
# per URL against the previous build of that same URL; a false "unchanged"
# would need the old and new contents of one file to collide.
HASH_LEN = 12


# ---------------------------------------------------------------- the engine


def engine_hash(text=None):
    """This file's own hash, independent of line endings and of the stamp."""
    if text is None:
        text = Path(__file__).resolve().read_text(encoding="utf-8")
    canonical = _STAMP.sub('ENGINE_SHA256 = ""', text)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def spec_hash():
    """The shared invariant suite's hash, or None where it is not checked out."""
    path = ROOT / SPEC
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- the config


DEFAULTS = {
    "prefix": None,
    "precache": None,
    "navigate_fallback": "redirect",
    "keep_caches": [],
    "range_support": False,
    "runtime_cache": "any",
    "network_first": [],
    "ignore_search": False,
    "offline_text": None,
    "passthrough_from": None,
    "note": "",
}


def load_config():
    if not CONFIG.exists():
        die("no sw.config.json beside this repository's root -- see the "
            "header of scripts/build-sw.py for the keys")
    try:
        raw = json.loads(CONFIG.read_text(encoding="utf-8"))
    except ValueError as exc:
        die("sw.config.json is not valid JSON: %s" % exc)

    unknown = sorted(set(raw) - set(DEFAULTS) - {"$schema", "_comment"})
    if unknown:
        die("sw.config.json has keys this generator does not know: %s"
            % ", ".join(unknown))

    cfg = dict(DEFAULTS)
    cfg.update({k: v for k, v in raw.items() if k in DEFAULTS})

    prefix = cfg["prefix"]
    if not isinstance(prefix, str) or not re.fullmatch(r"[a-z0-9]+-", prefix):
        die('prefix must be lowercase and end with "-", e.g. "la-"; got %r'
            % (prefix,))
    if not isinstance(cfg["precache"], list) or not cfg["precache"]:
        die("precache must be a non-empty list of rules")

    for name in cfg["keep_caches"]:
        # A kept cache that does not carry this app's prefix is either a
        # typo or an attempt to hold on to a sibling's storage. Both are
        # bugs, and the second one is the bug this whole exercise is about.
        if not name.startswith(prefix):
            die("keep_caches entry %r does not start with the prefix %r"
                % (name, prefix))

    fallback = cfg["navigate_fallback"]
    if fallback != "redirect":
        if not isinstance(fallback, dict) or list(fallback) != ["shell"]:
            die('navigate_fallback must be "redirect" or {"shell": "<url>"}')

    if cfg["runtime_cache"] not in ("any", "precache"):
        die('runtime_cache must be "any" or "precache"')

    src = cfg["passthrough_from"]
    if src is not None:
        if not isinstance(src, dict) or set(src) != {"file", "regex"}:
            die('passthrough_from must be {"file": ..., "regex": ...}')

    return cfg


# ------------------------------------------------------- the list of files


def git(*args):
    """Run git in this repository, or return None if that is not possible."""
    try:
        out = subprocess.run(("git", "-C", str(ROOT)) + args,
                             capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.decode("utf-8", "replace")


def shipped_files():
    """Every file that ships, as a repo-root-relative POSIX path, sorted.

    Tracked and present in the working tree. A file tracked but deleted from
    the working tree is excluded: it is still on the deployed site until the
    deletion is committed, but it cannot be served here, so listing it would
    break this repository's own offline test -- and the sw.js this writes is
    committed in the same commit as the deletion.
    """
    listing = git("ls-files", "-z", "--cached", "--exclude-standard")
    if listing is None:
        # Not a checkout: an unpacked tarball, or git is missing. Fall back to
        # the tree, loudly, because this is exactly the mode in which the old
        # generators listed files that were not on the deployed site.
        warn("not a git checkout -- falling back to the filesystem, which "
             "cannot tell a committed file from a scratch one")
        files = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                 if p.is_file()]
        return sorted(files), False

    files = [p for p in listing.split("\0") if p]
    return sorted(p for p in files if (ROOT / p).is_file()), True


def compile_rule(pattern):
    """A precache rule -> (negated, compiled regex) over a POSIX path."""
    negated = pattern.startswith("!")
    if negated:
        pattern = pattern[1:]
    if pattern.startswith("/"):
        # Anchored at the repository root, as in a .gitignore. "/index.html"
        # is the home page; "index.html" would also match the one in
        # src/content/, which is a build input and must not ship.
        pattern = pattern[1:]
    elif "/" not in pattern:
        # Like gitignore: a bare name or extension glob matches at any depth.
        pattern = "**/" + pattern

    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:[^/]+/)*")       # zero or more directories
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return negated, re.compile("".join(out) + r"\Z")


def select(files, rules):
    """Apply the rules in order -- last match wins -- and keep what is in."""
    compiled = [compile_rule(r) for r in rules]
    kept = []
    for path in files:
        state = False
        for negated, rx in compiled:
            if rx.match(path):
                state = not negated
        if state:
            kept.append(path)
    return kept


def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 16), b""):
            h.update(block)
    return h.hexdigest()[:HASH_LEN]


def passthrough(cfg):
    """The paths this worker must leave alone, read from another file."""
    src = cfg["passthrough_from"]
    if src is None:
        return []
    path = ROOT / src["file"]
    if not path.exists():
        die("passthrough_from names %s, which is not there" % src["file"])
    found = re.findall(src["regex"], path.read_text(encoding="utf-8"), re.M)
    if not found:
        die("passthrough_from found nothing in %s -- has its shape changed?"
            % src["file"])
    return sorted(set(found))


# -------------------------------------------------------------- the template


HEADER = """\
/* ============================================================
   Service worker -- GENERATED by scripts/build-sw.py from
   sw.config.json. Do not edit this file: edit the config, or the
   generator, and run the generator again.

%(note)s
   Install precaches every file this app ships, so that after one
   visit the whole thing opens with the network off and the browser
   offers to install it.

   Navigations are network-first: online the reader gets the page as
   it is on the server, and the copy that answered goes back into the
   cache; offline the cached page answers instead.

   Assets are cache-first. They are versioned by this file's cache
   name, so there is nothing to revalidate.
   ============================================================ */
'use strict';

/* The cache this worker owns. The name is a content hash of every
   entry in PRECACHE, so it changes when -- and only when -- a file
   that ships changes. A rebuild that changes nothing keeps the name,
   and this file stays byte-identical, so an installed reader
   re-downloads nothing: there are no timestamps in here on purpose. */
var CACHE = '%(cache)s';

/* THE INVARIANT ON THIS ORIGIN.

   Seven apps are served from shamsfelfel.github.io -- the hub at the
   root, six courses in folders beside each other. Cache Storage is
   scoped to the origin and not to the path, so caches.keys() in the
   activate handler below lists all seven apps' caches. Every cache
   this app owns starts with PREFIX, and activate deletes nothing that
   does not. A worker that deleted "every cache that is not mine" --
   which four of them did until 4 November 2026 -- takes the other six
   apps offline every time this one is deployed. */
var PREFIX = '%(prefix)s';

/* Caches that carry PREFIX but belong to the page rather than to this
   worker: searched first on a hit, never written to here, and never
   deleted here -- not on this app's own update, and not on a
   sibling's. A file the reader spent data on must survive both. */
var KEEP = %(keep)s;

/* Searched in order, so a file the reader deliberately saved answers
   ahead of the shipped copy. */
var READ = KEEP.concat([CACHE]);

var MATCH = { ignoreSearch: %(ignore_search)s };

/* Everything this app ships, relative to this file -- which sits at
   the site root, so every path resolves the same whether the app is
   served from a domain root or from a GitHub Pages project subpath.

   Derived from `git ls-files`: what is deployed is what is committed.
   A file that is not committed is not on the deployed site, so listing
   it here would be a precache entry that 404s for every reader. */
var PRECACHE = [
%(precache)s
];

/* Parallel to PRECACHE: each entry's content hash at build time. Used
   by install to copy a file that has not changed out of the previous
   cache instead of downloading it again -- so editing one lesson in a
   course of two hundred files costs one download, not two hundred. */
var HASHES = [
%(hashes)s
];
"""

INSTALL = """
/* The first %(hash_len)d hex characters of a body's SHA-256, the same way
   build-sw.py computes HASHES. */
function digest(buffer) {
  return crypto.subtle.digest('SHA-256', buffer).then(function (sum) {
    var bytes = new Uint8Array(sum), out = '';
    for (var i = 0; i < %(hash_bytes)d; i++) {
      out += (bytes[i] + 0x100).toString(16).slice(1);
    }
    return out;
  });
}

/* A byte-identical copy of `url` already in one of our caches, or null.

   The candidate's actual bytes are hashed and compared against what
   this build ships, rather than trusting a stored manifest: an entry
   holding a stale body, or an error page saved under that URL, fails
   the comparison and is fetched again. On a first install there is no
   previous cache, nothing matches, and everything is downloaded -- the
   behaviour this replaced. */
function reusable(sources, url, want) {
  if (!want) return Promise.resolve(null);
  function attempt(i) {
    if (i >= sources.length) return null;
    return caches.match(url, { cacheName: sources[i] }).then(function (hit) {
      if (!hit) return attempt(i + 1);
      return hit.clone().arrayBuffer().then(digest).then(function (got) {
        return got === want ? hit : attempt(i + 1);
      });
    })['catch'](function () { return attempt(i + 1); });
  }
  return Promise.resolve(attempt(0));
}

self.addEventListener('install', function (event) {
  event.waitUntil(
    /* Listed before CACHE is opened, on purpose: on a first install there
       is nothing of ours on the origin yet, so `sources` comes back empty
       and every entry goes straight to the network. Asking after opening
       CACHE would mean a lookup per entry against a cache that cannot
       possibly hold anything -- two hundred of them, delaying the
       downloads that are the whole point of install, and with them the
       page the reader is waiting for.

       Names, not open caches. caches.open CREATES a cache that is not
       there, so opening the names from a keys() listing can resurrect --
       as an empty cache, under the same name -- a cache that activate
       deleted a moment ago in another tab. The only cache this worker
       ever opens is its own. */
    caches.keys().then(function (keys) {
      var sources = keys.filter(function (k) {
        return k.indexOf(PREFIX) === 0 && KEEP.indexOf(k) < 0;
      });
      return caches.open(CACHE).then(function (cache) {
        /* One entry at a time: addAll rejects as a unit, so a single
           404 would leave the worker uninstalled and the app with no
           offline support at all. */
        return Promise.all(PRECACHE.map(function (url, i) {
          if (!sources.length) {
            return cache.add(new Request(url, { cache: 'reload' }))
              ['catch'](function () {});
          }
          return reusable(sources, url, HASHES[i]).then(function (hit) {
            if (hit) return cache.put(url, hit);
            return cache.add(new Request(url, { cache: 'reload' }));
          })['catch'](function () {});
        }));
      });
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        /* THE INVARIANT. Only this app's own superseded caches: the
           six sibling apps on this origin own everything else, and
           KEEP belongs to the page. */
        if (k === CACHE || KEEP.indexOf(k) >= 0) return null;
        return k.indexOf(PREFIX) === 0 ? caches['delete'](k) : null;
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('message', function (event) {
  if (event.data === 'skipWaiting') self.skipWaiting();
});

/* A hit from any of our caches, page-owned ones first. Through
   caches.match with a cacheName rather than caches.open, which would
   create a cache that is not there -- see install. */
function cachedMatch(request) {
  function attempt(i) {
    if (i >= READ.length) return undefined;
    return caches.match(request, {
      cacheName: READ[i], ignoreSearch: MATCH.ignoreSearch
    })['catch'](function () { return undefined; }).then(function (hit) {
      return hit || attempt(i + 1);
    });
  }
  return Promise.resolve(attempt(0));
}
"""

RANGE = """
/* Answer a ranged request out of a cached whole response.

   A phone's audio player asks for byte ranges when the listener seeks,
   and a cached Response handed back as it is answers the whole file
   with status 200 -- which some players treat as unseekable and others
   refuse outright. So a ranged request against a cached file is
   answered here with a real 206 slice. */
function slice(cached, header) {
  return cached.arrayBuffer().then(function (buffer) {
    var size = buffer.byteLength;
    var m = /^bytes=(\\d*)-(\\d*)$/.exec(header.trim());
    if (!m) {
      return new Response(buffer, { status: 200, headers: cached.headers });
    }
    var start, end;
    if (m[1] === '') {                     /* bytes=-500: the last 500 bytes */
      var suffix = parseInt(m[2], 10);
      if (!isFinite(suffix) || suffix <= 0) {
        return new Response(null, { status: 416 });
      }
      start = Math.max(0, size - suffix);
      end = size - 1;
    } else {
      start = parseInt(m[1], 10);
      end = m[2] === '' ? size - 1 : parseInt(m[2], 10);
    }
    if (!isFinite(start) || start >= size || start < 0) {
      return new Response(null, {
        status: 416,
        headers: { 'Content-Range': 'bytes */' + size }
      });
    }
    if (!isFinite(end) || end >= size) end = size - 1;

    var headers = new Headers();
    headers.set('Content-Type', cached.headers.get('Content-Type') ||
      'application/octet-stream');
    headers.set('Content-Length', String(end - start + 1));
    headers.set('Content-Range', 'bytes ' + start + '-' + end + '/' + size);
    headers.set('Accept-Ranges', 'bytes');
    return new Response(buffer.slice(start, end + 1), {
      status: 206,
      statusText: 'Partial Content',
      headers: headers
    });
  });
}
"""

PASSTHROUGH = """
/* Paths this worker must not touch, kept in step with %(from_file)s by
   the build script that wrote this file.

   This app's scope is "/", the whole origin, which also covers every
   course folder -- so until a course has been opened once and has
   registered its own, more specific worker, that course's requests
   arrive here. They are passed to the network untouched, for two
   reasons: caching them here would hold a second, ageing copy of
   pages the course's own worker owns, and answering one from this
   app's shell would render this app's HTML under a course URL, where
   every relative link resolves one directory too deep. A course that
   has not been saved therefore fails to open offline, which is the
   truth, and the home page says as much. */
var PASSTHROUGH = [
%(paths)s
];

function isPassthrough(url) {
  /* url.pathname is absolute ("/linear-algebra/..."); this app is
     served from the origin root, so a leading-slash compare is
     enough. */
  for (var i = 0; i < PASSTHROUGH.length; i++) {
    if (url.pathname.indexOf('/' + PASSTHROUGH[i] + '/') === 0) return true;
  }
  return false;
}
"""

SHIPPED = """
/* The absolute paths of everything this app ships. Used to keep the
   runtime cache to those files alone: anything else the reader fetches
   is hers to save or not, and is never stored behind her back. */
var SHIPPED = PRECACHE.map(function (u) {
  return new URL(u, self.location.href).pathname;
});
"""

NETWORK_FIRST = """
/* Files that must be the server's copy when there is a server --
   a catalogue, an index -- and the saved copy when there is not. */
var NETWORK_FIRST = %(paths)s.map(function (u) {
  return new URL(u, self.location.href).pathname;
});
"""

FETCH_HEAD = """
self.addEventListener('fetch', function (event) {
  var req = event.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   /* never cross-origin */
"""

FETCH_TAIL = """
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      })['catch'](function () {
        return cachedMatch(req).then(function (hit) {
          if (hit) return hit;
%(navigate_fallback)s
        });
      })
    );
    return;
  }
%(network_first)s
  event.respondWith(
    cachedMatch(req).then(function (hit) {
%(on_hit)s
      return fetch(req).then(function (res) {
        if (res && res.status === 200 && res.type === 'basic'%(runtime_guard)s) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      });
    })%(offline)s
  );
});
"""

FALLBACK_REDIRECT = """\
          /* A page that was never cached, with no network to fetch it.
             Answering with the home page's HTML would render it under
             the URL that was asked for, where every relative link and
             asset resolves one directory too deep -- an unstyled page
             with a dead menu. Redirecting instead lands the reader on
             the real home page, which is cached. */
          return Response.redirect(self.registration.scope, 302);"""

FALLBACK_SHELL = """\
          /* Nothing cached under this URL, and no network to fetch it.
             This app answers every navigation from one shell, so that
             is the answer here too. */
          return cachedMatch('%(shell)s')%(or_home)s;"""

OR_HOME = """.then(function (shell) {
            return shell || cachedMatch('./');
          })"""

NETWORK_FIRST_BLOCK = """
  if (NETWORK_FIRST.indexOf(url.pathname) >= 0) {
    event.respondWith(
      fetch(req).then(function (res) {
        if (res && res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      })['catch'](function () {
        return cachedMatch(req).then(function (hit) {
          return hit || Response.error();
        });
      })
    );
    return;
  }
"""

ON_HIT_PLAIN = """\
      if (hit) return hit;"""

ON_HIT_RANGE = """\
      if (hit) {
        var range = req.headers.get('range');
        return range ? slice(hit.clone(), range) : hit;
      }"""

OFFLINE_TAIL = """['catch'](function () {
      return cachedMatch(req).then(function (hit) {
        return hit || new Response(%(text)s, {
          status: 503,
          headers: { 'Content-Type': 'text/plain; charset=utf-8' }
        });
      });
    })"""


def js_list(items, indent="  ", quote="'"):
    return "\n".join("%s%s%s%s%s" % (indent, quote, x, quote,
                                     "," if i < len(items) - 1 else "")
                     for i, x in enumerate(items))


def js_inline(items):
    return "[" + ", ".join("'%s'" % x for x in items) + "]"


def render(cfg, files, hashes, paths):
    """The whole worker, as text."""
    note = cfg["note"].strip()
    if note:
        note = "\n".join("   " + line if line else "" for line in
                         note.splitlines()) + "\n"

    text = HEADER % {
        "note": note,
        "cache": cache_name(cfg, files, hashes),
        "prefix": cfg["prefix"],
        "keep": js_inline(cfg["keep_caches"]),
        "ignore_search": "true" if cfg["ignore_search"] else "false",
        "precache": js_list(files, quote='"'),
        "hashes": js_list(hashes),
    }
    text += INSTALL % {"hash_len": HASH_LEN, "hash_bytes": HASH_LEN // 2}
    if cfg["range_support"]:
        text += RANGE
    if paths:
        text += PASSTHROUGH % {"from_file": cfg["passthrough_from"]["file"],
                               "paths": js_list(paths)}
    if cfg["runtime_cache"] == "precache":
        text += SHIPPED
    if cfg["network_first"]:
        text += NETWORK_FIRST % {"paths": js_inline(cfg["network_first"])}

    text += FETCH_HEAD
    if paths:
        text += "\n  if (isPassthrough(url)) return;\n"

    fallback = cfg["navigate_fallback"]
    text += FETCH_TAIL % {
        "navigate_fallback": (
            FALLBACK_REDIRECT if fallback == "redirect"
            else FALLBACK_SHELL % {
                "shell": fallback["shell"],
                "or_home": "" if fallback["shell"] == "./" else OR_HOME,
            }),
        "network_first": NETWORK_FIRST_BLOCK if cfg["network_first"] else "",
        "on_hit": ON_HIT_RANGE if cfg["range_support"] else ON_HIT_PLAIN,
        "runtime_guard": ("" if cfg["runtime_cache"] == "any"
                          else "\n            && SHIPPED.indexOf(url.pathname) >= 0"),
        "offline": (OFFLINE_TAIL % {"text": json.dumps(cfg["offline_text"])}
                    if cfg["offline_text"] else ""),
    }
    return text


def cache_name(cfg, files, hashes):
    """The prefix, then a content hash of everything that ships.

    The config is deliberately not part of it. A change to this app's
    behaviour changes sw.js, which is what makes the browser reinstall the
    worker; it does not change what the files are, so the install can reuse
    every entry of the existing cache and download nothing.
    """
    h = hashlib.sha256()
    for path, digest in zip(files, hashes):
        h.update(("%s\0%s\0" % (path, digest)).encode("utf-8"))
    return "%s%s" % (cfg["prefix"], h.hexdigest()[:HASH_LEN])


# ------------------------------------------------------------------ the guard


def assert_invariant(text, cfg):
    """Refuse to write a worker that cannot keep its hands off a sibling.

    This is the one failure in this script that must never reach a file.
    Whatever anybody does to the template, a worker without the prefix guard
    is not written: the build fails instead.
    """
    needed = [
        "var PREFIX = '%s';" % cfg["prefix"],
        "k.indexOf(PREFIX) === 0 ? caches['delete'](k) : null;",
        "if (k === CACHE || KEEP.indexOf(k) >= 0) return null;",
    ]
    missing = [n for n in needed if n not in text]
    if missing:
        die("the generated worker is missing the prefix guard (%s) -- "
            "refusing to write it" % "; ".join(missing))
    for name in cfg["keep_caches"]:
        if "'%s'" % name not in text:
            die("the generated worker does not keep %r" % name)


# ------------------------------------------------------------------- plumbing


def warn(message):
    print("build-sw: %s" % message, file=sys.stderr)


def die(message):
    print("build-sw: %s" % message, file=sys.stderr)
    raise SystemExit(1)


def main(argv):
    check = "--check" in argv
    listing = "--list" in argv

    cfg = load_config()
    files, from_git = shipped_files()
    kept = select(files, cfg["precache"])
    if not kept:
        die("the precache rules match nothing -- has the site been built?")

    hashes = [file_hash(ROOT / p) for p in kept]
    # "./" is the home page under the name the browser asks for first; it is
    # the same bytes as index.html, which is what the server answers with.
    home = dict(zip(kept, hashes)).get("index.html", "")
    entries = ["./"] + kept
    digests = [home] + hashes

    if listing:
        for path, digest in zip(entries, digests):
            print("%s  %s" % (digest or "-" * HASH_LEN, path))
        print("%d entries" % len(entries), file=sys.stderr)
        return 0

    paths = passthrough(cfg)
    text = render(cfg, entries, digests, paths)
    assert_invariant(text, cfg)

    if check:
        problems = []

        stamped = engine_hash()
        if stamped != ENGINE_SHA256:
            problems.append(
                "scripts/build-sw.py has been edited in this repository: it "
                "no longer matches the authoritative copy in the hub "
                "(%s, expected %s). Either revert it, or make the change in "
                "shamsfelfel.github.io/scripts/build-sw.py and re-run "
                "scripts/vendor-sw.py there to copy it out to every repo."
                % (stamped[:12], ENGINE_SHA256[:12]))

        spec = spec_hash()
        if spec is not None and spec != SPEC_SHA256:
            problems.append(
                "%s has been edited in this repository: the invariant suite "
                "is shared unchanged by every app (%s, expected %s). Make the "
                "change in the hub's copy and re-run scripts/vendor-sw.py "
                "there." % (SPEC, spec[:12], SPEC_SHA256[:12]))

        if not from_git:
            problems.append(
                "the precache list could not be read from git, so it cannot "
                "be checked against what is committed")

        if not TARGET.exists():
            problems.append("there is no sw.js -- run this script without --check")
        else:
            current = TARGET.read_text(encoding="utf-8")
            if current != text:
                listed = [x for x in re.findall(r'^  "([^"]+)",?$', current, re.M)
                          if x != "./"]
                missing = sorted(set(kept) - set(listed))
                gone = sorted(set(listed) - set(kept))
                if missing:
                    problems.append("sw.js does not precache: %s"
                                    % ", ".join(missing))
                if gone:
                    problems.append(
                        "sw.js precaches files that do not ship (not committed, "
                        "or deleted): %s" % ", ".join(gone))
                old = re.search(r"var CACHE = '([^']+)'", current)
                fresh = cache_name(cfg, entries, digests)
                if old and old.group(1) != fresh and not missing and not gone:
                    problems.append(
                        "a file that ships has changed since sw.js was written "
                        "(%s, now %s)" % (old.group(1), fresh))
                if not missing and not gone and (not old or old.group(1) == fresh):
                    problems.append(
                        "sw.js differs from what sw.config.json and this tree "
                        "would produce")

        if problems:
            for p in problems:
                print("build-sw: %s" % p, file=sys.stderr)
            return 1

        print("sw.js is in step: %d entries under %s, engine %s"
              % (len(entries), cfg["prefix"], ENGINE_SHA256[:12]))
        return 0

    unchanged = TARGET.exists() and TARGET.read_text(encoding="utf-8") == text
    if not unchanged:
        TARGET.write_text(text, encoding="utf-8", newline="\n")
    print("%s sw.js -- %d entries, cache %s"
          % ("unchanged" if unchanged else "wrote", len(entries),
             cache_name(cfg, entries, digests)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
