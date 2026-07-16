from __future__ import annotations

import argparse
import os
import signal
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
FRONTEND_URL = "http://127.0.0.1:5173"
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = "8000"
MACOS_APP_BINARY = ROOT / "dist" / "Human Controller.app" / "Contents" / "MacOS" / "Human Controller"
# This supervisor script is the "one command local preview" workflow.
# It keeps the frontend dev server and desktop app running together so team
# members can test the integrated experience without starting each piece by hand.
PROCESS_PATTERNS = [
    "Human Controller",
    "app.main",
    "backend.dev_server",
    "vite --host 127.0.0.1 --port 5173",
    "preview_local.py",
    "run_app.py",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Run the integrated local preview flow.")
    parser.add_argument("--log-fe", action="store_true", help="Show frontend logs.")
    parser.add_argument("--log-app", action="store_true", help="Show desktop app logs.")
    parser.add_argument("--log-be", action="store_true", help="Show backend logs.")
    parser.add_argument("--log-all", action="store_true", help="Show all logs.")
    return parser.parse_args()


class ManagedProcess:
    def __init__(self, name, command, cwd=None, env=None, stream_logs=False):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env
        self.stream_logs = stream_logs
        self.process = None
        self.tail = deque(maxlen=60)
        self.thread = None

    def start(self):
        popen_options = {}
        if os.name == "nt":
            # Keep each service in its own process group so Ctrl+C is handled by
            # this supervisor and shutdown can clean up the complete child tree.
            popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        self.process = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            env=self.env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            **popen_options,
        )
        self.thread = threading.Thread(target=self._read_output, daemon=True)
        self.thread.start()

    def terminate(self):
        if self.process is None or self.process.poll() is not None:
            return

        if os.name == "nt":
            # npm and the desktop app both spawn child processes on Windows.
            # taskkill /T ensures Vite, Qt, and their helpers close as one tree.
            subprocess.run(
                ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)

    def _read_output(self):
        if self.process is None or self.process.stdout is None:
            return

        for line in self.process.stdout:
            cleaned = line.rstrip()
            if cleaned:
                self.tail.append(cleaned)
                if self.stream_logs:
                    print(f"[{self.name}] {cleaned}", flush=True)


def wait_for_url(url, process, timeout=30):
    deadline = time.time() + timeout

    while time.time() < deadline:
        if process.process is not None and process.process.poll() is not None:
            raise RuntimeError(f"{process.name} exited before becoming ready.")

        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status < 500:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)

    raise RuntimeError(f"Timed out waiting for {url}.")


def format_tail(process):
    if not process.tail:
        return f"No {process.name} logs captured."
    return "\n".join(process.tail)


def resolve_desktop_command():
    if sys.platform == "darwin":
        # On macOS we deliberately launch the packaged app bundle because camera
        # permissions are tied to that bundle identity, not to `python -m app.main`.
        if not MACOS_APP_BINARY.exists():
            raise RuntimeError(
                "macOS local preview requires the packaged app bundle for camera permissions.\n"
                "Run `make macos-app` once, then retry `make preview-local`."
            )
        return [str(MACOS_APP_BINARY)]

    return [sys.executable, "-m", "app.main"]


def resolve_backend_runner():
    # Virtual environments use Scripts/python.exe on Windows and bin/python on
    # Unix. Passing the matching interpreter keeps backend reload dependencies
    # consistent with the desktop app's environment.
    candidates = (
        ROOT / ".venv" / "Scripts" / "python.exe",
        ROOT / ".venv" / "bin" / "python",
    )
    for venv_python in candidates:
        if venv_python.exists():
            return str(venv_python)

    return sys.executable


def cleanup_orphan_processes():
    if os.name == "nt":
        return

    for pattern in PROCESS_PATTERNS:
        subprocess.run(
            ["pkill", "-f", pattern],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def main():
    args = parse_args()
    if args.log_all:
        args.log_fe = True
        args.log_app = True
        args.log_be = True

    # npm is a .cmd launcher on Windows; Popen needs that executable rather than
    # relying on shell command resolution.
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if npm is None:
        print("Could not find npm. Install Node.js and ensure npm is on PATH.", file=sys.stderr)
        return 1

    frontend = ManagedProcess(
        "frontend",
        [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
        cwd=str(FRONTEND_DIR),
        stream_logs=args.log_fe,
        env=os.environ.copy(),
    )

    desktop_env = os.environ.copy()
    desktop_env.update(
        {
            "HUMAN_CONTROLLER_FRONTEND_URL": FRONTEND_URL,
            "HUMAN_CONTROLLER_BACKEND_AUTOSTART": "1",
            "HUMAN_CONTROLLER_BACKEND_HOST": BACKEND_HOST,
            "HUMAN_CONTROLLER_BACKEND_PORT": BACKEND_PORT,
            "HUMAN_CONTROLLER_BACKEND_RELOAD": "1",
            "HUMAN_CONTROLLER_BACKEND_RUNNER": resolve_backend_runner(),
            "HUMAN_CONTROLLER_PROJECT_ROOT": str(ROOT),
            "HUMAN_CONTROLLER_LOG_BE": "1" if args.log_be else "0",
        }
    )
    # These env vars tell the desktop app to load the live Vite URL instead of
    # bundled frontend files, and to spin up the lightweight preview backend.
    desktop = ManagedProcess(
        "app",
        resolve_desktop_command(),
        cwd=str(ROOT),
        stream_logs=args.log_app,
        env=desktop_env,
    )

    processes = [frontend, desktop]
    shutting_down = False

    def shutdown(*_args):
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        for process in reversed(processes):
            process.terminate()
        cleanup_orphan_processes()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        print("Starting frontend preview...", flush=True)
        frontend.start()
        wait_for_url(FRONTEND_URL, frontend)

        print("Starting desktop app...", flush=True)
        desktop.start()

        while True:
            if frontend.process is not None and frontend.process.poll() is not None:
                raise RuntimeError(f"Frontend exited unexpectedly.\n{format_tail(frontend)}")
            if desktop.process is not None and desktop.process.poll() is not None:
                raise RuntimeError(f"Desktop app exited unexpectedly.\n{format_tail(desktop)}")
            time.sleep(0.5)
    except RuntimeError as error:
        print(str(error), file=sys.stderr, flush=True)
        if desktop.tail and not args.log_app:
            print(format_tail(desktop), file=sys.stderr, flush=True)
        if frontend.tail and not args.log_fe:
            print(format_tail(frontend), file=sys.stderr, flush=True)
        shutdown()
        return 1
    finally:
        shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
