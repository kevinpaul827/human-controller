import { Button, Paper, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import useDesktopCameraPreview from "../hooks/useDesktopCameraPreview";
import SessionCameraErrorModal from "./modals/SessionCameraErrorModal";
import sessionBridge from "../services/sessionBridge";
import styles from "../styles/session.module.css";
import type { SessionStatusEvent, SessionState } from "../types/session";

const SessionCamera = () => {
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [errorEvent, setErrorEvent] = useState<SessionStatusEvent | null>(null);
  const isLive = sessionState === "live";
  const { elapsed, previewAspectRatio, previewViewportRef, setElapsed } =
    useDesktopCameraPreview({
      bridge: sessionBridge,
      isLive,
    });

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
        <Paper className={`${styles.dashboardPanel} ${styles.cameraPanel}`}>
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
              <div
                ref={previewViewportRef}
                className={styles.cameraViewport}
                style={{ aspectRatio: String(previewAspectRatio) }}
              >
                {!isLive ? (
                  <Typography className={styles.cameraPlaceholder}>
                    Idle camera feed
                  </Typography>
                ) : null}
              </div>
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
