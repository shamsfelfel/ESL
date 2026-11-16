#!/usr/bin/env python3
"""Serve the course over http, for authoring and for the test suite.

    python scripts/dev-server.py            # http://127.0.0.1:8088/
    python scripts/dev-server.py 8090
    python scripts/dev-server.py -v         # log every request

Opening index.html from disk is not enough to work on this app: a service
worker only exists in a secure context, and file:// is not one, so offline --
the whole point of the course -- cannot be tried or tested without a server.
localhost does count as a secure context.

`Cache-Control: no-store` on every response, so an edited page, script or
catalogue shows up on a plain reload instead of being served from the
browser's HTTP cache. That is also what the suite wants: it has to prove the
app opens with the network off out of the service worker's cache, which an
HTTP cache hit would hide.
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERBOSE = "-v" in sys.argv or "--verbose" in sys.argv


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Quiet unless asked: saving the shell is a dozen requests and the
        # suite makes hundreds, which would bury the report printed beside it.
        if VERBOSE:
            sys.stderr.write("  %s\n" % (fmt % args))

    def log_error(self, fmt, *args):
        # A browser that navigates away mid-response leaves an aborted
        # connection behind. Normal, and not this server's problem.
        if VERBOSE:
            sys.stderr.write("  %s\n" % (fmt % args))


class Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, request, client_address):
        kind = sys.exc_info()[0]
        if kind in (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            return
        if VERBOSE:
            super().handle_error(request, client_address)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    port = int(args[0]) if args else 8088
    print("%s\nhttp://127.0.0.1:%d/  -- ctrl-c to stop" % (ROOT, port))
    # Threaded: the shell is a dozen files at once, and a lesson the student
    # saves is a dozen more, several megabytes of PDF and audio.
    Server(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
