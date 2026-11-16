/**
 * The service-worker invariants, shared by every app on shamsfelfel.github.io.
 *
 * GENERATED: this file is byte-identical in all seven repositories. It is
 * maintained in shamsfelfel.github.io/e2e/ and copied out by
 * scripts/vendor-sw.py. Do not edit it in one repository -- the copy's hash
 * is checked, and an edit fails this suite.
 *
 * It reads `sw.config.json` for everything app-specific, so there is nothing
 * to adapt per repo: the prefix, the precache list, whether the app supports
 * ranged requests. Four of these tests exist because the bug they guard
 * against reached the live site.
 *
 *   - Seven apps share one GitHub Pages origin and Cache Storage is scoped to
 *     the origin, not the path. Four workers used to delete every cache that
 *     was not their own, which took the other six apps offline on every
 *     deployment. "leaves a sibling's caches alone" is the regression guard,
 *     and it is behavioural: it plants a cache and watches it survive.
 *
 *   - The precache list used to be read off the filesystem, which swept the
 *     author's uncommitted lesson files into it -- precache entries that 404
 *     for every reader. It now comes from git, and "everything it lists is
 *     actually served" checks that against the real server.
 *
 *   - ESL's content cache holds PDFs and audio the student chose to download
 *     over a metered connection. It must survive its own app's updates and
 *     every sibling's activation.
 *
 * One trap, which cost real debugging time on 4 November 2026: an offline
 * test must navigate to a DIFFERENT precached URL, never back to the URL the
 * page is already on. Navigating to the current URL is a reload, i.e. a
 * validating navigation, and Chromium fails one outright against an
 * emulated-down network without ever consulting the worker.
 */
const { test, expect } = require('@playwright/test');
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const CONFIG = JSON.parse(fs.readFileSync(path.join(ROOT, 'sw.config.json'), 'utf8'));
const PREFIX = CONFIG.prefix;
const KEEP = CONFIG.keep_caches || [];

/** The worker as it is on disk, which is the file the server hands out. */
function worker() {
  return fs.readFileSync(path.join(ROOT, 'sw.js'), 'utf8');
}

/** PRECACHE, read out of the generated file rather than recomputed. */
function precache() {
  const block = /var PRECACHE = \[([^\]]*)\]/.exec(worker());
  expect(block, 'sw.js has no PRECACHE list').not.toBeNull();
  return [...block[1].matchAll(/"([^"]+)"/g)].map((m) => m[1]);
}

/**
 * The page to start on, and a different precached page to prove the offline
 * claim with. Prefer one in a subdirectory: it is further from the start page
 * and exercises relative resolution, which is where a worker gets this wrong.
 */
function pages() {
  const html = precache().filter((u) => u.endsWith('.html'));
  /* Always start at "./", so the offline target below is never the URL the
     page is already on -- see the note at the top of this file. A page in a
     subdirectory is the better target where there is one: it is further from
     the start page and it exercises relative resolution, which is where a
     worker gets this wrong. */
  const deep = html.find((u) => u.includes('/'));
  return { start: './', target: deep || 'index.html' };
}

/** A precache entry as a path the test can navigate to. */
function at(entry) {
  return entry === './' ? '/' : '/' + entry;
}

/** Run the generator, whichever name python goes by here. */
function generator(...args) {
  let last;
  for (const exe of ['python', 'python3']) {
    try {
      return { ok: true, out: execFileSync(exe, ['scripts/build-sw.py', ...args],
        { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }) };
    } catch (err) {
      if (err.code === 'ENOENT') { last = err; continue; }
      return { ok: false, out: (err.stdout || '') + (err.stderr || '') };
    }
  }
  throw last;
}

/**
 * Poll a condition inside the page until it holds.
 *
 * Not `page.waitForFunction`: hand that an async predicate and it awaits the
 * promise exactly once and then resolves whatever the value was, false
 * included. So every wait built on one returns almost immediately and the
 * test that follows reads a half-installed worker -- which is how a suite
 * ends up green by luck. `page.evaluate` does await the promise and hand back
 * its value, so the loop lives out here.
 */
async function until(page, fn, arg, what, timeout = 60000) {
  const deadline = Date.now() + timeout;
  for (;;) {
    if (await page.evaluate(fn, arg)) return;
    if (Date.now() > deadline) throw new Error('timed out waiting until ' + what);
    await new Promise((r) => setTimeout(r, 150));
  }
}

async function workerReady(page) {
  await until(page, async () => {
    const reg = await navigator.serviceWorker.getRegistration();
    return !!(reg && reg.active && reg.active.state === 'activated'
              && navigator.serviceWorker.controller);
  }, null, 'the worker is activated and controlling this page', 30000);
}

/**
 * Wait until the precache is actually full, not merely started.
 *
 * A controlled page is not a filled cache, and "the home page is in there"
 * is not either: install adds entries one at a time, so under load a test
 * can read a cache that is a third full and conclude the app is broken. The
 * count is the signal -- every entry the worker lists, present.
 */
