import styles from "../styles/calibrationProgress.module.css";

type CalibrationProgressProps = {
  currentStep: number;
  totalSteps: number;
};

const CalibrationProgress = ({
  currentStep,
  totalSteps,
}: CalibrationProgressProps) => (
  <div
    className={styles.track}
    role="progressbar"
    aria-valuenow={currentStep}
    aria-valuemin={1}
    aria-valuemax={totalSteps}
  >
    {Array.from({ length: totalSteps }, (_, index) => (
      <span
        key={index}
        className={`${styles.segment} ${index < currentStep ? styles.segmentActive : ""}`}
      />
    ))}
  </div>
);

export default CalibrationProgress;
