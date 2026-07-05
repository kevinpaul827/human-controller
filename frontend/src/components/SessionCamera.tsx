import { Button, Paper, Typography } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import SessionCameraErrorModal from "./modals/SessionCameraErrorModal";
import sessionBridge from "../services/sessionBridge";
import styles from "../styles/session.module.css";
import type { SessionStatusEvent, SessionState } from "../types/session";

const SessionCamera = () => {
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [errorEvent, setErrorEvent] = useState<SessionStatusEvent | null>(null);
  const cameraPanelRef = useRef<HTMLDivElement | null>(null);
  const isLive = sessionState === "live";

  useEffect(() => {
    if (!isLive) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setElapsed((current) => Number((current + 0.1).toFixed(1)));
    }, 100);

    return () => window.clearInterval(intervalId);
  }, [isLive]);

  useEffect(() => {
    const panel = cameraPanelRef.current;

    if (!panel) {
      return;
    }

    let frameId = 0;

    const syncPreviewBounds = () => {
      frameId = 0;

      const rect = panel.getBoundingClientRect();

      void sessionBridge.updatePreviewBounds({
        left: rect.left,
        top: rect.top,
        width: rect.width,
        height: rect.height,
        devicePixelRatio: window.devicePixelRatio,
      });
    };

    const scheduleSync = () => {
      if (frameId !== 0) {
        return;
      }

      frameId = window.requestAnimationFrame(syncPreviewBounds);
    };

    scheduleSync();

    const resizeObserver = new ResizeObserver(() => {
      scheduleSync();
    });

    resizeObserver.observe(panel);
    window.addEventListener("resize", scheduleSync);
    window.addEventListener("scroll", scheduleSync, true);

    return () => {
      resizeObserver.disconnect();
      window.removeEventListener("resize", scheduleSync);
      window.removeEventListener("scroll", scheduleSync, true);

      if (frameId !== 0) {
        window.cancelAnimationFrame(frameId);
      }

      void sessionBridge.updatePreviewBounds({
        left: 0,
        top: 0,
        width: 0,
        height: 0,
        devicePixelRatio: window.devicePixelRatio,
      });
    };
  }, []);

  useEffect(() => {
    const unsubscribe = sessionBridge.onSessionStatus((event) => {
      if (event.state === "error") {
        setElapsed(0);
        setSessionState("idle");
        setErrorEvent(event);
        return;
      }

      if (event.state === "idle") {
        setElapsed(0);
      }
      setErrorEvent(null);
      setSessionState(event.state);
    });

    return unsubscribe;
  }, []);

  const handleStartSession = async () => {
    setErrorEvent(null);
    setElapsed(0);
    try {
      await sessionBridge.startSession();
      setSessionState("live");
    } catch (error) {
      setSessionState("error");
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to reach the desktop session bridge.",
      });
    }
  };

  const handleStopSession = async () => {
    try {
      setElapsed(0);
      await sessionBridge.stopSession();
      setSessionState("idle");
    } catch (error) {
      setSessionState("error");
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to stop the desktop-managed session.",
      });
    }
  };

  const handleConfigure = async () => {
    try {
      await sessionBridge.openCameraSettings();
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to open desktop camera settings.",
      });
    }
  };

  const handleCloseError = async () => {
    try {
      await handleStopSession();
    } finally {
      setErrorEvent(null);
    }
  };

  return (
    <>
      <div className={styles.cameraSection}>
        <Paper
          ref={cameraPanelRef}
          className={`${styles.dashboardPanel} ${styles.cameraPanel}`}
        >
          <div className={styles.cameraFeed}>
            <div
              className={`${styles.cameraHeader} ${isLive ? styles.recordingBoxActive : ""}`}
            >
              <Typography className={styles.recordingTitle}>
                {isLive ? "● RECORDING" : "Camera idle"}
              </Typography>
              <Typography className={styles.recordingCaption}>
                {isLive
                  ? `Session camera is active (${elapsed.toFixed(1)}s elapsed)`
                  : "Press Start Session to begin the live camera session."}
              </Typography>
            </div>
            <div className={styles.cameraFeedContent}>
              <Typography className={styles.cameraPlaceholder}>
                {isLive
                  ? "Desktop camera preview is being rendered by the PySide6 app."
                  : "Idle camera feed"}
              </Typography>
            </div>
          </div>
        </Paper>
        <div className={styles.cameraControls}>
          <Button
            variant="contained"
            size="large"
            className={styles.startButton}
            onClick={isLive ? handleStopSession : handleStartSession}
          >
            {isLive ? "Stop Session" : "Start Session"}
          </Button>
        </div>
      </div>

      <SessionCameraErrorModal
        open={errorEvent !== null}
        message={errorEvent?.message}
        onCancel={handleCloseError}
        onConfigure={handleConfigure}
      />
    </>
  );
};

export default SessionCamera;