async function installed(page) {
  const want = precache().length;
  await until(page, async (a) => {
    let n = 0;
    for (const name of (await caches.keys()).filter((k) => k.startsWith(a.p))) {
      const cache = await caches.open(name);
      n += (await cache.keys()).length;
    }
    return n >= a.want;
  }, { p: PREFIX, want }, `all ${want} precache entries are in the cache`);
}

function names(page) {
  return page.evaluate(() => caches.keys());
}

/**
 * Make the app install and activate again, for real -- a deployment, as the
 * reader's browser sees one.
 *
 * Dropping the registration and reloading is what does it: the next load
 * re-registers from scratch, so install and activate both genuinely run.
 * Navigating to about:blank first is not decoration -- an unregistered
 * registration lives on while it still has a client, and `register()` from
 * the next page can then hand back the very same active worker: no install,
 * no activate, and a test that silently checks nothing.
 */
async function reinstall(page, start) {
  await page.evaluate(async () => {
    const reg = await navigator.serviceWorker.getRegistration();
    if (reg) await reg.unregister();
  });
  await page.goto('about:blank');
  await page.goto(at(start));
  await workerReady(page);
}

test.describe('the generator', () => {
  test('sw.js is in step with what this repository ships', () => {
    /* --check is where precache completeness lives: it lists what git says
       ships, renders the worker that list implies, and compares it to the
       file on disk. It also recomputes this copy of build-sw.py's own hash,
       so a vendored generator edited in place fails here -- with no hub
       checkout and no network. */
    const r = generator('--check');
    expect(r.ok, r.out).toBe(true);
    expect(r.out, r.out).toContain('in step');
  });

  test('everything it lists is actually served', async ({ request }) => {
    const listed = precache();
    expect(listed.length).toBeGreaterThan(0);
    expect(listed[0]).toBe('./');

    for (const url of listed) {
      const res = await request.get(url === './' ? '/' : '/' + url);
      expect(res.status(), `sw.js precaches ${url}, which the server does not have`)
        .toBe(200);
    }
  });

  test('its cache name is a content hash, so an unchanged build is a no-op', () => {
    const sw = worker();
    const name = /var CACHE = '([^']+)'/.exec(sw);
    expect(name, 'sw.js has no CACHE name').not.toBeNull();
    expect(name[1]).toMatch(new RegExp('^' + PREFIX + '[0-9a-f]{12}$'));

    /* A date or a counter in here would change the name, and the file's
       bytes, on every build -- and a browser reinstalls a worker when the
       file changes, re-fetching every entry with cache: 'reload'. For
       readers on metered connections a rebuild that changes nothing has to
       cost nothing. */
    expect(sw).not.toMatch(/CACHE = '[^']*20\d{6}/);
  });
});

test.describe('the prefix invariant', () => {
  test('the worker declares it and guards with it', () => {
    const sw = worker();
    expect(sw).toContain(`var PREFIX = '${PREFIX}';`);
    expect(sw).toContain("k.indexOf(PREFIX) === 0 ? caches['delete'](k) : null;");
    expect(sw).toContain('if (k === CACHE || KEEP.indexOf(k) >= 0) return null;');
    for (const name of KEEP) expect(sw).toContain(`'${name}'`);
  });

  test('it caches under its own prefix and creates nothing else', async ({ page }) => {
    const { start } = pages();
    await page.goto(at(start));
    await workerReady(page);
    await installed(page);

    const all = await names(page);
    expect(all.filter((n) => n.startsWith(PREFIX)).length).toBeGreaterThan(0);
    expect(all.filter((n) => !n.startsWith(PREFIX)),
      'this app created a cache outside its own prefix').toEqual([]);

    /* installed() above is the assertion that the precache filled: it waits
       for one cache entry per listed URL. The list is the claim, the cache
       is the fact. */
  });

  test("leaves a sibling's caches alone, and retires its own", async ({ page }) => {
    const { start } = pages();
    await page.goto(at(start));
    await workerReady(page);
    await installed(page);

    /* Two plants. The siblings must survive -- that is the bug. The stale
       cache under this app's own prefix must not, or the test would pass for
       an activate handler that deletes nothing at all. */
    const siblings = ['hub-', 'da-', 'oop-', 'la-', 'ps-', 'sqllab-', 'esl-']
      .filter((p) => p !== PREFIX).map((p) => p + 'planted0000');
    await page.evaluate(async (args) => {
      for (const name of args.siblings.concat([args.stale])) {
        const c = await caches.open(name);
        await c.put(new Request('/planted.txt'), new Response('planted'));
      }
    }, { siblings, stale: PREFIX + 'stale0000000' });

    await reinstall(page, start);

    /* Wait for the outcome rather than for a state: activate retires the
       stale cache inside its own waitUntil, and the only honest signal that
       it has finished is the cache being gone. If it never goes, this times
       out -- which is the right failure, because an activate handler that
       deletes nothing at all would otherwise pass the sibling check below. */
    await until(page,
      (stale) => caches.keys().then((all) => !all.includes(stale)),
      PREFIX + 'stale0000000',
      'this app has retired the superseded cache of its own', 30000);

    const after = await names(page);
    for (const name of siblings) {
      expect(after, `activate deleted ${name}, which belongs to another app`)
        .toContain(name);
    }
    /* And it left exactly one cache of its own: nothing stale kept, and
       nothing resurrected by a worker opening a cache it does not own. */
    expect(after.filter((n) => n.startsWith(PREFIX)))
      .toEqual([/var CACHE = '([^']+)'/.exec(worker())[1]]);
  });

  if (KEEP.length) {
    test('keeps the caches the page owns, across its own reinstall', async ({ page }) => {
      const { start } = pages();
      await page.goto(at(start));
      await workerReady(page);
      await installed(page);

      /* Stand in for a file the reader deliberately downloaded. It carries
         this app's prefix, so only the KEEP list saves it -- and it was
         paid for with data she may not have again. */
      await page.evaluate(async (kept) => {
        for (const name of kept) {
          const c = await caches.open(name);
          await c.put(new Request('/paid-for.pdf'), new Response('pdf'));
        }
      }, KEEP);

      await reinstall(page, start);
      await installed(page);

      for (const name of KEEP) {
        const held = await page.evaluate(async (n) => {
          const c = await caches.open(n);
          return (await c.keys()).length;
        }, name);
        expect(held, `${name} was emptied by an update`).toBe(1);
      }
    });
  }
});

