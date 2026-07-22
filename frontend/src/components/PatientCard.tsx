import { useMemo, useState } from "react";
import type { GestureSummary, PatientProfile } from "../types/profile";
import { formatKey } from "../utils/keyboard";
import KeyCaptureInput from "./KeyCaptureInput";
import styles from "../styles/patientCard.module.css";

const formatUpdatedAt = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
};

type PatientCardProps = {
  profile: PatientProfile;
  gestures: GestureSummary[];
  expanded: boolean;
  onExpandChange: (expanded: boolean) => void;
  onSetBinding: (gestureId: string, key: string) => Promise<string | null>;
  onRemoveBinding: (gestureId: string) => Promise<string | null>;
  onCalibrate: () => void;
  onStartSession: () => void;
  onDelete: () => Promise<void>;
};

const PatientCard = ({
  profile,
  gestures,
  expanded,
  onExpandChange,
  onSetBinding,
  onRemoveBinding,
  onCalibrate,
  onStartSession,
  onDelete,
}: PatientCardProps) => {
  const [selectedGestureId, setSelectedGestureId] = useState("");
  const [newKey, setNewKey] = useState("");
  const [editingGestureId, setEditingGestureId] = useState<string | null>(null);
  const [editedKey, setEditedKey] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const gestureById = useMemo(
    () => new Map(gestures.map((gesture) => [gesture.gestureId, gesture])),
    [gestures],
  );
  const bindings = Object.entries(profile.keyBindings).sort(
    ([left], [right]) => {
      const leftName = gestureById.get(left)?.name ?? left;
      const rightName = gestureById.get(right)?.name ?? right;
      return leftName.localeCompare(rightName);
    },
  );
  const availableGestures = gestures.filter(
    (gesture) => !(gesture.gestureId in profile.keyBindings),
  );
  const bindingCount = bindings.length;
  const bindingLabel = `${bindingCount} key binding${bindingCount === 1 ? "" : "s"}`;

  const handleAddBinding = async () => {
    if (!selectedGestureId || !newKey) {
      setFormError("Choose a calibrated movement and press a keyboard key.");
      return;
    }

    setSaving(true);
    setFormError(null);
    const error = await onSetBinding(selectedGestureId, newKey);
    setSaving(false);
    setFormError(error);
    if (!error) {
      setSelectedGestureId("");
      setNewKey("");
    }
  };

  const startEditing = (gestureId: string, key: string) => {
    setEditingGestureId(gestureId);
    setEditedKey(key);
    setFormError(null);
  };

  const handleUpdateBinding = async () => {
    if (!editingGestureId || !editedKey) {
      setFormError("Press a keyboard key before saving.");
      return;
    }

    setSaving(true);
    setFormError(null);
    const error = await onSetBinding(editingGestureId, editedKey);
    setSaving(false);
    setFormError(error);
    if (!error) {
      setEditingGestureId(null);
      setEditedKey("");
    }
  };

  const handleRemoveBinding = async (gestureId: string) => {
    setSaving(true);
    setFormError(null);
    const error = await onRemoveBinding(gestureId);
    setSaving(false);
    setFormError(error);
  };

  return (
    <article
      className={`${styles.card} ${expanded ? styles.cardExpanded : ""}`}
    >
      <div className={styles.header}>
        <div className={styles.patientIdentity}>
          <span className={styles.avatar} aria-hidden="true">
            {profile.patientName.charAt(0).toUpperCase()}
          </span>
          <h2 className={styles.patientName}>{profile.patientName}</h2>
        </div>
        <span className={styles.badge}>{bindingLabel}</span>
      </div>

      {profile.notes ? <p className={styles.notes}>{profile.notes}</p> : null}
      <p className={styles.updatedAt}>
        Last updated {formatUpdatedAt(profile.updatedAt)}
      </p>

      {expanded ? (
        <div className={styles.body}>
          <div className={styles.sectionHeader}>
            <div>
              <h3 className={styles.sectionTitle}>Gesture keybindings</h3>
              <p className={styles.sectionHelp}>
                Review movements saved to this profile or change their keys.
              </p>
            </div>
          </div>

          {bindings.length === 0 ? (
            <p className={styles.emptyBindings}>
              No keybindings saved for this profile.
            </p>
          ) : (
            <div className={styles.bindingList}>
              {bindings.map(([gestureId, key]) => {
                const editing = editingGestureId === gestureId;
                const gesture = gestureById.get(gestureId);
                return (
                  <div key={gestureId} className={styles.bindingRow}>
                    {editing ? (
                      <>
                        <span className={styles.gestureName}>
                          {gesture?.name ?? "Unavailable gesture"}
                        </span>
                        <KeyCaptureInput
                          ariaLabel={`New key for ${gesture?.name ?? "gesture"}`}
                          value={editedKey}
                          onChange={setEditedKey}
                          disabled={saving}
                        />
                        <div className={styles.rowActions}>
                          <button
                            type="button"
                            className={styles.buttonPrimary}
                            onClick={() => void handleUpdateBinding()}
                            disabled={saving}
                          >
                            {saving ? "Saving…" : "Save"}
                          </button>
                          <button
                            type="button"
                            className={styles.buttonSecondary}
                            onClick={() => {
                              setEditingGestureId(null);
                              setEditedKey("");
                              setFormError(null);
                            }}
                            disabled={saving}
                          >
                            Cancel
                          </button>
                        </div>
                      </>
                    ) : (
                      <>
                        <span className={styles.gestureName}>
                          {gesture?.name ?? "Unavailable gesture"}
                        </span>
                        <span className={styles.keycap}>{formatKey(key)}</span>
                        <div className={styles.rowActions}>
                          <button
                            type="button"
                            className={styles.buttonSecondary}
                            onClick={() => startEditing(gestureId, key)}
                            disabled={saving}
                          >
                            Change key
                          </button>
                          <button
                            type="button"
                            className={styles.buttonDangerSmall}
                            onClick={() => void handleRemoveBinding(gestureId)}
                            disabled={saving}
                          >
                            Remove
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {gestures.length === 0 ? (
            <div className={styles.calibrationPrompt}>
              <span>No calibrated movements are available yet.</span>
            </div>
          ) : availableGestures.length > 0 ? (
            <div className={styles.addBinding}>
              <h4 className={styles.addBindingTitle}>
                Add calibrated movement
              </h4>
              <div className={styles.addBindingFields}>
                <select
                  aria-label="Calibrated movement"
                  className={styles.bindingInput}
                  value={selectedGestureId}
                  onChange={(event) => setSelectedGestureId(event.target.value)}
                  disabled={saving}
                >
                  <option value="">Choose movement</option>
                  {availableGestures.map((gesture) => (
                    <option key={gesture.gestureId} value={gesture.gestureId}>
                      {gesture.name}
                    </option>
                  ))}
                </select>
                <KeyCaptureInput
                  ariaLabel="Keyboard key for movement"
                  value={newKey}
                  onChange={setNewKey}
                  disabled={saving}
                />
                <button
                  type="button"
                  className={styles.buttonPrimary}
                  onClick={() => void handleAddBinding()}
                  disabled={saving}
                >
                  {saving ? "Adding…" : "Add"}
                </button>
              </div>
            </div>
          ) : (
            <p className={styles.allAssigned}>
              All calibrated movements are already in this profile.
            </p>
          )}

          {formError ? (
            <p className={styles.formError} role="alert">
              {formError}
            </p>
          ) : null}
        </div>
      ) : null}

      <div className={styles.actions}>
        <button
          type="button"
          className={styles.buttonSecondary}
          onClick={() => {
            onExpandChange(!expanded);
            setFormError(null);
          }}
          disabled={saving}
        >
          {expanded ? "Close" : "Manage keybindings"}
        </button>
        <button
          type="button"
          className={styles.buttonSecondary}
          onClick={onCalibrate}
          disabled={saving}
        >
          Calibrate
        </button>
        <button
          type="button"
          className={styles.buttonPrimary}
          onClick={onStartSession}
          disabled={saving}
        >
          Start session
        </button>
        <span className={styles.actionsSpacer} aria-hidden="true" />
        <button
          type="button"
          className={styles.buttonDanger}
          onClick={() => void onDelete()}
          disabled={saving}
        >
          Delete profile
        </button>
      </div>
    </article>
  );
};

export default PatientCard;
