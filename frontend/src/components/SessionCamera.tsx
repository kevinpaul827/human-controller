import { Box, Button, Paper, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import SessionCameraErrorModal from "./modals/SessionCameraErrorModal";
import sessionBridge from "../services/sessionBridge";
import styles from "../styles/session.module.css";
import type { SessionStatusEvent, SessionState } from "../types/session";

// FIXME: implement a real help page if needed
const CAMERA_HELP_URL = "https://support.google.com/chrome/answer/2693767";

const SessionCamera = () => {
  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [errorEvent, setErrorEvent] = useState<SessionStatusEvent | null>(null);

  useEffect(() => {
    const unsubscribe = sessionBridge.onSessionStatus((event) => {
      if (event.state === "error") {
        setSessionState("idle");
        setErrorEvent(event);
        return;
      }

      setErrorEvent(null);
      setSessionState(event.state);
    });

    return unsubscribe;
  }, []);

  const handleStartSession = async () => {
    setErrorEvent(null);
    try {
      await sessionBridge.startSession();
    } catch (error) {
      setSessionState("idle");
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
      await sessionBridge.stopSession();
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to stop the desktop-managed session.",
      });
    }
  };

  const handleConfigure = () => {
    window.open(CAMERA_HELP_URL, "_blank", "noopener,noreferrer");
  };

  const isStarting = sessionState === "starting";
  const isLive = sessionState === "live";

  return (
    <>
      <Paper className={`${styles.dashboardPanel} ${styles.cameraPanel}`}>
        <Box className={styles.cameraHeader}>
          <Typography variant="subtitle1" className={styles.cameraStatus}>
            {isLive ? "Webcam Preview - Live" : "Webcam Preview - Ready"}
          </Typography>
        </Box>

        <Box className={styles.cameraFeed}>
          <Box className={styles.cameraFeedContent}>
            <Typography className={styles.cameraPlaceholder}>
              {isLive
                ? "Desktop session is live. Preview integration will be provided by PySide6."
                : "Idle camera feed"}
            </Typography>

            <Button
              variant="contained"
              size="large"
              className={styles.startButton}
              onClick={isLive ? handleStopSession : handleStartSession}
              disabled={isStarting}
            >
              {isStarting
                ? "Starting Session..."
                : isLive
                  ? "Stop Session"
                  : "Start Session"}
            </Button>
          </Box>
        </Box>
      </Paper>

      <SessionCameraErrorModal
        open={errorEvent !== null}
        message={errorEvent?.message}
        onCancel={() => setErrorEvent(null)}
        onConfigure={handleConfigure}
      />
    </>
  );
};

export default SessionCamera;
