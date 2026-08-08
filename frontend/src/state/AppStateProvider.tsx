import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import type { Binding, Gesture, Patient } from "@/types/profile";
import type { DesktopState, RuntimeSettings } from "@/types/desktopState";
import type { SavedRepResult } from "@/types/calibrate";
import { desktopStateBridge } from "@/services/desktopStateBridge";
import { AppStateContext } from "./appStateContext";
import {
  bindingsForPatient,
  parseStoredState,
  readinessFor,
  resolveBindings,
  sameBindings,
  STORAGE_KEY,
  withSelectedPatientBindings,
} from "./appStateModel";

const UNDO_WINDOW_MS = 30_000;

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID().replace(/-/g, "")
    : Math.random().toString(16).slice(2).padEnd(32, "0");

const loadState = (): DesktopState =>
  parseStoredState(window.localStorage.getItem(STORAGE_KEY));

const AppStateProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<DesktopState>(loadState);
  const [persistenceReady, setPersistenceReady] = useState(false);
  const [undoLabel, setUndoLabel] = useState<string | null>(null);
  const undoSnapshot = useRef<DesktopState | null>(null);
  const undoTimer = useRef<number | null>(null);
  const persistenceMode = useRef<"unknown" | "desktop" | "browser">("unknown");

  useEffect(() => {
    let active = true;
    void desktopStateBridge
      .getState()
      .then((desktopState) => {
        if (!active) return;
        persistenceMode.current = "desktop";
        setState(desktopState);
        setPersistenceReady(true);
      })
      .catch(() => {
        if (!active) return;
        persistenceMode.current = "browser";
        setPersistenceReady(true);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (persistenceMode.current === "unknown") return;
    if (persistenceMode.current === "desktop") {
      const timer = window.setTimeout(() => {
        void desktopStateBridge.saveState(state).catch(() => {});
      }, 100);
      return () => window.clearTimeout(timer);
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      return;
    }
  }, [state]);

  useEffect(
    () => () => {
      if (undoTimer.current !== null) {
        window.clearTimeout(undoTimer.current);
      }
    },
    [],
  );

  const withUndo = useCallback(
    (label: string, next: (current: DesktopState) => DesktopState) => {
      setState((current) => {
        undoSnapshot.current = current;
        return next(current);
      });
      setUndoLabel(label);

      if (undoTimer.current !== null) {
        window.clearTimeout(undoTimer.current);
      }
      undoTimer.current = window.setTimeout(() => {
        setUndoLabel(null);
        undoSnapshot.current = null;
        undoTimer.current = null;
      }, UNDO_WINDOW_MS);
    },
    [],
  );

  const gestureById = useMemo(
    () =>
      new Map(state.gestures.map((gesture) => [gesture.gestureId, gesture])),
    [state.gestures],
  );

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

  const updateSetting = useCallback(
    <K extends keyof RuntimeSettings>(key: K, setting: RuntimeSettings[K]) =>
      setState((current) =>
        current.settings[key] === setting
          ? current
          : {
              ...current,
              settings: { ...current.settings, [key]: setting },
            },
      ),
    [],
  );

  const value = useMemo(
    () => ({
      gestures: state.gestures,
      bindings,
      unboundGestures,
      presets: state.presets,
      patients: state.patients,
      selectedPatient,
      activePreset,
      hasUnsavedChanges,
      readiness,
      undoLabel,
      settings: state.settings,

      addGesture: (name: string) => {
        const gestureId = newId();
        setState((current) => ({
          ...current,
          gestures: [
            ...current.gestures,
            { gestureId, name, calibratedAt: null, matchScore: null },
          ],
        }));
        return gestureId;
      },

      renameGesture: (gestureId: string, name: string) =>
        setState((current) => ({
          ...current,
          gestures: current.gestures.map((gesture) =>
            gesture.gestureId === gestureId ? { ...gesture, name } : gesture,
          ),
        })),

      deleteGesture: (gestureId: string) => {
        setState((current) => ({
          ...current,
          gestures: current.gestures.filter(
            (gesture) => gesture.gestureId !== gestureId,
          ),
          bindings: current.bindings.filter(
            (binding) => binding.gestureId !== gestureId,
          ),
          presets: current.presets.map((preset) => ({
            ...preset,
            bindings: preset.bindings.filter(
              (binding) => binding.gestureId !== gestureId,
            ),
          })),
          patients: current.patients.map((patient) => {
            const keyBindings = { ...patient.keyBindings };
            const matchThresholds = { ...patient.matchThresholds };
            delete keyBindings[gestureId];
            delete matchThresholds[gestureId];
            return { ...patient, keyBindings, matchThresholds };
          }),
        }));
        if (persistenceMode.current === "desktop") {
          void desktopStateBridge
            .deleteGesture(gestureId)
            .then(setState)
            .catch(() => {});
        }
      },

      completeRecording: (previousGestureId: string, result: SavedRepResult) =>
        setState((current) => {
          const replaceId = (binding: Binding) =>
            binding.gestureId === previousGestureId
              ? { ...binding, gestureId: result.gestureId }
              : binding;
          const nextBindings = current.bindings.map(replaceId);
          const recordedGesture: Gesture = {
            gestureId: result.gestureId,
            name: result.name,
            matchScore: null,
            calibratedAt: new Date().toISOString(),
          };
          const nextGestures = current.gestures.some(
            (gesture) => gesture.gestureId === previousGestureId,
          )
            ? current.gestures.map((gesture) =>
                gesture.gestureId === previousGestureId
                  ? recordedGesture
                  : gesture,
              )
            : [...current.gestures, recordedGesture];
          const next = {
            ...current,
            gestures: nextGestures,
            bindings: nextBindings,
            presets: current.presets.map((preset) => ({
              ...preset,
              bindings: preset.bindings.map(replaceId),
            })),
          };
          return withSelectedPatientBindings(next, nextBindings);
        }),

      bindGesture: (gestureId: string, key: string) =>
        setState((current) => {
          const nextBindings = [
            ...current.bindings.filter(
              (binding) => binding.gestureId !== gestureId,
            ),
            {
              gestureId,
              key,
              matchThreshold: current.settings.matchThreshold,
            },
          ];
          return withSelectedPatientBindings(current, nextBindings);
        }),

      rebindKey: (gestureId: string, key: string) =>
        setState((current) => {
          const nextBindings = current.bindings.map((binding) =>
            binding.gestureId === gestureId ? { ...binding, key } : binding,
          );
          return withSelectedPatientBindings(current, nextBindings);
        }),

      setBindingThreshold: (gestureId: string, threshold: number) =>
        setState((current) => {
          const nextBindings = current.bindings.map((binding) =>
            binding.gestureId === gestureId
              ? {
                  ...binding,
                  matchThreshold: Math.min(100, Math.max(0, threshold)),
                }
              : binding,
          );
          return withSelectedPatientBindings(current, nextBindings);
        }),

      unbindGesture: (gestureId: string) => {
        const name = gestureById.get(gestureId)?.name ?? "Movement";
        withUndo(`Removed ${name}`, (current) => {
          const nextBindings = current.bindings.filter(
            (binding) => binding.gestureId !== gestureId,
          );
          return withSelectedPatientBindings(current, nextBindings);
        });
      },

      setPatientBinding: (patientId: string, gestureId: string, key: string) =>
        setState((current) => {
          const patients = current.patients.map((patient) =>
            patient.patientId === patientId
              ? {
                  ...patient,
                  updatedAt: new Date().toISOString(),
                  keyBindings: { ...patient.keyBindings, [gestureId]: key },
                  matchThresholds: {
                    ...patient.matchThresholds,
                    [gestureId]:
                      patient.matchThresholds[gestureId] ??
                      current.settings.matchThreshold,
                  },
                }
              : patient,
          );
          if (current.selectedPatientId !== patientId) {
            return { ...current, patients };
          }
          const patient = patients.find((item) => item.patientId === patientId);
          return {
            ...current,
            patients,
            bindings: bindingsForPatient(
              patient,
              current.settings.matchThreshold,
            ),
          };
        }),

      removePatientBinding: (patientId: string, gestureId: string) =>
        setState((current) => {
          const patients = current.patients.map((patient) => {
            if (patient.patientId !== patientId) {
              return patient;
            }
            const keyBindings = { ...patient.keyBindings };
            const matchThresholds = { ...patient.matchThresholds };
            delete keyBindings[gestureId];
            delete matchThresholds[gestureId];
            return {
              ...patient,
              updatedAt: new Date().toISOString(),
              keyBindings,
              matchThresholds,
            };
          });
          if (current.selectedPatientId !== patientId) {
            return { ...current, patients };
          }
          const patient = patients.find((item) => item.patientId === patientId);
          return {
            ...current,
            patients,
            bindings: bindingsForPatient(
              patient,
              current.settings.matchThreshold,
            ),
          };
        }),

      savePreset: (name: string) =>
        setState((current) => {
          const existing = current.presets.find(
            (preset) => preset.name.toLowerCase() === name.toLowerCase(),
          );
          if (existing) {
            return {
              ...current,
              activePresetId: existing.presetId,
              presets: current.presets.map((preset) =>
                preset.presetId === existing.presetId
                  ? { ...preset, bindings: current.bindings }
                  : preset,
              ),
            };
          }

          const presetId = newId();
          return {
            ...current,
            activePresetId: presetId,
            presets: [
              ...current.presets,
              { presetId, name, bindings: current.bindings },
            ],
          };
        }),

      loadPreset: (presetId: string) => {
        const preset = state.presets.find((item) => item.presetId === presetId);
        if (!preset) {
          return;
        }

        withUndo(`Loaded ${preset.name}`, (current) =>
          withSelectedPatientBindings(
            { ...current, activePresetId: presetId },
            preset.bindings,
          ),
        );
      },

      deletePreset: (presetId: string) => {
        const name =
          state.presets.find((preset) => preset.presetId === presetId)?.name ??
          "Preset";
        withUndo(`Deleted ${name}`, (current) => ({
          ...current,
          presets: current.presets.filter(
            (preset) => preset.presetId !== presetId,
          ),
          activePresetId:
            current.activePresetId === presetId ? null : current.activePresetId,
        }));
      },

      selectPatient: async (patientId: string) => {
        if (persistenceMode.current === "desktop") {
          const next = await desktopStateBridge.selectPatient(patientId);
          setState(next);
        } else {
          setState((current) => {
            const patient = current.patients.find(
              (item) => item.patientId === patientId,
            );
            if (!patient) {
              return current;
            }
            return {
              ...current,
              selectedPatientId: patientId,
              activePresetId: null,
              bindings: bindingsForPatient(
                patient,
                current.settings.matchThreshold,
              ),
            };
          });
        }
      },

      createPatient: async (patientName: string, notes = "") => {
        const name = patientName.trim();
        if (!name) {
          return null;
        }
        if (persistenceMode.current === "desktop") {
          const next = await desktopStateBridge.createProfile(name, notes);
          setState(next);
          return (
            next.patients.find(
              (patient) => patient.patientId === next.selectedPatientId,
            ) ?? null
          );
        }

        const patientId = newId();
        const patient: Patient = {
          schemaVersion: 2,
          patientId,
          patientName: name,
          notes: notes.trim(),
          updatedAt: new Date().toISOString(),
          keyBindings: {},
          matchThresholds: {},
        };
        setState((current) => ({
          ...current,
          patients: [...current.patients, patient],
          selectedPatientId: patientId,
          activePresetId: null,
          bindings: [],
        }));
        return patient;
      },

      deletePatient: async (patientId: string) => {
        if (persistenceMode.current === "desktop") {
          const next = await desktopStateBridge.deleteProfile(patientId);
          setState(next);
          return;
        }
        setState((current) => {
          const patients = current.patients.filter(
            (patient) => patient.patientId !== patientId,
          );
          const deletingSelected = current.selectedPatientId === patientId;
          return {
            ...current,
            patients,
            selectedPatientId: deletingSelected
              ? null
              : current.selectedPatientId,
            activePresetId: deletingSelected ? null : current.activePresetId,
            bindings: deletingSelected ? [] : current.bindings,
          };
        });
      },

      clearPatientSelection: async () => {
        if (persistenceMode.current === "desktop") {
          const next = await desktopStateBridge.clearPatientSelection();
          setState(next);
        } else {
          setState((current) => ({
            ...current,
            selectedPatientId: null,
            activePresetId: null,
            bindings: [],
          }));
        }
      },

      refreshState: async () => {
        if (persistenceMode.current === "desktop") {
          setState(await desktopStateBridge.getState());
        }
      },

      updateSetting,

      undo: () => {
        if (undoSnapshot.current) {
          setState(undoSnapshot.current);
          undoSnapshot.current = null;
        }
        setUndoLabel(null);
      },

      dismissUndo: () => {
        undoSnapshot.current = null;
        setUndoLabel(null);
      },
    }),
    [
      state.gestures,
      state.presets,
      state.patients,
      state.settings,
      bindings,
      unboundGestures,
      selectedPatient,
      activePreset,
      hasUnsavedChanges,
      readiness,
      undoLabel,
      updateSetting,
      withUndo,
      gestureById,
    ],
  );

  return (
    <AppStateContext.Provider value={value}>
      {persistenceReady ? children : null}
    </AppStateContext.Provider>
  );
};

export default AppStateProvider;
