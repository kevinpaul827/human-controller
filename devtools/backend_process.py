from __future__ import annotations

import http.client
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Preview-helper process contract; these are not application-wide settings.
BACKEND_HELPER_FLAG = "--backend-helper"
BACKEND_RELOAD_FLAG = "HUMAN_CONTROLLER_BACKEND_RELOAD"
BACKEND_RUNNER_ENV = "HUMAN_CONTROLLER_BACKEND_RUNNER"
PROJECT_ROOT_ENV = "HUMAN_CONTROLLER_PROJECT_ROOT"
BACKEND_RELOADER_PATH = Path("scripts") / "run_backend_dev.py"

# This module is the desktop app's small process manager for the preview/backend
# helper. Its job is to start the helper, wait until `/health` responds, and
# stop the helper cleanly when the app closes.


def build_backend_command(env: dict[str, str] | None = None):
    env = env or os.environ
    if env.get(BACKEND_RELOAD_FLAG) == "1":
        runner = env.get(BACKEND_RUNNER_ENV)
        project_root = env.get(PROJECT_ROOT_ENV)
        if runner and project_root:
            return [runner, str(Path(project_root) / BACKEND_RELOADER_PATH)]

    if getattr(sys, "frozen", False):
        return [sys.executable, BACKEND_HELPER_FLAG]

    return [sys.executable, "-m", "devtools.backend_health_server"]


class BackendProcessManager:
    def __init__(self):
        self.host = os.environ.get("HUMAN_CONTROLLER_BACKEND_HOST", "127.0.0.1")
        self.port = int(os.environ.get("HUMAN_CONTROLLER_BACKEND_PORT", "8000"))
        self.health_url = f"http://{self.host}:{self.port}/health"
        self.log_backend = os.environ.get("HUMAN_CONTROLLER_LOG_BE") == "1"
        self.process = None
        self._tail = deque(maxlen=40)
        self._threads: list[threading.Thread] = []

    def start(self):
        if self.process is not None:
            return

        env = {
            "HUMAN_CONTROLLER_BACKEND_HOST": self.host,
            "HUMAN_CONTROLLER_BACKEND_PORT": str(self.port),
        }
        full_env = {**os.environ, **env}

        self.process = subprocess.Popen(
            build_backend_command(full_env),
            cwd=str(Path(full_env.get(PROJECT_ROOT_ENV, ROOT))),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=full_env,
        )
        self._threads = [
            threading.Thread(
                target=self._read_output,
                args=(self.process.stdout,),
                daemon=True,
            )
        ]
        for thread in self._threads:
            thread.start()

        try:
            self._wait_until_healthy()
        except Exception:
            self.stop()
            raise

    def stop(self):
        if self.process is None:
            return

        if self.process.poll() is None:
            if os.name == "nt":
                # Windows does not propagate terminate() from the Python/venv
                # launcher to its children. /T removes the reloader and backend
                # server together so closing the app does not leave port 8000 in use.
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

        self.process = None

    def _read_output(self, stream):
        if stream is None:
            return

        for line in stream:
            cleaned = line.rstrip()
            if cleaned:
                self._tail.append(cleaned)
                if self.log_backend:
                    print(f"[backend] {cleaned}", flush=True)

    def _wait_until_healthy(self):
        deadline = time.time() + 10

        while time.time() < deadline:
            if self.process is None:
                raise RuntimeError("Backend process was not started.")

            if self.process.poll() is not None:
                tail = "\n".join(self._tail) or "No backend logs captured."
                raise RuntimeError(f"Backend process exited early.\n{tail}")

            try:
                with urllib.request.urlopen(self.health_url, timeout=0.5) as response:
                    if response.status == 200:
                        return
            except (
                urllib.error.URLError,
                http.client.RemoteDisconnected,
                TimeoutError,
            ):
                # On Windows a backend that is still starting or restarting can
                # accept the connection before it can return /health. Treat that
                # short disconnect as a retryable readiness state.
                time.sleep(0.2)

        self.stop()
        tail = "\n".join(self._tail) or "No backend logs captured."
        raise RuntimeError(f"Backend failed health check at {self.health_url}.\n{tail}")
