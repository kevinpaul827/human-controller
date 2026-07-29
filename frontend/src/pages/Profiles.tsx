import { useEffect, useMemo, useState } from "react";
import { Plus, Users } from "lucide-react";
import { useNavigate } from "react-router-dom";
import CreateProfileDialog from "../components/CreateProfileDialog";
import Page from "@/components/Page";
import PatientCard from "../components/PatientCard";
import { BrutalButton } from "@/components/ui/brutal-button";
import { BrutalCard } from "@/components/ui/brutal-card";
import profileBridge, {
  isProfileDesktopRuntime,
} from "../services/profileBridge";
import { useAppState } from "@/state/appStateContext";
import type { GestureSummary, PatientProfile } from "../types/profile";
import { ROUTES } from "../utils/constants";

const getErrorMessage = (error: unknown) =>
  error instanceof Error ? error.message : "The profile operation failed.";

const Profiles = () => {
  const navigate = useNavigate();
  const {
    patients,
    gestures: stateGestures,
    selectPatient,
    createPatient,
    deletePatient,
    setPatientBinding,
    removePatientBinding,
    refreshState,
  } = useAppState();
  const desktopRuntime = isProfileDesktopRuntime();
  const [profiles, setProfiles] = useState<PatientProfile[]>(patients);
  const [gestures, setGestures] = useState<GestureSummary[]>(stateGestures);
  const [expandedPatientId, setExpandedPatientId] = useState<string | null>(
    null,
  );
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [loading, setLoading] = useState(desktopRuntime);
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    if (!desktopRuntime) {
      setProfiles(patients);
      setGestures(stateGestures);
      return;
    }

    let active = true;
    setLoading(true);
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
        setPageError(null);
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
  }, [desktopRuntime, stateGestures, patients]);

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
        : await createPatient(patientName, notes);
      if (!createdProfile) return "The profile could not be created.";
      setProfiles((current) => [...current, createdProfile]);
      setExpandedPatientId(createdProfile.patientId);
      setShowNewDialog(false);
      setPageError(null);
      if (desktopRuntime) await refreshState();
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
      if (desktopRuntime) {
        const updatedProfile = await profileBridge.setKeyBinding(
          profile.patientId,
          gestureId,
          key,
        );
        replaceProfile(updatedProfile);
        await refreshState();
      } else {
        setPatientBinding(profile.patientId, gestureId, key);
      }
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
      if (desktopRuntime) {
        const updatedProfile = await profileBridge.removeKeyBinding(
          profile.patientId,
          gestureId,
        );
        replaceProfile(updatedProfile);
        await refreshState();
      } else {
        removePatientBinding(profile.patientId, gestureId);
      }
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
        await refreshState();
      } else {
        await deletePatient(profile.patientId);
      }
      setProfiles((current) =>
        current.filter((item) => item.patientId !== profile.patientId),
      );
      if (expandedPatientId === profile.patientId) {
        setExpandedPatientId(null);
      }
      setPageError(null);
    } catch (error) {
      setPageError(getErrorMessage(error));
    }
  };

  const openProfileRoute = async (
    profile: PatientProfile,
    route: typeof ROUTES.calibrate | typeof ROUTES.session,
  ) => {
    try {
      await selectPatient(profile.patientId);
      navigate(route);
    } catch (error) {
      setPageError(getErrorMessage(error));
    }
  };

  return (
    <Page>
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl">Patient profiles</h1>
          <p className="mt-1 text-sm font-semibold text-muted-foreground">
            Manage each patient&apos;s movement controls and session setup.
          </p>
        </div>
        <BrutalButton size="lg" onClick={() => setShowNewDialog(true)}>
          <Plus aria-hidden="true" />
          Create profile
        </BrutalButton>
      </header>

      {pageError ? (
        <p className="text-sm font-bold text-destructive" role="alert">
          {pageError}
        </p>
      ) : null}

      {loading ? (
        <BrutalCard className="items-center justify-center p-10">
          <p className="font-semibold text-muted-foreground">
            Loading profiles…
          </p>
        </BrutalCard>
      ) : sortedProfiles.length ? (
        <div className="space-y-5">
          {sortedProfiles.map((profile) => (
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
              onCalibrate={() =>
                void openProfileRoute(profile, ROUTES.calibrate)
              }
              onStartSession={() =>
                void openProfileRoute(profile, ROUTES.session)
              }
              onDelete={() => handleDeleteProfile(profile)}
            />
          ))}
        </div>
      ) : (
        <BrutalCard className="items-center justify-center gap-4 p-10 text-center">
          <Users className="size-10" aria-hidden="true" />
          <div>
            <h2 className="text-lg font-bold">No patient profiles</h2>
            <p className="mt-1 text-sm font-semibold text-muted-foreground">
              Create a profile before starting calibration or a session.
            </p>
          </div>
          <BrutalButton onClick={() => setShowNewDialog(true)}>
            <Plus aria-hidden="true" />
            Create profile
          </BrutalButton>
        </BrutalCard>
      )}

      {showNewDialog ? (
        <CreateProfileDialog
          open
          onClose={() => setShowNewDialog(false)}
          onCreate={handleCreateProfile}
        />
      ) : null}
    </Page>
  );
};

export default Profiles;
