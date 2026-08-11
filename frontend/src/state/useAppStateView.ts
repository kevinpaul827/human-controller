import { useMemo } from "react";

import type { DesktopState } from "@/types/desktopState";
import type { AppStateSnapshot } from "./appStateContext";
import { readinessFor, resolveBindings, sameBindings } from "./appStateModel";

type AppStateView = Omit<AppStateSnapshot, "undoLabel">;

/** Builds the read-only view exposed by AppStateContext from persisted state. */
export const useAppStateView = (state: DesktopState): AppStateView => {
  const bindings = useMemo(() => resolveBindings(state), [state]);

  const unboundGestures = useMemo(() => {
    const bound = new Set(state.bindings.map((binding) => binding.gestureId));
    return state.gestures.filter((gesture) => !bound.has(gesture.gestureId));
  }, [state.gestures, state.bindings]);

  const readiness = useMemo(() => readinessFor(bindings), [bindings]);

  const activePreset = useMemo(
    () =>
      state.presets.find(
        (preset) => preset.presetId === state.activePresetId,
      ) ?? null,
    [state.presets, state.activePresetId],
  );

  const hasUnsavedChanges = useMemo(
    () =>
      activePreset !== null &&
      !sameBindings(
        activePreset.bindings,
        state.bindings,
        state.settings.matchThreshold,
      ),
    [activePreset, state.bindings, state.settings.matchThreshold],
  );

  const selectedPatient = useMemo(
    () =>
      state.selectedPatientId
        ? (state.patients.find(
            (patient) => patient.patientId === state.selectedPatientId,
          ) ?? null)
        : null,
    [state.selectedPatientId, state.patients],
  );

  return {
    gestures: state.gestures,
    bindings,
    unboundGestures,
    presets: state.presets,
    patients: state.patients,
    selectedPatient,
    activePreset,
    hasUnsavedChanges,
    readiness,
    settings: state.settings,
  };
};
