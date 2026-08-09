import {
  SAMPLE_BINDINGS,
  SAMPLE_GESTURES,
  SAMPLE_PATIENTS,
  SAMPLE_PRESETS,
} from "@/data/sampleProfiles";
import type { DesktopState, RuntimeSettings } from "@/types/desktopState";
import type { Binding, Patient } from "@/types/profile";
import type { Readiness, ResolvedBinding } from "./appStateContext";

export const STORAGE_KEY = "human-controller/app-state/v2";

export const DEFAULT_SETTINGS: RuntimeSettings = {
  matchThreshold: 75,
  cooldown: 0.5,
  smoothing: 2,
  poseModel: "lite",
};

const copyBindings = (bindings: Binding[]): Binding[] =>
  bindings.map((binding) => ({ ...binding }));

export const initialState = (): DesktopState => ({
  gestures: SAMPLE_GESTURES.map((gesture) => ({ ...gesture })),
  bindings: copyBindings(SAMPLE_BINDINGS),
  presets: SAMPLE_PRESETS.map((preset) => ({
    ...preset,
    bindings: copyBindings(preset.bindings),
  })),
  selectedPatientId: null,
  activePresetId: null,
  patients: SAMPLE_PATIENTS.map((patient) => ({
    ...patient,
    keyBindings: { ...patient.keyBindings },
    matchThresholds: { ...patient.matchThresholds },
  })),
  settings: { ...DEFAULT_SETTINGS },
});

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

export const parseStoredState = (raw: string | null): DesktopState => {
  if (!raw) {
    return initialState();
  }
  try {
    const parsed: unknown = JSON.parse(raw);
    if (
      !isRecord(parsed) ||
      !Array.isArray(parsed.gestures) ||
      !Array.isArray(parsed.bindings)
    ) {
      return initialState();
    }
    const defaults = initialState();
    return {
      gestures: parsed.gestures as DesktopState["gestures"],
      bindings: parsed.bindings as DesktopState["bindings"],
      presets: Array.isArray(parsed.presets)
        ? (parsed.presets as DesktopState["presets"])
        : [],
      selectedPatientId:
        typeof parsed.selectedPatientId === "string"
          ? parsed.selectedPatientId
          : null,
      activePresetId:
        typeof parsed.activePresetId === "string"
          ? parsed.activePresetId
          : null,
      patients: Array.isArray(parsed.patients)
        ? (parsed.patients as DesktopState["patients"])
        : defaults.patients,
      settings: {
        ...DEFAULT_SETTINGS,
        ...(isRecord(parsed.settings)
          ? (parsed.settings as Partial<RuntimeSettings>)
          : {}),
      },
    };
  } catch {
    return initialState();
  }
};

export const clampPercentage = (value: unknown, fallback: number): number => {
  const numeric = Number(value);
  return Number.isFinite(numeric)
    ? Math.min(100, Math.max(0, numeric))
    : fallback;
};

export const sameBindings = (
  leftBindings: Binding[],
  rightBindings: Binding[],
  defaultThreshold: number,
): boolean => {
  if (leftBindings.length !== rightBindings.length) {
    return false;
  }
  const key = (binding: Binding) =>
    `${binding.gestureId}:${binding.key}:${clampPercentage(binding.matchThreshold, defaultThreshold)}`;
  const left = leftBindings.map(key).sort();
  const right = rightBindings.map(key).sort();
  return left.every((value, index) => value === right[index]);
};

export const bindingsForPatient = (
  patient: Patient | null | undefined,
  defaultThreshold: number,
): Binding[] =>
  patient
    ? Object.entries(patient.keyBindings).map(([gestureId, key]) => ({
        gestureId,
        key,
        matchThreshold: clampPercentage(
          patient.matchThresholds[gestureId],
          defaultThreshold,
        ),
      }))
    : [];

export const withSelectedPatientBindings = (
  current: DesktopState,
  bindings: Binding[],
  updatedAt = new Date().toISOString(),
): DesktopState => {
  const selectedPatientId = current.selectedPatientId;
  if (!selectedPatientId) {
    return { ...current, bindings };
  }
  const keyBindings = Object.fromEntries(
    bindings.map(({ gestureId, key }) => [gestureId, key]),
  );
  const matchThresholds = Object.fromEntries(
    bindings.map(({ gestureId, matchThreshold }) => [
      gestureId,
      clampPercentage(matchThreshold, current.settings.matchThreshold),
    ]),
  );
  return {
    ...current,
    bindings,
    patients: current.patients.map((patient) =>
      patient.patientId === selectedPatientId
        ? {
            ...patient,
            updatedAt,
            keyBindings,
            matchThresholds,
          }
        : patient,
    ),
  };
};

export const resolveBindings = (state: DesktopState): ResolvedBinding[] => {
  const gestureById = new Map(
    state.gestures.map((gesture) => [gesture.gestureId, gesture]),
  );
  return state.bindings.map((binding) => ({
    gesture: gestureById.get(binding.gestureId) ?? {
      gestureId: binding.gestureId,
      name: `Missing movement (${binding.gestureId})`,
      calibratedAt: null,
      matchScore: null,
    },
    key: binding.key,
    matchThreshold: clampPercentage(
      binding.matchThreshold,
      state.settings.matchThreshold,
    ),
  }));
};

export const readinessFor = (bindings: ResolvedBinding[]): Readiness => {
  const pending = bindings
    .filter((binding) => !binding.gesture.calibratedAt)
    .map((binding) => binding.gesture);
  return {
    total: bindings.length,
    recorded: bindings.length - pending.length,
    pending,
    isReady: bindings.length > 0 && pending.length === 0,
  };
};
