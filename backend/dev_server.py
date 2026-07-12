from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            self.send_response(404)
            self.end_headers()
            return

        body = json.dumps({"ok": True, "service": "dev-backend"}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        print(format % args, flush=True)


class DevThreadingHTTPServer(ThreadingHTTPServer):
    # SO_REUSEADDR permits multiple listeners on the same port on Windows.
    # Disable it there so an orphan is reported as a port conflict instead of
    # intermittently receiving requests intended for the new preview backend.
    allow_reuse_address = os.name != "nt"


def main():
    host = os.environ.get("HUMAN_CONTROLLER_BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("HUMAN_CONTROLLER_BACKEND_PORT", "8000"))
    server = DevThreadingHTTPServer((host, port), Handler)
    print(f"dev backend listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
