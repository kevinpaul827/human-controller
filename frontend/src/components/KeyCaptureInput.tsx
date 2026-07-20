import { formatKey, normaliseKey } from "../utils/keyboard";
import styles from "../styles/patientCard.module.css";

type KeyCaptureInputProps = {
  value: string;
  onChange: (key: string) => void;
  ariaLabel: string;
  disabled?: boolean;
};

const KeyCaptureInput = ({
  value,
  onChange,
  ariaLabel,
  disabled = false,
}: KeyCaptureInputProps) => (
  <input
    aria-label={ariaLabel}
    className={styles.bindingInput}
    value={value ? formatKey(value) : ""}
    placeholder="Click, then press a key"
    readOnly
    disabled={disabled}
    onKeyDown={(event) => {
      if (event.key === "Tab") {
        return;
      }
      event.preventDefault();
      onChange(normaliseKey(event.key));
    }}
  />
);

export default KeyCaptureInput;
