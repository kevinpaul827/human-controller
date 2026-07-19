import { type CSSProperties, useEffect, useState } from "react";
import CalibrationProgress from "../components/CalibrationProgress";
import CalibrateSkeleton from "../components/CalibrateSkeleton";
import KeyButton from "../components/KeyButton";
import sessionBridge from "../services/sessionBridge";
import styles from "../styles/calibratePage.module.css";
import type { SavedGesture } from "../types/gesture";

type KeyOption = {
  id: string;
  label: string;
  displayLabel: string;
};

const KEYS: KeyOption[] = [
  { id: "up", label: "↑", displayLabel: "Up Arrow" },
  { id: "down", label: "↓", displayLabel: "Down Arrow" },
  { id: "left", label: "←", displayLabel: "Left Arrow" },
  { id: "right", label: "→", displayLabel: "Right Arrow" },
  { id: "space", label: "Space", displayLabel: "Space" },
];

const STEP_LABELS = [
  "Select Key",
  "Record Movement",
  "Review Match",
  "Complete Calibration",
];

const SIMILARITY_SCORE = 87;
const THRESHOLD = 75;
const DEFAULT_GESTURE_NAME = "Right Arm Raise";
const DEFAULT_GESTURE_REGIONS = ["right_arm"];
const DEFAULT_ACTIVE_JOINTS = ["R_SHOULDER_ABD", "R_ELBOW"];
const DEFAULT_TARGET_ANGLES = {
  R_SHOULDER_ABD: 90,
  R_ELBOW: 170,
};
const DEFAULT_TOLERANCE_DEG = {
  R_SHOULDER_ABD: 20,
  R_ELBOW: 20,
};

