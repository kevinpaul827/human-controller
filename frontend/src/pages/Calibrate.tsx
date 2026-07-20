import { useEffect, useState, type RefObject } from "react";
import {
  Box,
  Button,
  Chip,
  Divider,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import CalibrationProgress from "../components/CalibrationProgress";
import SessionCameraErrorModal from "../components/modals/SessionCameraErrorModal";
import useDesktopCameraPreview from "../hooks/useDesktopCameraPreview";
import useSavedGestures from "../hooks/useSavedGestures";
import calibrateBridge from "../services/calibrateBridge";
import styles from "../styles/calibratePage.module.css";
import type {
  CalibrateState,
  CalibrateStatusEvent,
  CapturedRep,
  SavedGestureSummary,
} from "../types/calibrate";
import { ROUTES, CALIBRATION_STEPS } from "../utils/constants";

const formatRepAngles = (rep: CapturedRep) => {
  const joints = Object.entries(rep.angles);
  if (joints.length === 0) {
    return "No measurable joints captured yet.";
  }

  return joints
    .map(([joint, angle]) => `${joint} ${angle.toFixed(1)}°`)
    .join(" · ");
};

const renderTextBlock = (primary: string, secondary: string) => (
  <Box>
    <Typography className={styles.textPrimary}>{primary}</Typography>
    {secondary ? (
      <Typography className={styles.textSecondary}>{secondary}</Typography>
    ) : null}
  </Box>
);

type CameraPreviewProps = {
  elapsed: number;
  isLive: boolean;
  previewAspectRatio: number;
  previewViewportRef: RefObject<HTMLDivElement | null>;
};

const CameraPreview = ({
  elapsed,
  isLive,
  previewAspectRatio,
  previewViewportRef,
}: CameraPreviewProps) => (
  <Box className={styles.previewColumn}>
    <Box
      ref={previewViewportRef}
      // Keep this ref mount. The desktop app draws the preview here.
      className={styles.previewViewport}
    >
      {!isLive ? (
        <Stack spacing={1} alignItems="center" className={styles.previewIdle}>
          <Typography variant="h6" className={styles.previewIdleTitle}>
            Camera preview waiting
          </Typography>
          <Typography className={styles.previewIdleText}>
            Start calibration to hand camera ownership to the calibration bridge
            and render the desktop overlay in this viewport.
          </Typography>
        </Stack>
      ) : null}

      <Box className={styles.previewOverlay}>
        <Chip
          label={isLive ? "REC" : "Preview idle"}
          color={isLive ? "error" : "default"}
          size="small"
          className={`${styles.previewChip} ${
            isLive ? styles.previewChipLive : styles.previewChipDark
          }`}
        />
        <Chip
          label={
            isLive
              ? `${elapsed.toFixed(1)}s elapsed`
              : `aspect ${previewAspectRatio.toFixed(2)}`
          }
          size="small"
          className={`${styles.previewChip} ${styles.previewChipDark}`}
        />
      </Box>
    </Box>
  </Box>
);

type CalibrationPanelProps = {
  calibrateState: CalibrateState;
  capturedReps: CapturedRep[];
  currentStep: number;
  elapsed: number;
  gestureName: string;
  isLive: boolean;
  isSubmitting: boolean;
  previewAspectRatio: number;
  repCount: number;
  saveMessage: string | null;
  loadedGestures: SavedGestureSummary[];
  onLoadGestureClick: () => void;
  onCaptureRep: () => Promise<void>;
  onConfigure: () => Promise<void>;
  onGestureNameChange: (value: string) => void;
  onNavigateBack: () => void;
  onResetReps: () => Promise<void>;
  onSaveRep: () => Promise<void>;
  onStartCalibration: () => Promise<void>;
  onStopCalibration: () => Promise<void>;
};

const CalibrationPanel = ({
  calibrateState,
  capturedReps,
  currentStep,
  elapsed,
  gestureName,
  isLive,
  isSubmitting,
  previewAspectRatio,
  repCount,
  saveMessage,
  loadedGestures,
  onLoadGestureClick,
  onCaptureRep,
  onConfigure,
  onGestureNameChange,
  onNavigateBack,
  onResetReps,
  onSaveRep,
  onStartCalibration,
  onStopCalibration,
}: CalibrationPanelProps) => {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <Paper variant="outlined" className={styles.sidebar}>
      <Box className={styles.sidebarBody}>
        <Box className={styles.sidebarTop}>
          <Stack direction="row" spacing={1} className={styles.controlRow}>
            <Button
              size="small"
              variant={isLive ? "outlined" : "contained"}
              onClick={onStartCalibration}
              disabled={isLive}
              className={styles.controlButton}
            >
              Start
            </Button>
            <Button
              size="small"
              variant={isLive ? "contained" : "outlined"}
              color={isLive ? "error" : "inherit"}
              onClick={onStopCalibration}
              disabled={!isLive}
              className={styles.controlButton}
            >
              Stop
            </Button>
            <Button
              size="small"
              variant="outlined"
              onClick={onConfigure}
              className={`${styles.controlButton} ${styles.cameraButton}`}
            >
              Camera
            </Button>
          </Stack>

          <Typography variant="subtitle2" className={styles.sectionTitle}>
            Calibration status
          </Typography>
          <Stack
            direction="row"
            spacing={0.75}
            flexWrap="wrap"
            useFlexGap
            className={styles.chipRow}
          >
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
            <Chip label={`reps: ${repCount}`} size="small" variant="outlined" />
          </Stack>

          <Divider className={styles.sectionDivider} />

          <Typography variant="subtitle2" className={styles.sectionTitle}>
            Gesture capture
          </Typography>
          <Stack spacing={1} className={styles.sectionBlock}>
            <TextField
              size="small"
              label="Gesture name"
              value={gestureName}
              onChange={(event) => onGestureNameChange(event.target.value)}
              disabled={isSubmitting}
            />
            <Stack direction="row" spacing={1}>
              <Button
                size="small"
                variant="contained"
                onClick={onCaptureRep}
                disabled={!isLive || isSubmitting}
                className={styles.equalButton}
              >
                Capture Rep
              </Button>
              <Button
                size="small"
                variant="outlined"
                onClick={onResetReps}
                disabled={repCount === 0 || isSubmitting}
                className={styles.equalButton}
              >
                Clear Reps
              </Button>
            </Stack>
            <Button
              size="small"
              variant="outlined"
              onClick={onLoadGestureClick}
              disabled={isSubmitting}
            >
              Load Gesture
            </Button>
            <Button
              size="small"
              variant="contained"
              color="success"
              onClick={onSaveRep}
              disabled={!gestureName.trim() || repCount === 0 || isSubmitting}
            >
              Save Gesture
            </Button>
            {saveMessage ? (
              <Typography className={styles.saveMessage}>
                {saveMessage}
              </Typography>
            ) : null}
            {loadedGestures.length > 0 ? (
              <Stack
                direction="row"
                spacing={0.75}
                flexWrap="wrap"
                useFlexGap
                className={styles.loadedGestureRow}
              >
                {loadedGestures.map((gesture) => (
                  <Chip
                    key={gesture.gestureId}
                    size="small"
                    color="primary"
                    variant="outlined"
                    label={gesture.name}
                  />
                ))}
              </Stack>
            ) : null}
          </Stack>
        </Box>

        <Box className={styles.tabSection}>
          <Divider className={styles.sectionDivider} />
          <Tabs
            value={activeTab}
            onChange={(_, value: number) => setActiveTab(value)}
            variant="fullWidth"
            className={styles.sectionTabs}
          >
            <Tab label="Captured reps" />
            <Tab label="Bridge telemetry" />
          </Tabs>

          <Box className={styles.tabPanel}>
            {activeTab === 0 ? (
              <List dense disablePadding className={styles.sectionList}>
                {capturedReps.length > 0 ? (
                  capturedReps.map((rep, index) => (
                    <ListItem
                      key={`${index}-${rep.repCount}`}
                      disableGutters
                      className={styles.listItem}
                    >
                      <ListItemText
                        primary={renderTextBlock(
                          `Rep ${index + 1}`,
                          formatRepAngles(rep),
                        )}
                      />
                    </ListItem>
                  ))
                ) : (
                  <ListItem disableGutters className={styles.listItem}>
                    <ListItemText
                      primary={renderTextBlock(
                        "No reps captured yet",
                        "Hold the target pose, then press Capture Rep.",
                      )}
                    />
                  </ListItem>
                )}
              </List>
            ) : (
              <List dense disablePadding className={styles.sectionList}>
                <ListItem disableGutters className={styles.listItem}>
                  <ListItemText
                    primary={renderTextBlock(
                      "Preview surface",
                      "Viewport bounds are synchronized to the desktop bridge.",
                    )}
                  />
                </ListItem>
                <ListItem disableGutters className={styles.listItem}>
                  <ListItemText
                    primary={renderTextBlock(
                      "Aspect ratio",
                      previewAspectRatio.toFixed(2),
                    )}
                  />
                </ListItem>
                <ListItem disableGutters className={styles.listItem}>
                  <ListItemText
                    primary={renderTextBlock(
                      "Ownership",
                      isLive
                        ? "Calibration bridge currently owns the shared camera."
                        : "Camera ownership is released.",
                    )}
                  />
                </ListItem>
              </List>
            )}
          </Box>
        </Box>
      </Box>

      <Divider />

      <Box className={styles.footer}>
        <Button onClick={onNavigateBack} className={styles.backButton}>
          Back to Session
        </Button>
      </Box>
    </Paper>
  );
};

