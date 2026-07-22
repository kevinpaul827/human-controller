import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import CreateProfileDialog from "../components/CreateProfileDialog";
import PatientCard from "../components/PatientCard";
import { SAMPLE_GESTURES, SAMPLE_PROFILES } from "../data/sampleProfiles";
import useActiveProfile from "../hooks/useActiveProfile";
import profileBridge, {
  isProfileDesktopRuntime,
} from "../services/profileBridge";
import type { GestureSummary, PatientProfile } from "../types/profile";
import { ROUTES } from "../utils/constants";
import styles from "../styles/profiles.module.css";

const getErrorMessage = (error: unknown) =>
  error instanceof Error ? error.message : "The profile operation failed.";

const Profiles = () => {
  const navigate = useNavigate();
  const { activeProfile, clearActiveProfile, setActiveProfile } =
    useActiveProfile();
  const desktopRuntime = isProfileDesktopRuntime();
  const [profiles, setProfiles] = useState<PatientProfile[]>(
    desktopRuntime ? [] : SAMPLE_PROFILES,
  );
  const [gestures, setGestures] = useState<GestureSummary[]>(
    desktopRuntime ? [] : SAMPLE_GESTURES,
  );
  const [expandedPatientId, setExpandedPatientId] = useState<string | null>(
    null,
  );
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [loading, setLoading] = useState(desktopRuntime);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    if (!desktopRuntime) {
      return;
    }

    let active = true;
    void Promise.all([
      profileBridge.listProfiles(),
      profileBridge.listGestures(),
    ])
      .then(([loadedProfiles, loadedGestures]) => {
        if (!active) {
          return;
        }
        setProfiles(loadedProfiles);
        setGestures(loadedGestures);
      })
      .catch((error: unknown) => {
        if (active) {
          setPageError(getErrorMessage(error));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [desktopRuntime]);

  const sortedProfiles = useMemo(
    () =>
      [...profiles].sort((a, b) => a.patientName.localeCompare(b.patientName)),
    [profiles],
  );

  const replaceProfile = (updatedProfile: PatientProfile) => {
    setProfiles((current) =>
      current.map((profile) =>
        profile.patientId === updatedProfile.patientId
          ? updatedProfile
          : profile,
      ),
    );
  };

  const handleCreateProfile = async (patientName: string, notes: string) => {
    try {
      const createdProfile = desktopRuntime
        ? await profileBridge.createProfile(patientName, notes)
        : {
            schemaVersion: 2 as const,
            patientId: crypto.randomUUID(),
            patientName,
            notes,
            updatedAt: new Date().toISOString(),
            keyBindings: {},
          };
      setProfiles((current) => [...current, createdProfile]);
      setExpandedPatientId(createdProfile.patientId);
      setShowNewDialog(false);
      setPageError(null);
      return null;
    } catch (error) {
      return getErrorMessage(error);
    }
  };

  const handleSetBinding = async (
    profile: PatientProfile,
    gestureId: string,
    key: string,
  ) => {
    try {
      const updatedProfile = desktopRuntime
        ? await profileBridge.setKeyBinding(profile.patientId, gestureId, key)
        : {
            ...profile,
            updatedAt: new Date().toISOString(),
            keyBindings: { ...profile.keyBindings, [gestureId]: key },
          };
      replaceProfile(updatedProfile);
      setPageError(null);
      return null;
    } catch (error) {
      return getErrorMessage(error);
    }
  };

  const handleRemoveBinding = async (
    profile: PatientProfile,
    gestureId: string,
  ) => {
    try {
      const updatedProfile = desktopRuntime
        ? await profileBridge.removeKeyBinding(profile.patientId, gestureId)
        : (() => {
            const keyBindings = { ...profile.keyBindings };
            delete keyBindings[gestureId];
            return {
              ...profile,
              updatedAt: new Date().toISOString(),
              keyBindings,
            };
          })();
      replaceProfile(updatedProfile);
      setPageError(null);
      return null;
    } catch (error) {
      return getErrorMessage(error);
    }
  };

  const handleDeleteProfile = async (profile: PatientProfile) => {
    const confirmed = window.confirm(
      `Delete the profile for ${profile.patientName}? This cannot be undone.`,
    );
    if (!confirmed) {
      return;
    }

    try {
      if (desktopRuntime) {
        await profileBridge.deleteProfile(profile.patientId);
      }
      setProfiles((current) =>
        current.filter((item) => item.patientId !== profile.patientId),
      );
      if (expandedPatientId === profile.patientId) {
        setExpandedPatientId(null);
      }
      if (activeProfile?.patientId === profile.patientId) {
        clearActiveProfile();
      }
      setPageError(null);
    } catch (error) {
      setPageError(getErrorMessage(error));
    }
  };

  const openProfileRoute = (
    profile: PatientProfile,
    route: typeof ROUTES.calibrate | typeof ROUTES.session,
  ) => {
    setActiveProfile(profile);
    navigate(route);
  };

  return (
    <div className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.heading}>Patient Profiles</h1>
          <p className={styles.subheading}>
            Keep each patient&apos;s calibrated movements and game controls in
            one place.
          </p>
        </div>
        <button
          type="button"
          className={styles.addNewButton}
          onClick={() => setShowNewDialog(true)}
        >
          + New profile
        </button>
      </header>

      <p className={styles.saveNotice}>
        Changes to profiles and key bindings are saved automatically.
      </p>

      {pageError ? (
        <p className={styles.pageError} role="alert">
          {pageError}
        </p>
      ) : null}

      {loading ? (
        <p className={styles.empty}>Loading patient profiles…</p>
      ) : (
        <div className={styles.list}>
          {sortedProfiles.length === 0 ? (
            <p className={styles.empty}>
              No patient profiles yet. Create one to begin calibration.
            </p>
          ) : (
            sortedProfiles.map((profile) => (
              <PatientCard
                key={profile.patientId}
                profile={profile}
                gestures={gestures}
                expanded={expandedPatientId === profile.patientId}
                onExpandChange={(expanded) =>
                  setExpandedPatientId(expanded ? profile.patientId : null)
                }
                onSetBinding={(gestureId, key) =>
                  handleSetBinding(profile, gestureId, key)
                }
                onRemoveBinding={(gestureId) =>
                  handleRemoveBinding(profile, gestureId)
                }
                onCalibrate={() => openProfileRoute(profile, ROUTES.calibrate)}
                onStartSession={() => openProfileRoute(profile, ROUTES.session)}
                onDelete={() => handleDeleteProfile(profile)}
              />
            ))
          )}
        </div>
      )}

      {showNewDialog ? (
        <CreateProfileDialog
          onClose={() => setShowNewDialog(false)}
          onCreate={handleCreateProfile}
        />
      ) : null}
    </div>
  );
};

export default Profiles;
