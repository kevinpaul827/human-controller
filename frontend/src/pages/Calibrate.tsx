import { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import CalibrationProgress from "../components/CalibrationProgress";
import SessionCameraErrorModal from "../components/modals/SessionCameraErrorModal";
import calibrateBridge from "../services/calibrateBridge";
import type {
  CalibrateState,
  CalibrateStatusEvent,
  CapturedRep,
} from "../types/calibrate";
import { ROUTES } from "../utils/constants";

const CALIBRATION_STEPS = [
  "Choose movement",
  "Align camera",
  "Record gesture",
  "Save mapping",
];

const LIVE_CHECKLIST = [
  "Center the patient so both shoulders and arms remain visible.",
  "Use the live preview to confirm the desktop overlay is aligned.",
  "Only begin capture once the patient can comfortably hold the final pose.",
];

const IDLE_CHECKLIST = [
  "Open the calibration camera to attach the desktop preview to this page.",
  "Check framing before recording so the target joints stay in shot.",
  "Use camera settings if permissions or device selection need attention.",
];

const formatRepAngles = (rep: CapturedRep) => {
  const joints = Object.entries(rep.angles);
  if (joints.length === 0) {
    return "No measurable joints captured yet.";
  }

  return joints
    .map(([joint, angle]) => `${joint} ${angle.toFixed(1)}°`)
    .join(" · ");
};

const Calibrate = () => {
  const navigate = useNavigate();
  const [calibrateState, setCalibrateState] = useState<CalibrateState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [errorEvent, setErrorEvent] = useState<CalibrateStatusEvent | null>(null);
  const [previewAspectRatio, setPreviewAspectRatio] = useState(4 / 3);
  const [gestureName, setGestureName] = useState("");
  const [repCount, setRepCount] = useState(0);
  const [capturedReps, setCapturedReps] = useState<CapturedRep[]>([]);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const previewViewportRef = useRef<HTMLDivElement | null>(null);
  const isLive = calibrateState === "live";
  const currentStep = isLive ? 3 : 2;
  const checklist = isLive ? LIVE_CHECKLIST : IDLE_CHECKLIST;

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
    const panel = previewViewportRef.current;

    if (!panel) {
      return;
    }

    let frameId = 0;

    const syncPreviewBounds = () => {
      frameId = 0;

      const rect = panel.getBoundingClientRect();

      void calibrateBridge.updatePreviewBounds({
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

      void calibrateBridge.updatePreviewBounds({
        left: 0,
        top: 0,
        width: 0,
        height: 0,
        devicePixelRatio: window.devicePixelRatio,
      });
    };
  }, [isLive, previewAspectRatio]);

  useEffect(() => {
    const unsubscribe = calibrateBridge.onCalibrateStatus((event) => {
      if (event.state === "error") {
        setElapsed(0);
        setCalibrateState("idle");
        setErrorEvent(event);
        return;
      }

      if (event.state === "idle") {
        setElapsed(0);
        setRepCount(0);
        setCapturedReps([]);
      }

      setErrorEvent(null);
      setCalibrateState(event.state);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    return calibrateBridge.onPreviewAspectRatio((aspectRatio) => {
      if (Number.isFinite(aspectRatio) && aspectRatio > 0) {
        setPreviewAspectRatio(aspectRatio);
      }
    });
  }, []);

  useEffect(() => {
    return calibrateBridge.onCalibrationUpdated((event) => {
      setRepCount(event.repCount);
      if (event.repCount === 0) {
        setCapturedReps([]);
      }
    });
  }, []);

  useEffect(() => {
    return () => {
      void calibrateBridge.stopCalibrate().catch(() => {});
    };
  }, []);

  const handleStartCalibration = async () => {
    setErrorEvent(null);
    setElapsed(0);
    setSaveMessage(null);

    try {
      await calibrateBridge.startCalibrate();
      await calibrateBridge.startCalibration();
      setCapturedReps([]);
      setRepCount(0);
      setCalibrateState("live");
    } catch (error) {
      setCalibrateState("error");
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to reach the desktop calibration bridge.",
      });
    }
  };

  const handleStopCalibration = async () => {
    try {
      setElapsed(0);
      await calibrateBridge.stopCalibrate();
      setCalibrateState("idle");
      setCapturedReps([]);
      setRepCount(0);
    } catch (error) {
      setCalibrateState("error");
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to stop the desktop-managed calibration camera.",
      });
    }
  };

  const handleCaptureRep = async () => {
    setErrorEvent(null);
    setSaveMessage(null);
    setIsSubmitting(true);

    try {
      const capturedRep = await calibrateBridge.captureRep();
      setRepCount(capturedRep.repCount);
      setCapturedReps((current) => [...current, capturedRep]);
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to capture the current gesture rep.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleResetReps = async () => {
    setErrorEvent(null);
    setSaveMessage(null);
    setIsSubmitting(true);

    try {
      await calibrateBridge.resetRep();
      setRepCount(0);
      setCapturedReps([]);
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to clear captured gesture reps.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSaveRep = async () => {
    setErrorEvent(null);
    setSaveMessage(null);
    setIsSubmitting(true);

    try {
      const result = await calibrateBridge.saveRep(gestureName);
      setGestureName("");
      setRepCount(result.repCount);
      setCapturedReps([]);
      setSaveMessage(`Saved "${result.name}" successfully.`);
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to save the captured gesture reps.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfigure = async () => {
    try {
      await calibrateBridge.openCameraSettings();
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
      await handleStopCalibration();
    } finally {
      setErrorEvent(null);
    }
  };

  return (
    <>
      <Box
        sx={{
          p: { xs: 2, md: 3 },
          maxWidth: 1280,
          mx: "auto",
          height: "100%",
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Stack spacing={1.5} sx={{ mb: 2, flexShrink: 0 }}>
          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
            <Typography variant="h4" component="h1" sx={{ flexGrow: 1, minWidth: 220 }}>
              Calibration Workspace
            </Typography>
            <Chip
              label={isLive ? "live" : "idle"}
              color={isLive ? "success" : "default"}
              size="small"
            />
            <Chip
              label={errorEvent ? "camera issue" : "bridge connected"}
              color={errorEvent ? "error" : "primary"}
              variant={errorEvent ? "filled" : "outlined"}
              size="small"
            />
          </Stack>

          <Typography color="text.secondary">
            Demo branch layout, current branch camera lifecycle. The preview,
            ownership, and cleanup are still managed by the desktop calibration
            bridge.
          </Typography>

          <Typography sx={{ color: "#3b6df6", fontWeight: 700 }}>
            Step {currentStep} of 4: {CALIBRATION_STEPS[currentStep - 1]}
          </Typography>
          <CalibrationProgress currentStep={currentStep} totalSteps={4} />
        </Stack>

        <Box
          sx={{
            display: "flex",
            gap: 2,
            flex: 1,
            minHeight: 0,
            flexDirection: { xs: "column", lg: "row" },
          }}
        >
          <Box
            sx={{
              flex: { lg: "1 1 58%" },
              minWidth: 0,
              minHeight: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Box
              ref={previewViewportRef}
              sx={{
                position: "relative",
                width: "100%",
                maxHeight: "100%",
                aspectRatio: String(previewAspectRatio),
                borderRadius: 3,
                overflow: "hidden",
                bgcolor: "#000",
                boxShadow: "0 20px 50px rgba(15, 23, 42, 0.16)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {!isLive ? (
                <Stack spacing={1} alignItems="center" sx={{ px: 3, textAlign: "center" }}>
                  <Typography variant="h6" sx={{ color: "#f8fafc", fontWeight: 700 }}>
                    Camera preview waiting
                  </Typography>
                  <Typography sx={{ color: "rgba(248, 250, 252, 0.76)", maxWidth: 360 }}>
                    Start calibration to hand camera ownership to the calibration
                    bridge and render the desktop overlay in this viewport.
                  </Typography>
                </Stack>
              ) : null}

              <Box
                sx={{
                  position: "absolute",
                  top: 16,
                  left: 16,
                  right: 16,
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 1,
                  pointerEvents: "none",
                }}
              >
                <Chip
                  label={isLive ? "REC" : "Preview idle"}
                  color={isLive ? "error" : "default"}
                  size="small"
                  sx={{
                    bgcolor: isLive ? "rgba(211, 47, 47, 0.92)" : "rgba(15, 23, 42, 0.72)",
                    color: "#fff",
                    fontWeight: 700,
                  }}
                />
                <Chip
                  label={
                    isLive
                      ? `${elapsed.toFixed(1)}s elapsed`
                      : `aspect ${previewAspectRatio.toFixed(2)}`
                  }
                  size="small"
                  sx={{
                    bgcolor: "rgba(15, 23, 42, 0.72)",
                    color: "#fff",
                    fontWeight: 700,
                  }}
                />
              </Box>
            </Box>
          </Box>

          <Paper
            variant="outlined"
            sx={{
              flex: { lg: "1 1 42%" },
              maxWidth: { lg: 420 },
              display: "flex",
              flexDirection: "column",
              minHeight: 0,
              overflow: "hidden",
              borderRadius: 3,
            }}
          >
            <Box sx={{ overflowY: "auto", flex: 1, px: 2, py: 1.5 }}>
              <Stack direction="row" spacing={1} sx={{ mb: 1.5 }}>
                <Button
                  size="small"
                  variant={isLive ? "outlined" : "contained"}
                  onClick={handleStartCalibration}
                  disabled={isLive}
                  sx={{ flex: 1, minWidth: 0, py: 0.75 }}
                >
                  Start
                </Button>
                <Button
                  size="small"
                  variant={isLive ? "contained" : "outlined"}
                  color={isLive ? "error" : "inherit"}
                  onClick={handleStopCalibration}
                  disabled={!isLive}
                  sx={{ flex: 1, minWidth: 0, py: 0.75 }}
                >
                  Stop
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  onClick={handleConfigure}
                  sx={{ flex: 1, minWidth: 0, py: 0.75, fontSize: 11 }}
                >
                  Camera
                </Button>
              </Stack>

              <Typography variant="subtitle2" sx={{ mb: 0.75, fontSize: 12 }}>
                Calibration status
              </Typography>
              <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap sx={{ mb: 1.5 }}>
                <Chip
                  label={`state: ${calibrateState}`}
                  size="small"
                  color={isLive ? "success" : "default"}
                  variant={isLive ? "filled" : "outlined"}
                />
                <Chip
                  label={`step: ${CALIBRATION_STEPS[currentStep - 1]}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
                <Chip
                  label={`timer: ${elapsed.toFixed(1)}s`}
                  size="small"
                  variant="outlined"
                />
                <Chip
                  label={`reps: ${repCount}`}
                  size="small"
                  variant="outlined"
                />
              </Stack>

              <Divider sx={{ my: 1.5 }} />

              <Typography variant="subtitle2" sx={{ mb: 0.75, fontSize: 12 }}>
                Gesture capture
              </Typography>
              <Stack spacing={1} sx={{ mb: 1.5 }}>
                <TextField
                  size="small"
                  label="Gesture name"
                  value={gestureName}
                  onChange={(event) => setGestureName(event.target.value)}
                  disabled={isSubmitting}
                />
                <Stack direction="row" spacing={1}>
                  <Button
                    size="small"
                    variant="contained"
                    onClick={handleCaptureRep}
                    disabled={!isLive || isSubmitting}
                    sx={{ flex: 1 }}
                  >
                    Capture Rep
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={handleResetReps}
                    disabled={repCount === 0 || isSubmitting}
                    sx={{ flex: 1 }}
                  >
                    Clear Reps
                  </Button>
                </Stack>
                <Button
                  size="small"
                  variant="contained"
                  color="success"
                  onClick={handleSaveRep}
                  disabled={!gestureName.trim() || repCount === 0 || isSubmitting}
                >
                  Save Gesture
                </Button>
                {saveMessage ? (
                  <Typography sx={{ fontSize: 12, color: "success.main" }}>
                    {saveMessage}
                  </Typography>
                ) : null}
              </Stack>

              <Divider sx={{ my: 1.5 }} />

              <Typography variant="subtitle2" sx={{ mb: 0.75, fontSize: 12 }}>
                Session notes
              </Typography>
              <List dense disablePadding sx={{ mb: 1.5 }}>
                {checklist.map((item) => (
                  <ListItem key={item} disableGutters sx={{ alignItems: "flex-start", py: 0.25 }}>
                    <ListItemText
                      primary={item}
                      primaryTypographyProps={{
                        fontSize: 13,
                        color: "text.secondary",
                        lineHeight: 1.45,
                      }}
                    />
                  </ListItem>
                ))}
              </List>

              <Divider sx={{ my: 1.5 }} />

              <Typography variant="subtitle2" sx={{ mb: 0.75, fontSize: 12 }}>
                Captured reps
              </Typography>
              <List dense disablePadding sx={{ mb: 1.5 }}>
                {capturedReps.length > 0 ? (
                  capturedReps.map((rep, index) => (
                    <ListItem key={`${index}-${rep.repCount}`} disableGutters sx={{ py: 0.35 }}>
                      <ListItemText
                        primary={`Rep ${index + 1}`}
                        secondary={formatRepAngles(rep)}
                        primaryTypographyProps={{ fontSize: 13, fontWeight: 600 }}
                        secondaryTypographyProps={{ fontSize: 11 }}
                      />
                    </ListItem>
                  ))
                ) : (
                  <ListItem disableGutters sx={{ py: 0.35 }}>
                    <ListItemText
                      primary="No reps captured yet"
                      secondary="Hold the target pose, then press Capture Rep."
                      primaryTypographyProps={{ fontSize: 13, fontWeight: 600 }}
                      secondaryTypographyProps={{ fontSize: 11 }}
                    />
                  </ListItem>
                )}
              </List>

              <Divider sx={{ my: 1.5 }} />

              <Typography variant="subtitle2" sx={{ mb: 0.75, fontSize: 12 }}>
                Bridge telemetry
              </Typography>
              <List dense disablePadding>
                <ListItem disableGutters sx={{ py: 0.35 }}>
                  <ListItemText
                    primary="Preview surface"
                    secondary="Viewport bounds are synchronized to the desktop bridge."
                    primaryTypographyProps={{ fontSize: 13, fontWeight: 600 }}
                    secondaryTypographyProps={{ fontSize: 11 }}
                  />
                </ListItem>
                <ListItem disableGutters sx={{ py: 0.35 }}>
                  <ListItemText
                    primary="Aspect ratio"
                    secondary={previewAspectRatio.toFixed(2)}
                    primaryTypographyProps={{ fontSize: 13, fontWeight: 600 }}
                    secondaryTypographyProps={{ fontSize: 11 }}
                  />
                </ListItem>
                <ListItem disableGutters sx={{ py: 0.35 }}>
                  <ListItemText
                    primary="Ownership"
                    secondary={
                      isLive
                        ? "Calibration bridge currently owns the shared camera."
                        : "Camera ownership is released."
                    }
                    primaryTypographyProps={{ fontSize: 13, fontWeight: 600 }}
                    secondaryTypographyProps={{ fontSize: 11 }}
                  />
                </ListItem>
              </List>
            </Box>

            <Divider />

            <Box sx={{ p: 1.5, display: "flex", justifyContent: "flex-end" }}>
              <Button onClick={() => navigate(ROUTES.session)} sx={{ fontWeight: 700 }}>
                Back to Session
              </Button>
            </Box>
          </Paper>
        </Box>
      </Box>

      <SessionCameraErrorModal
        open={errorEvent !== null}
        title="Calibration camera error"
        defaultMessage="The desktop app reported a camera error while opening the calibration camera."
        message={errorEvent?.message}
        onCancel={handleCloseError}
        onConfigure={handleConfigure}
      />
    </>
  );
};

export default Calibrate;
