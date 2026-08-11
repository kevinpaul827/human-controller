from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
POLL_INTERVAL_SECONDS = 0.75

# This helper watches backend Python files during local preview.
# When someone edits backend code, it restarts the preview backend so the
# desktop app can pick up the change without rerunning the full preview flow.

def backend_command():
    return [sys.executable, "-m", "devtools.backend_health_server"]


def snapshot_backend_files():
    # We keep the reload logic simple for students: if any backend `.py` file
    # timestamp changes, restart the preview backend process.
    tracked = {}
    for path in BACKEND_DIR.rglob("*.py"):
        try:
            tracked[path] = path.stat().st_mtime_ns
        except FileNotFoundError:
            continue
    return tracked


def start_backend(env):
    print("[backend-reloader] starting backend helper", flush=True)
    return subprocess.Popen(
        backend_command(),
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=None,
        stderr=None,
    )


def stop_backend(process):
    if process.poll() is not None:
        return

    if os.name == "nt":
        # The venv Python launcher may create a separate interpreter process on
        # Windows. Kill its full tree so reloads do not orphan backend servers.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def main():
    env = dict(os.environ)
    child = start_backend(env)
    previous = snapshot_backend_files()
    stopped = False

    def shutdown(*_args):
        nonlocal stopped
        if stopped:
            return
        stopped = True
        stop_backend(child)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while not stopped:
            if child.poll() is not None:
                print("[backend-reloader] backend exited, restarting...", flush=True)
                child = start_backend(env)
                previous = snapshot_backend_files()

            current = snapshot_backend_files()
            if current != previous:
                print("[backend-reloader] backend change detected, restarting...", flush=True)
                stop_backend(child)
                child = start_backend(env)
                previous = current

            time.sleep(POLL_INTERVAL_SECONDS)
    finally:
        shutdown()


if __name__ == "__main__":
    main()
