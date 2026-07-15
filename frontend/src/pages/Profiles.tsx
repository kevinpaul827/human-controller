import { useMemo, useState } from "react";
import PatientCard from "../components/PatientCard";
import { SAMPLE_PROFILES } from "../data/sampleProfiles";
import type { PatientProfile } from "../types/profile";
import styles from "../styles/profiles.module.css";

const slugifyPatientId = (name: string) => {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || "patient";
};

type NewProfileForm = {
  patientName: string;
  patientId: string;
  gameName: string;
  gestureName: string;
  gestureKey: string;
};

const Profiles = () => {
  const [profiles, setProfiles] = useState<PatientProfile[]>(SAMPLE_PROFILES);
  const [expandedPatientId, setExpandedPatientId] = useState<string | null>(
    SAMPLE_PROFILES[0]?.patientId ?? null,
  );
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [form, setForm] = useState<NewProfileForm>({
    patientName: "",
    patientId: "",
    gameName: "",
    gestureName: "",
    gestureKey: "",
  });

  const sortedProfiles = useMemo(
    () =>
      [...profiles].sort((a, b) => a.patientName.localeCompare(b.patientName)),
    [profiles],
  );

  const resetForm = () => {
    setForm({
      patientName: "",
      patientId: "",
      gameName: "",
      gestureName: "",
      gestureKey: "",
    });
  };

  const handlePatientNameChange = (patientName: string) => {
    setForm((current) => ({
      ...current,
      patientName,
      patientId: current.patientId || slugifyPatientId(patientName),
    }));
  };

  const handleCreateProfile = () => {
    const patientName = form.patientName.trim();
    const patientId = form.patientId.trim() || slugifyPatientId(patientName);
    const gameName = form.gameName.trim() || "New Game";
    const gestureName = form.gestureName.trim() || "Wave";
    const gestureKey = form.gestureKey.trim() || "Space";

    if (!patientName || !patientId) {
      return;
    }

    if (profiles.some((profile) => profile.patientId === patientId)) {
      window.alert(`Profile already exists: ${patientId}`);
      return;
    }

    const newProfile: PatientProfile = {
      schemaVersion: 1,
      patientId,
      patientName,
      gameProfiles: [
        {
          gameName,
          gestures: [{ name: gestureName, key: gestureKey, threshold: 0.75 }],
        },
      ],
    };

    setProfiles((current) => [...current, newProfile]);
    setExpandedPatientId(patientId);
    setShowNewDialog(false);
    resetForm();
  };

  const handleExpandChange = (patientId: string, expanded: boolean) => {
    setExpandedPatientId(expanded ? patientId : null);
  };

  const handleLoadLastSession = (profile: PatientProfile) => {
    const gameName = profile.lastSessionGame;
    if (!gameName) {
      window.alert("No last session recorded for this patient.");
      return;
    }
    window.alert(`Load last session: ${profile.patientName} → ${gameName}`);
  };

  const handleGameAction = (
    profile: PatientProfile,
    gameName: string,
    action: "load" | "edit",
  ) => {
    window.alert(
      `${action === "load" ? "Load" : "Edit"} game profile: ${profile.patientName} → ${gameName}`,
    );
  };

  const handleDeleteProfile = (profile: PatientProfile) => {
    const confirmed = window.confirm(
      `Delete profile "${profile.patientName}" (${profile.patientId})? This cannot be undone.`,
    );
    if (!confirmed) {
      return;
    }

    setProfiles((current) =>
      current.filter((item) => item.patientId !== profile.patientId),
    );
    if (expandedPatientId === profile.patientId) {
      setExpandedPatientId(null);
    }
  };

  const handleAddGameProfile = (profile: PatientProfile) => {
    const gameName = window.prompt("Game profile name:", "New Game");
    if (!gameName?.trim()) {
      return;
    }

    setProfiles((current) =>
      current.map((item) =>
        item.patientId === profile.patientId
          ? {
              ...item,
              gameProfiles: [
                ...item.gameProfiles,
                {
                  gameName: gameName.trim(),
                  gestures: [{ name: "Wave", key: "Space", threshold: 0.75 }],
                },
              ],
            }
          : item,
      ),
    );
  };

  return (
    <div className={styles.page}>
      <header>
        <h1 className={styles.heading}>Patient &amp; Game Profiles</h1>
        <p className={styles.subheading}>
          One patient profile may contain multiple game mapping profiles. Each
          game profile holds all gesture-to-key bindings for that title.
        </p>
      </header>

      <div className={styles.list}>
        {sortedProfiles.length === 0 ? (
          <p className={styles.empty}>
            No profiles yet. Use ADD NEW to create one.
          </p>
        ) : (
          sortedProfiles.map((profile) => (
            <PatientCard
              key={profile.patientId}
              profile={profile}
              expanded={expandedPatientId === profile.patientId}
              onExpandChange={(expanded) =>
                handleExpandChange(profile.patientId, expanded)
              }
              onLoadLastSession={() => handleLoadLastSession(profile)}
              onGameLoad={(gameName) =>
                handleGameAction(profile, gameName, "load")
              }
              onGameEdit={(gameName) =>
                handleGameAction(profile, gameName, "edit")
              }
              onAddGameProfile={() => handleAddGameProfile(profile)}
              onDelete={() => handleDeleteProfile(profile)}
            />
          ))
        )}
      </div>

      <button
        type="button"
        className={styles.addNewButton}
        onClick={() => setShowNewDialog(true)}
      >
        ADD NEW
      </button>

      {showNewDialog ? (
        <div
          className={styles.dialogBackdrop}
          role="presentation"
          onClick={() => setShowNewDialog(false)}
        >
          <div
            className={styles.dialog}
            role="dialog"
            aria-modal="true"
            aria-labelledby="new-profile-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="new-profile-title" className={styles.dialogTitle}>
              Create New Profile
            </h2>

            <div className={styles.field}>
              <label htmlFor="patient-name">Patient name</label>
              <input
                id="patient-name"
                value={form.patientName}
                onChange={(event) =>
                  handlePatientNameChange(event.target.value)
                }
                placeholder="e.g. Patient C"
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="patient-id">Profile ID</label>
              <input
                id="patient-id"
                value={form.patientId}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    patientId: event.target.value,
                  }))
                }
                placeholder="e.g. patient-c"
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="game-name">First game name</label>
              <input
                id="game-name"
                value={form.gameName}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    gameName: event.target.value,
                  }))
                }
                placeholder="e.g. Celeste — Rehab Mode"
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="gesture-name">Gesture name</label>
              <input
                id="gesture-name"
                value={form.gestureName}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    gestureName: event.target.value,
                  }))
                }
                placeholder="e.g. Right Arm Raise"
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="gesture-key">Key</label>
              <input
                id="gesture-key"
                value={form.gestureKey}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    gestureKey: event.target.value,
                  }))
                }
                placeholder="e.g. ArrowUp"
              />
            </div>

            <div className={styles.dialogActions}>
              <button
                type="button"
                className={styles.dialogCancel}
                onClick={() => {
                  setShowNewDialog(false);
                  resetForm();
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                className={styles.dialogSubmit}
                onClick={handleCreateProfile}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default Profiles;