const Calibrate = () => {
  const navigate = useNavigate();
  const [calibrateState, setCalibrateState] = useState<CalibrateState>("idle");
  const [errorEvent, setErrorEvent] = useState<CalibrateStatusEvent | null>(
    null,
  );
  const [gestureName, setGestureName] = useState("");
  const [repCount, setRepCount] = useState(0);
  const [capturedReps, setCapturedReps] = useState<CapturedRep[]>([]);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGesturePickerOpen, setIsGesturePickerOpen] = useState(false);
  const isLive = calibrateState === "live";
  const {
    availableGestures,
    loadedGestures,
    isLoading: isLoadingGestures,
    loadGesture,
    refresh: refreshSavedGestures,
  } = useSavedGestures();
  const { elapsed, previewAspectRatio, previewViewportRef, setElapsed } =
    useDesktopCameraPreview({
      bridge: calibrateBridge,
      isLive,
    });
  const currentStep = isLive ? 3 : 2;
  useEffect(() => {
    // Keep this bridge listener. The desktop app is the source of camera state.
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
    // Keep this bridge listener. Rep updates come from the desktop app.
    return calibrateBridge.onCalibrationUpdated((event) => {
      setRepCount(event.repCount);
      if (event.repCount === 0) {
        setCapturedReps([]);
      }
    });
  }, []);

  useEffect(() => {
    return () => {
      // Keep this cleanup. It releases the shared desktop camera.
      void calibrateBridge.stopCalibrate().catch(() => {});
    };
  }, []);

  useEffect(() => {
    if (previewViewportRef.current) {
      previewViewportRef.current.style.setProperty(
        "--preview-aspect-ratio",
        String(previewAspectRatio),
      );
    }
  }, [previewAspectRatio, previewViewportRef]);

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
      if (result.loadedGestures) {
        void refreshSavedGestures();
      }
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

  const handleLoadSavedGesture = async (gestureId: string) => {
    setErrorEvent(null);
    setSaveMessage(null);
    setIsSubmitting(true);

    try {
      const result = await loadGesture(gestureId);
      setSaveMessage(`Loaded "${result.gesture.name}" for this session.`);
      setIsGesturePickerOpen(false);
    } catch (error) {
      setErrorEvent({
        state: "error",
        message:
          error instanceof Error
            ? error.message
            : "Unable to load the selected saved gesture.",
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
      <Box className={styles.page}>
        <Stack spacing={1.5} className={styles.header}>
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            flexWrap="wrap"
          >
            <Typography variant="h4" component="h1" className={styles.title}>
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

          <Typography className={styles.stepLabel}>
            Step {currentStep} of 4: {CALIBRATION_STEPS[currentStep - 1]}
          </Typography>
          <CalibrationProgress currentStep={currentStep} totalSteps={4} />
        </Stack>

        <Box className={styles.layout}>
          <CameraPreview
            elapsed={elapsed}
            isLive={isLive}
            previewAspectRatio={previewAspectRatio}
            previewViewportRef={previewViewportRef}
          />
          <CalibrationPanel
            calibrateState={calibrateState}
            capturedReps={capturedReps}
            currentStep={currentStep}
            elapsed={elapsed}
            gestureName={gestureName}
            isLive={isLive}
            isSubmitting={isSubmitting}
            previewAspectRatio={previewAspectRatio}
            repCount={repCount}
            saveMessage={saveMessage}
            loadedGestures={loadedGestures}
            onLoadGestureClick={() => {
              void refreshSavedGestures();
              setIsGesturePickerOpen(true);
            }}
            onCaptureRep={handleCaptureRep}
            onConfigure={handleConfigure}
            onGestureNameChange={setGestureName}
            onNavigateBack={() => navigate(ROUTES.session)}
            onResetReps={handleResetReps}
            onSaveRep={handleSaveRep}
            onStartCalibration={handleStartCalibration}
            onStopCalibration={handleStopCalibration}
          />
        </Box>
      </Box>

      <Dialog
        open={isGesturePickerOpen}
        onClose={() => setIsGesturePickerOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Load saved gestures</DialogTitle>
        <DialogContent dividers>
          <List disablePadding>
            {availableGestures.length > 0 ? (
              availableGestures.map((gesture) => {
                const isLoaded = loadedGestures.some(
                  (loadedGesture) => loadedGesture.gestureId === gesture.gestureId,
                );

                return (
                  <ListItem key={gesture.gestureId} disablePadding>
                    <ListItemButton
                      disabled={isSubmitting || isLoaded}
                      onClick={() => void handleLoadSavedGesture(gesture.gestureId)}
                    >
                      <ListItemText
                        primary={gesture.name}
                        secondary={isLoaded ? "Already loaded for this session" : gesture.gestureId}
                      />
                    </ListItemButton>
                  </ListItem>
                );
              })
            ) : (
              <ListItem disableGutters>
                <ListItemText
                  primary="No saved gestures found"
                  secondary={
                    isLoadingGestures
                      ? "Loading saved gestures..."
                      : "Save a gesture first, then load it into this session."
                  }
                />
              </ListItem>
            )}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsGesturePickerOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

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
