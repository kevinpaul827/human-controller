import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import {
  SAMPLE_BINDINGS,
  SAMPLE_GESTURES,
  SAMPLE_PATIENTS,
  SAMPLE_PRESETS,
} from "@/data/sampleProfiles";
import type { Binding, Gesture, Patient, Preset } from "@/types/profile";
import type { RuntimeSettings } from "@/types/desktopState";
import type { SavedRepResult } from "@/types/calibrate";
import { desktopStateBridge } from "@/services/desktopStateBridge";
import {
  AppStateContext,
  type Readiness,
  type ResolvedBinding,
} from "./appStateContext";

const STORAGE_KEY = "human-controller/app-state/v2";

const UNDO_WINDOW_MS = 30_000;

const newId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID().replace(/-/g, "")
    : Math.random().toString(16).slice(2).padEnd(32, "0");

type Persisted = {
  gestures: Gesture[];
  bindings: Binding[];
  presets: Preset[];
  selectedPatientId: string | null;
  activePresetId: string | null;
  patients: Patient[];
  settings: RuntimeSettings;
};

const DEFAULT_SETTINGS: RuntimeSettings = {
  matchThreshold: 75,
  holdDuration: 1.5,
  cooldown: 0.5,
  smoothing: 2,
};

const initialState = (): Persisted => ({
  gestures: SAMPLE_GESTURES,
  bindings: SAMPLE_BINDINGS,
  presets: SAMPLE_PRESETS,
  selectedPatientId: SAMPLE_PATIENTS[0]?.patientId ?? null,
  activePresetId: null,
  patients: SAMPLE_PATIENTS,
  settings: DEFAULT_SETTINGS,
});

const loadState = (): Persisted => {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return initialState();
    }
    const parsed = JSON.parse(raw) as Partial<Persisted>;
    if (!Array.isArray(parsed.gestures) || !Array.isArray(parsed.bindings)) {
      return initialState();
    }
    return {
      gestures: parsed.gestures,
      bindings: parsed.bindings,
      presets: parsed.presets ?? [],
      selectedPatientId: parsed.selectedPatientId ?? null,
      activePresetId: parsed.activePresetId ?? null,
      patients: Array.isArray(parsed.patients)
        ? parsed.patients
        : SAMPLE_PATIENTS,
      settings: { ...DEFAULT_SETTINGS, ...(parsed.settings ?? {}) },
    };
  } catch {
    return initialState();
  }
};

const sameBindings = (a: Binding[], b: Binding[], defaultThreshold: number) => {
  if (a.length !== b.length) {
    return false;
  }
  const key = (binding: Binding) =>
    `${binding.gestureId}:${binding.key}:${binding.matchThreshold ?? defaultThreshold}`;
  const left = [...a].map(key).sort();
  const right = [...b].map(key).sort();
  return left.every((value, index) => value === right[index]);
};

