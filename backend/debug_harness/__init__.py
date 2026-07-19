"""Debug harness — DEBUG / TESTING ONLY, not part of the production system.

A self-contained WebSocket server + static browser page for manually driving the
matching engine end-to-end (webcam -> BlazePose -> smoothing -> state / DTW
matching). It exists purely to eyeball and sanity-check the engine during
development.

It is deliberately kept separate from the real frontend and the production
persistence layer:

  - it does NOT import or touch ``ProfileManager`` (it uses its own throwaway
    JSON store under ``backend/debug_harness/data/``, which is gitignored), and
  - it is NOT wired into the React app; the only client is the standalone
    ``static/index.html`` page shipped here.

Run with::

    python -m backend.debug_harness      # serves http://localhost:8000
"""
