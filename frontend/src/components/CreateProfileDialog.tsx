import { useState } from "react";
import styles from "../styles/profiles.module.css";

type CreateProfileDialogProps = {
  onClose: () => void;
  onCreate: (patientName: string, notes: string) => Promise<string | null>;
};

const CreateProfileDialog = ({
  onClose,
  onCreate,
}: CreateProfileDialogProps) => {
  const [patientName, setPatientName] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    const resolvedName = patientName.trim();
    if (!resolvedName) {
      setError("Patient name is required.");
      return;
    }
    if (resolvedName.length > 80) {
      setError("Patient name cannot exceed 80 characters.");
      return;
    }

    setSaving(true);
    setError(null);
    const saveError = await onCreate(resolvedName, notes.trim());
    setSaving(false);
    if (saveError) {
      setError(saveError);
    }
  };

  return (
    <div
      className={styles.dialogBackdrop}
      role="presentation"
      onClick={() => {
        if (!saving) {
          onClose();
        }
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape" && !saving) {
          onClose();
        }
      }}
    >
      <div
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-profile-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="new-profile-title" className={styles.dialogTitle}>
          Create patient profile
        </h2>
        <p className={styles.dialogDescription}>
          Movements can be calibrated and added after the profile is created.
        </p>

        <div className={styles.field}>
          <label htmlFor="patient-name">Patient name</label>
          <input
            id="patient-name"
            value={patientName}
            onChange={(event) => setPatientName(event.target.value)}
            placeholder="e.g. Patient C"
            autoFocus
            disabled={saving}
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="notes">Notes</label>
          <textarea
            id="notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder="Optional treatment or accessibility notes"
            rows={3}
            disabled={saving}
          />
        </div>

        {error ? (
          <p className={styles.formError} role="alert">
            {error}
          </p>
        ) : null}

        <div className={styles.dialogActions}>
          <button
            type="button"
            className={styles.dialogCancel}
            onClick={onClose}
            disabled={saving}
          >
            Cancel
          </button>
          <button
            type="button"
            className={styles.dialogSubmit}
            onClick={() => void handleSubmit()}
            disabled={saving}
          >
            {saving ? "Creating…" : "Create profile"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateProfileDialog;
