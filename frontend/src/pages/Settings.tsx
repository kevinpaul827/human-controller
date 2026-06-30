import { useState } from "react";
import SettingSlider from "../components/SettingSlider";
import styles from "../styles/settings.module.css";

const SMOOTHING_LABELS = ["Low", "Low-Med", "Medium", "Med-High", "High"];

const DEFAULTS = {
  matchThreshold: 75,
  holdDuration: 1.5,
  cooldown: 0.5,
  smoothing: 2,
};

const Settings = () => {
  const [matchThreshold, setMatchThreshold] = useState(DEFAULTS.matchThreshold);
  const [holdDuration, setHoldDuration] = useState(DEFAULTS.holdDuration);
  const [cooldown, setCooldown] = useState(DEFAULTS.cooldown);
  const [smoothing, setSmoothing] = useState(DEFAULTS.smoothing);

  const handleReset = () => {
    setMatchThreshold(DEFAULTS.matchThreshold);
    setHoldDuration(DEFAULTS.holdDuration);
    setCooldown(DEFAULTS.cooldown);
    setSmoothing(DEFAULTS.smoothing);
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.heading}>Sensitivity Settings — Patient A</h1>
        <p className={styles.subheading}>
          Adjust thresholds for patients with different mobility levels
        </p>
      </header>

      <div className={styles.card}>
        <h2 className={styles.sectionTitle}>Global Settings</h2>

        <div className={styles.sliderList}>
          <SettingSlider
            label="Match Threshold"
            value={matchThreshold}
            min={0}
            max={100}
            step={1}
            formatValue={(value) => `${value}%`}
            onChange={setMatchThreshold}
          />
          <SettingSlider
            label="Hold Duration"
            value={holdDuration}
            min={0.5}
            max={3}
            step={0.1}
            formatValue={(value) => `${value.toFixed(1)} sec`}
            onChange={setHoldDuration}
          />
          <SettingSlider
            label="Cooldown Between Triggers"
            value={cooldown}
            min={0}
            max={2}
            step={0.1}
            formatValue={(value) => `${value.toFixed(1)} sec`}
            onChange={setCooldown}
          />
          <SettingSlider
            label="Smoothing Buffer"
            value={smoothing}
            min={0}
            max={4}
            step={1}
            formatValue={(value) => SMOOTHING_LABELS[value] ?? "Medium"}
            onChange={setSmoothing}
          />
        </div>
      </div>

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.resetButton}
          onClick={handleReset}
        >
          Reset to Defaults
        </button>
        <button type="button" className={styles.saveButton}>
          Save Changes
        </button>
      </div>
    </div>
  );
};

export default Settings;
