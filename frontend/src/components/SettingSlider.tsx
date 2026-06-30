import type { CSSProperties } from "react";
import styles from "../styles/settingSlider.module.css";

type SettingSliderProps = {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  formatValue: (value: number) => string;
  onChange: (value: number) => void;
};

const SettingSlider = ({
  label,
  value,
  min,
  max,
  step,
  formatValue,
  onChange,
}: SettingSliderProps) => {
  const percent = ((value - min) / (max - min)) * 100;
  const trackStyle = {
    "--fill-percent": `${percent}%`,
  } as CSSProperties;

  return (
    <div className={styles.row}>
      <label className={styles.label} htmlFor={`slider-${label}`}>
        {label}: {formatValue(value)}
      </label>
      <div className={styles.sliderTrack} style={trackStyle}>
        <div className={styles.sliderFill} />
        <input
          id={`slider-${label}`}
          type="range"
          className={styles.sliderInput}
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
        />
      </div>
    </div>
  );
};

export default SettingSlider;
