import { useEffect, useState } from "react";
import { Box, Container, Paper, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import GestureMapping from "../components/GestureMapping";
import SessionCamera from "../components/SessionCamera";
import sessionBridge from "../services/sessionBridge";
import type { SavedGestureSummary } from "../types/calibrate";
import { ROUTES } from "../utils/constants";
import styles from "../styles/session.module.css";

const Session = () => {
  const navigate = useNavigate();
  const [loadedGestures, setLoadedGestures] = useState<SavedGestureSummary[]>([]);
  const [gestureLoadError, setGestureLoadError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const loadSessionGestures = async () => {
      try {
        const gestures = await sessionBridge.getLoadedSessionGestures();

        if (!active) {
          return;
        }
  
        setLoadedGestures(gestures);
        setGestureLoadError(null);
      } catch (error) {
        if (!active) {
          return;
        }

        setLoadedGestures([]);
        setGestureLoadError(error instanceof Error ? error.message : "Unable to load session gestures");
      }
    };

    void loadSessionGestures();

    return () => {
      active = false;
    };
  }, []);

  const handleCalibrateNewGesture = () => {
    navigate(ROUTES.calibrate);
  };

  return (
    <Container maxWidth="xl" className={styles.container}>
      <Paper className={styles.paper}>
        <Box className={styles.header}>
          <Typography variant="h4" component="h1" className={styles.title}>
            Session Dashboard - Patient A
          </Typography>
          <Typography className={styles.subtitle}>
            Step 4 of 4: Complete Calibration
          </Typography>
          <Box className={styles.progressTrack} aria-hidden="true">
            {[0, 1, 2, 3].map((segment) => (
              <span key={segment} className={styles.progressSegment} />
            ))}
          </Box>
        </Box>

        <Box className={styles.dashboardGrid}>
          <SessionCamera />
          <GestureMapping gestures={loadedGestures} errorMessage={gestureLoadError} onCalibrateNewGesture={handleCalibrateNewGesture} />
        </Box>
      </Paper>
    </Container>
  );
};

export default Session;