const Calibrate = () => {
  const [step, setStep] = useState(1);
  const [selectedKeyId, setSelectedKeyId] = useState("up");
  const [gestureName, setGestureName] = useState(DEFAULT_GESTURE_NAME);
  const [isRecording, setIsRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [savedGestures, setSavedGestures] = useState<SavedGesture[]>([]);
  const [saveError, setSaveError] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    void sessionBridge
      .listGestures()
      .then(setSavedGestures)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!isRecording) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setElapsed((current) => Number((current + 0.1).toFixed(1)));
    }, 100);

    return () => window.clearInterval(intervalId);
  }, [isRecording]);

  const selectedKey = KEYS.find((key) => key.id === selectedKeyId) ?? KEYS[0];
  const isArrowKey = ["up", "down", "left", "right"].includes(selectedKey.id);
  const selectedKeyText = isArrowKey
    ? `${selectedKey.label} ${selectedKey.displayLabel}`
    : selectedKey.displayLabel;

  const scoreFillStyle = {
    "--fill-percent": `${SIMILARITY_SCORE}%`,
  } as CSSProperties;

  const goToRecord = () => {
    setStep(2);
    setElapsed(0);
    setIsRecording(true);
  };

  const goToReview = () => {
    setIsRecording(false);
    setStep(3);
  };

  const handleConfirmSave = async () => {
    setIsSaving(true);
    setSaveError("");

    try {
      const savedGesture = await sessionBridge.saveGesture({
        name: gestureName.trim() || DEFAULT_GESTURE_NAME,
        regions: DEFAULT_GESTURE_REGIONS,
        active_joints: DEFAULT_ACTIVE_JOINTS,
        target_angles: DEFAULT_TARGET_ANGLES,
        tolerance_deg: DEFAULT_TOLERANCE_DEG,
      });

      setSavedGestures((current) => {
        const next = current.filter(
          (gesture) => gesture.gesture_id !== savedGesture.gesture_id,
        );
        return [...next, savedGesture].sort((left, right) =>
          left.name.localeCompare(right.name),
        );
      });
      setStep(4);
    } catch (error) {
      setSaveError(
        error instanceof Error ? error.message : "Unable to save gesture.",
      );
    } finally {
      setIsSaving(false);
    }
  };

  const restart = () => {
    setStep(1);
    setSelectedKeyId("up");
    setGestureName(DEFAULT_GESTURE_NAME);
    setElapsed(0);
    setIsRecording(false);
    setSaveError("");
  };

  return (
    <div className={styles.page}>
      <header>
        <h1 className={styles.heading}>Calibrate Movement</h1>
        <p className={styles.stepLabel}>
          Step {step} of 4: {STEP_LABELS[step - 1]}
        </p>
        <CalibrationProgress currentStep={step} totalSteps={4} />
      </header>

      {step === 1 ? (
        <div className={styles.card}>
          <p className={styles.prompt}>
            Which keyboard key should this movement trigger?
          </p>

          <div className={styles.keyRow}>
            {KEYS.map((key) => (
              <KeyButton
                key={key.id}
                label={key.label}
                displayLabel={key.displayLabel}
                isSelected={selectedKeyId === key.id}
                onSelect={() => setSelectedKeyId(key.id)}
              />
            ))}
          </div>

          <p className={styles.selectionFeedback}>
            Selected: {selectedKeyText}
          </p>

          <div className={styles.customRow}>
            <input
              type="text"
              className={styles.customInput}
              placeholder="Movement Name"
              value={gestureName}
              onChange={(event) => setGestureName(event.target.value)}
            />
          </div>

          {savedGestures.length > 0 ? (
            <div className={styles.savedSection}>
              <p className={styles.savedTitle}>Saved Gestures</p>
              <div className={styles.savedList}>
                {savedGestures.map((gesture) => (
                  <p key={gesture.gesture_id} className={styles.savedItem}>
                    {gesture.name}
                  </p>
                ))}
              </div>
            </div>
          ) : null}

          <div className={styles.navRow}>
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => setStep(1)}
            >
              Back
            </button>
            <button
              type="button"
              className={styles.primaryButton}
              onClick={goToRecord}
            >
              Continue: Record Movement →
            </button>
          </div>
        </div>
      ) : null}

      {step === 2 ? (
        <div className={styles.recordGrid}>
          <div className={styles.cameraPanel}>
            <div className={styles.cameraHeader}>
              <span className={styles.cameraStatus}>
                Skeleton Overlay — Tracking OK
              </span>
              {isRecording ? (
                <span className={styles.recBadge}>
                  <span className={styles.recDot} />
                  REC {elapsed.toFixed(1)}s
                </span>
              ) : null}
            </div>
            <div className={styles.cameraFeed}>
              <CalibrateSkeleton className={styles.skeletonOverlay} />
            </div>
          </div>

          <div className={styles.instructionsPanel}>
            <h2 className={styles.instructionsTitle}>Instructions</h2>
            <ol className={styles.instructionsList}>
              <li>Stand in front of webcam</li>
              <li>Perform target movement (e.g. raise right arm)</li>
              <li>Hold final pose for 2 seconds</li>
            </ol>

            <p className={styles.selectedKeyLine}>
              Selected Key: {selectedKeyText}
            </p>

            <div
              className={`${styles.recordingBox} ${isRecording ? styles.recordingBoxActive : ""}`}
            >
              <p className={styles.recordingTitle}>
                {isRecording ? "● RECORDING" : "Recording stopped"}
              </p>
              <p className={styles.recordingCaption}>
                {isRecording
                  ? `Capturing gesture — hold final pose (${elapsed.toFixed(1)}s elapsed)`
                  : `Captured gesture after ${elapsed.toFixed(1)}s`}
              </p>
            </div>

            <div className={styles.recordActions}>
              <button
                type="button"
                className={styles.stopButton}
                onClick={() => setIsRecording(false)}
                disabled={!isRecording}
              >
                ■ STOP
              </button>
              <button
                type="button"
                className={styles.primaryButton}
                onClick={goToReview}
              >
                Save Gesture →
              </button>
            </div>

            <button
              type="button"
              className={styles.backLink}
              onClick={() => {
                setIsRecording(false);
                setStep(1);
              }}
            >
              ← Back to key selection
            </button>
          </div>
        </div>
      ) : null}

      {step === 3 ? (
        <div className={styles.reviewGrid}>
          <div className={styles.poseCard}>
            <p className={styles.poseLabel}>Live Pose</p>
            <div className={styles.posePreview}>
              <CalibrateSkeleton className={styles.poseSkeleton} />
            </div>
          </div>

          <div className={styles.poseCard}>
            <p className={styles.poseLabel}>Template</p>
            <div className={styles.posePreview}>
              <CalibrateSkeleton className={styles.poseSkeleton} />
            </div>
          </div>

          <div className={styles.scoreCard}>
            <h2 className={styles.scoreTitle}>Similarity Score</h2>
            <p className={styles.scoreValue}>{SIMILARITY_SCORE}%</p>

            <div className={styles.scoreProgressTrack} style={scoreFillStyle}>
              <div className={styles.scoreProgressFill} />
            </div>

            <p className={styles.scoreMeta}>Threshold: {THRESHOLD}%</p>
            <p className={styles.scoreStatus}>
              ✓ Match would trigger {selectedKey.label} key
            </p>
            <p className={styles.scoreBinding}>
              Binding: Right Arm Raise → {selectedKey.label}
            </p>

            <div className={styles.reviewActions}>
              <button
                type="button"
                className={styles.secondaryButton}
                onClick={() => {
                  setStep(2);
                  setElapsed(0);
                  setIsRecording(true);
                }}
              >
                Re-record
              </button>
              <button type="button" className={styles.secondaryButton}>
                Adjust Threshold
              </button>
              <button
                type="button"
                className={styles.primaryButton}
                onClick={() => void handleConfirmSave()}
                disabled={isSaving}
              >
                {isSaving ? "Saving..." : "Confirm & Save →"}
              </button>
            </div>
            {saveError ? (
              <p className={styles.errorText}>{saveError}</p>
            ) : null}
          </div>
        </div>
      ) : null}

      {step === 4 ? (
        <div className={styles.completeCard}>
          <h2 className={styles.completeTitle}>Calibration Complete</h2>
          <p className={styles.completeMessage}>
            Gesture saved successfully. {gestureName.trim() || DEFAULT_GESTURE_NAME} is now bound to{" "}
            {selectedKeyText}.
          </p>
          {savedGestures.length > 0 ? (
            <div className={styles.savedSection}>
              <p className={styles.savedTitle}>Saved Gestures</p>
              <div className={styles.savedList}>
                {savedGestures.map((gesture) => (
                  <p key={gesture.gesture_id} className={styles.savedItem}>
                    {gesture.name}
                  </p>
                ))}
              </div>
            </div>
          ) : null}
          <div className={styles.navRow}>
            <button
              type="button"
              className={styles.primaryButton}
              onClick={restart}
            >
              Calibrate Another Gesture
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default Calibrate;
