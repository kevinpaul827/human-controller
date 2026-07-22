import { useEffect, useState } from "react";
import { Box, Container, Paper, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import GestureMapping from "../components/GestureMapping";
import SessionCamera from "../components/SessionCamera";
import useActiveProfile from "../hooks/useActiveProfile";
import sessionBridge from "../services/sessionBridge";
import type { SessionGestureMapping } from "../types/session";
import { ROUTES } from "../utils/constants";
import styles from "../styles/session.module.css";

const Session = () => {
  const navigate = useNavigate();
  const { activeProfile } = useActiveProfile();
  const [loadedGestures, setLoadedGestures] = useState<SessionGestureMapping[]>(
    [],
  );
  const [gestureLoadError, setGestureLoadError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const loadSessionGestures = async () => {
      if (!activeProfile) {
        setLoadedGestures([]);
        setGestureLoadError(null);
        return;
      }

      try {
        const profileData = await sessionBridge.loadProfile(
          activeProfile.patientId,
        );

        if (!active) {
          return;
        }

        setLoadedGestures(profileData.gestures);

        if (profileData.gestures.length === 0) {
          setGestureLoadError(
            "This profile has no usable gesture key bindings yet. Open Profiles and assign calibrated movements first.",
          );
        } else if ((profileData.missingGestureIds?.length ?? 0) > 0) {
          setGestureLoadError(
            `Loaded ${profileData.gestures.length} gesture(s). ${profileData.missingGestureIds?.length} bound gesture file(s) are missing from storage.`,
          );
        } else {
          setGestureLoadError(null);
        }
      } catch (error) {
        if (!active) {
          return;
        }

        setLoadedGestures([]);
        setGestureLoadError(
          error instanceof Error
            ? error.message
            : "Unable to load session gestures",
        );
      }
    };

    void loadSessionGestures();

    return () => {
      active = false;
      void sessionBridge.stopSession().catch(() => {});
    };
  }, [activeProfile]);

  const handleCalibrateNewGesture = () => {
    navigate(ROUTES.calibrate);
  };

  const handleGesturesLoaded = (gestures: SessionGestureMapping[]) => {
    setLoadedGestures(gestures);
    if (!activeProfile) {
      setGestureLoadError(null);
      return;
    }

    setGestureLoadError(
      gestures.length === 0
        ? "This profile has no usable gesture key bindings yet. Open Profiles and assign calibrated movements first."
        : null,
    );
  };

  return (
    <Container maxWidth="xl" className={styles.container}>
      <Paper className={styles.paper}>
        <Box className={styles.header}>
          <Typography variant="h4" component="h1" className={styles.title}>
            Session Dashboard — {activeProfile?.patientName ?? "Unassigned"}
          </Typography>
          <Typography className={styles.subtitle}>
            Step 4 of 4: Complete Calibration
          </Typography>
          {!activeProfile ? (
            <Typography className={styles.profileHint}>
              Camera works without a profile. To load gesture key bindings,{" "}
              <button
                type="button"
                className={styles.profileHintLink}
                onClick={() => navigate(ROUTES.profiles)}
              >
                go to Profiles
              </button>
              .
            </Typography>
          ) : null}
          <Box className={styles.progressTrack} aria-hidden="true">
            {[0, 1, 2, 3].map((segment) => (
              <span key={segment} className={styles.progressSegment} />
            ))}
          </Box>
        </Box>

        <Box className={styles.dashboardGrid}>
          <SessionCamera
            patientId={activeProfile?.patientId}
            onGesturesLoaded={handleGesturesLoaded}
          />
          <GestureMapping
            gestures={loadedGestures}
            errorMessage={gestureLoadError}
            onCalibrateNewGesture={handleCalibrateNewGesture}
          />
        </Box>
      </Paper>
    </Container>
  );
};

export default Session;
