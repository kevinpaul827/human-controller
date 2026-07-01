import styles from "../styles/keyButton.module.css";

type KeyButtonProps = {
  label: string;
  displayLabel: string;
  isSelected: boolean;
  onSelect: () => void;
};

const KeyButton = ({
  label,
  displayLabel,
  isSelected,
  onSelect,
}: KeyButtonProps) => (
  <button
    type="button"
    className={`${styles.button} ${isSelected ? styles.buttonSelected : ""}`}
    onClick={onSelect}
    aria-pressed={isSelected}
    aria-label={displayLabel}
  >
    {label}
  </button>
);

export default KeyButton;