test.describe('offline', () => {
  test('the app opens with the network off', async ({ page, context }) => {
    const { start, target } = pages();
    await page.goto(at(start));
    await workerReady(page);
    await installed(page);

    await context.setOffline(true);
    try {
      /* A different URL from the one we are on. See the note at the top. */
      const res = await page.goto(at(target));
      expect(res.status()).toBe(200);
      await expect(page.locator('body')).not.toBeEmpty();

      /* And its assets came out of the cache too, not just the HTML.
         Resolved against the worker's scope, not against the page: this page
         is in a subdirectory, and a relative fetch from here would ask for
         chapters/assets/... , which nothing has ever served. */
      const asset = precache().find((u) => /\.(css|js)$/.test(u));
      if (asset) {
        const ok = await page.evaluate(async (u) => {
          const reg = await navigator.serviceWorker.getRegistration();
          try { return (await fetch(new URL(u, reg.scope).href)).ok; }
          catch (e) { return false; }
        }, asset);
        expect(ok, `${asset} was not served from the cache`).toBe(true);
      }
    } finally {
      await context.setOffline(false);
    }
  });

  test('a URL it never cached does not become a browser error', async ({ page, context }) => {
    const { start } = pages();
    await page.goto(at(start));
    await workerReady(page);
    await installed(page);

    await context.setOffline(true);
    try {
      /* Either the shell answers or the worker redirects to the real home
         page; what must not happen is the browser's own failure page. */
      const res = await page.goto('/no-such-page-' + Date.now() + '.html')
        .catch(() => null);
      expect(res, 'offline navigation to an unknown page gave a network error')
        .not.toBeNull();
      await expect(page.locator('body')).not.toBeEmpty();
    } finally {
      await context.setOffline(false);
    }
  });
});

test.describe('by construction', () => {
  test('nothing is loaded from another origin', async ({ page }) => {
    const { start } = pages();
    const foreign = [];
    page.on('request', (r) => {
      const u = new URL(r.url());
      if (u.hostname !== 'localhost' && u.hostname !== '127.0.0.1'
          && u.protocol !== 'data:' && u.protocol !== 'blob:') {
        foreign.push(r.url());
      }
    });
    await page.goto(at(start));
    await workerReady(page);
    expect(foreign).toEqual([]);
  });
});

if (CONFIG.range_support) {
  test.describe('ranged requests', () => {
    test('a cached file answers a byte range with a real 206', async ({ page }) => {
      const { start } = pages();
      await page.goto(at(start));
      await workerReady(page);
      await installed(page);

      const file = precache().find((u) => /\.(js|css|mp3)$/.test(u));
      expect(file, 'nothing precached to slice').toBeTruthy();

      /* A phone's audio player asks for ranges when the listener seeks. A
         cached response handed back whole answers 200, and players treat
         that as unseekable or refuse it outright. */
      const got = await page.evaluate(async (u) => {
        const res = await fetch(u, { headers: { Range: 'bytes=0-9' } });
        const body = await res.arrayBuffer();
        return {
          status: res.status,
          range: res.headers.get('Content-Range'),
          accept: res.headers.get('Accept-Ranges'),
          length: body.byteLength,
        };
      }, file);

      expect(got.status).toBe(206);
      expect(got.length).toBe(10);
      expect(got.range).toMatch(/^bytes 0-9\/\d+$/);
      expect(got.accept).toBe('bytes');
    });
  });
}