const AppStateProvider = ({ children }: { children: ReactNode }) => {
  const [state, setState] = useState<Persisted>(loadState);
  const [undoLabel, setUndoLabel] = useState<string | null>(null);
  const undoSnapshot = useRef<Persisted | null>(null);
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
      })
      .catch(() => {
        persistenceMode.current = "browser";
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
    (label: string, next: (current: Persisted) => Persisted) => {
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

  const bindings = useMemo<ResolvedBinding[]>(
    () =>
      state.bindings.flatMap((binding) => {
        const gesture = gestureById.get(binding.gestureId);
        return gesture
          ? [
              {
                gesture,
                key: binding.key,
                matchThreshold: Math.min(
                  100,
                  Math.max(
                    0,
                    Number(
                      binding.matchThreshold ?? state.settings.matchThreshold,
                    ),
                  ),
                ),
              },
            ]
          : [];
      }),
    [state.bindings, state.settings.matchThreshold, gestureById],
  );

  const unboundGestures = useMemo(() => {
    const bound = new Set(state.bindings.map((binding) => binding.gestureId));
    return state.gestures.filter((gesture) => !bound.has(gesture.gestureId));
  }, [state.gestures, state.bindings]);

  const readiness = useMemo<Readiness>(() => {
    const pending = bindings
      .filter((binding) => !binding.gesture.calibratedAt)
      .map((binding) => binding.gesture);

    return {
      total: bindings.length,
      recorded: bindings.length - pending.length,
      pending,
      isReady: bindings.length > 0 && pending.length === 0,
    };
  }, [bindings]);

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
      state.patients.find(
        (patient) => patient.patientId === state.selectedPatientId,
      ) ??
      state.patients[0] ??
      null,
    [state.selectedPatientId, state.patients],
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
        }));
        if (persistenceMode.current === "desktop") {
          void desktopStateBridge.deleteGesture(gestureId).catch(() => {});
        }
      },

      completeRecording: (previousGestureId: string, result: SavedRepResult) =>
        setState((current) => {
          const replaceId = (binding: Binding) =>
            binding.gestureId === previousGestureId
              ? { ...binding, gestureId: result.gestureId }
              : binding;
          return {
            ...current,
            gestures: current.gestures.map((gesture) =>
              gesture.gestureId === previousGestureId
                ? {
                    ...gesture,
                    gestureId: result.gestureId,
                    name: result.name,
                    matchScore: null,
                    calibratedAt: new Date().toISOString(),
                  }
                : gesture,
            ),
            bindings: current.bindings.map(replaceId),
            presets: current.presets.map((preset) => ({
              ...preset,
              bindings: preset.bindings.map(replaceId),
            })),
          };
        }),

      bindGesture: (gestureId: string, key: string) =>
        setState((current) => ({
          ...current,
          bindings: [
            ...current.bindings.filter(
              (binding) => binding.gestureId !== gestureId,
            ),
            {
              gestureId,
              key,
              matchThreshold: current.settings.matchThreshold,
            },
          ],
        })),

      rebindKey: (gestureId: string, key: string) =>
        setState((current) => ({
          ...current,
          bindings: current.bindings.map((binding) =>
            binding.gestureId === gestureId ? { ...binding, key } : binding,
          ),
        })),

      setBindingThreshold: (gestureId: string, threshold: number) =>
        setState((current) => ({
          ...current,
          bindings: current.bindings.map((binding) =>
            binding.gestureId === gestureId
              ? {
                  ...binding,
                  matchThreshold: Math.min(100, Math.max(0, threshold)),
                }
              : binding,
          ),
        })),

      unbindGesture: (gestureId: string) => {
        const name = gestureById.get(gestureId)?.name ?? "Movement";
        withUndo(`Removed ${name}`, (current) => ({
          ...current,
          bindings: current.bindings.filter(
            (binding) => binding.gestureId !== gestureId,
          ),
        }));
      },

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

        withUndo(`Loaded ${preset.name}`, (current) => ({
          ...current,
          bindings: preset.bindings,
          activePresetId: presetId,
        }));
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

      selectPatient: (patientId: string) => {
        if (persistenceMode.current === "desktop") {
          void desktopStateBridge
            .selectPatient(patientId)
            .then(setState)
            .catch(() => {});
        } else {
          setState((current) => ({ ...current, selectedPatientId: patientId }));
        }
      },

      createPatient: (patientName: string) => {
        const name = patientName.trim();
        if (!name) {
          return;
        }
        if (persistenceMode.current === "desktop") {
          void desktopStateBridge
            .createProfile(name)
            .then(setState)
            .catch(() => {});
        } else {
          const patientId = newId();
          setState((current) => ({
            ...current,
            patients: [...current.patients, { patientId, patientName: name }],
            selectedPatientId: patientId,
            activePresetId: null,
          }));
        }
      },

      saveSettings: (settings: RuntimeSettings) =>
        setState((current) => ({ ...current, settings })),

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
      withUndo,
      gestureById,
    ],
  );

  return (
    <AppStateContext.Provider value={value}>
      {children}
    </AppStateContext.Provider>
  );
};

export default AppStateProvider;
