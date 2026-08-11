import { BrutalInput } from "@/components/ui/brutal-input";
import { formatKey, normaliseKey } from "../utils/keyboard";

type KeyCaptureInputProps = {
  value: string;
  onChange: (key: string) => void;
  ariaLabel: string;
  disabled?: boolean;
};

// Read-only input that listens for one key press and stores it in a normalised format.
const KeyCaptureInput = ({
  value,
  onChange,
  ariaLabel,
  disabled = false,
}: KeyCaptureInputProps) => (
  <BrutalInput
    aria-label={ariaLabel}
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
