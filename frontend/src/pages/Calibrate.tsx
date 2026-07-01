import { type CSSProperties, useEffect, useState } from "react";
import CalibrationProgress from "../components/CalibrationProgress";
import CalibrateSkeleton from "../components/CalibrateSkeleton";
import KeyButton from "../components/KeyButton";
import styles from "../styles/calibratePage.module.css";

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

const Calibrate = () => {
  const [step, setStep] = useState(1);
  const [selectedKeyId, setSelectedKeyId] = useState("up");
  const [customKey, setCustomKey] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);

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

  const restart = () => {
    setStep(1);
    setSelectedKeyId("up");
    setCustomKey("");
    setElapsed(0);
    setIsRecording(false);
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
              placeholder="Custom Key"
              value={customKey}
              onChange={(event) => setCustomKey(event.target.value)}
            />
            <button
              type="button"
              className={styles.secondaryButton}
              onClick={() => setCustomKey("")}
            >
              Add Key Binding
            </button>
          </div>

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
                onClick={() => setStep(4)}
              >
                Confirm &amp; Save →
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {step === 4 ? (
        <div className={styles.completeCard}>
          <h2 className={styles.completeTitle}>Calibration Complete</h2>
          <p className={styles.completeMessage}>
            Gesture saved successfully. Right Arm Raise is now bound to{" "}
            {selectedKeyText}.
          </p>
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
