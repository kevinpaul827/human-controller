import type {
  DesktopState,
  PoseModel,
  RuntimeSettings,
} from "@/types/desktopState";
import type { Binding, Gesture, Patient, Preset } from "@/types/profile";
import type { Readiness, ResolvedBinding } from "./appStateContext";

export const STORAGE_KEY = "human-controller/app-state/v2";

export const DEFAULT_SETTINGS: RuntimeSettings = {
  matchThreshold: 75,
  cooldown: 0.5,
  smoothing: 2,
  poseModel: "lite",
};

export const initialState = (): DesktopState => ({
  gestures: [],
  bindings: [],
  presets: [],
  selectedPatientId: null,
  activePresetId: null,
  patients: [],
  settings: { ...DEFAULT_SETTINGS },
});

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const nonEmptyString = (value: unknown): string | null =>
  typeof value === "string" && value.trim() ? value.trim() : null;

const optionalString = (value: unknown): string | null =>
  typeof value === "string" ? value : null;

const finiteNumber = (value: unknown): number | null =>
  typeof value === "number" && Number.isFinite(value) ? value : null;

const boundedNumber = (
  value: unknown,
  fallback: number,
  minimum: number,
  maximum: number,
): number => {
  const numeric = finiteNumber(value);
  return numeric === null
    ? fallback
    : Math.min(maximum, Math.max(minimum, numeric));
};

const parseStringRecord = (value: unknown): Record<string, string> => {
  if (!isRecord(value)) return {};
  return Object.fromEntries(
    Object.entries(value).flatMap(([key, entryValue]) => {
      const normalizedKey = key.trim();
      const normalizedValue = nonEmptyString(entryValue);
      return normalizedKey && normalizedValue
        ? [[normalizedKey, normalizedValue]]
        : [];
    }),
  );
};

const parseThresholdRecord = (
  value: unknown,
  fallback: number,
): Record<string, number> => {
  if (!isRecord(value)) return {};
  return Object.fromEntries(
    Object.entries(value).flatMap(([key, threshold]) =>
      key.trim() && finiteNumber(threshold) !== null
        ? [[key, clampPercentage(threshold, fallback)]]
        : [],
    ),
  );
};

const parseGesture = (value: unknown): Gesture | null => {
  if (!isRecord(value)) return null;
  const gestureId = nonEmptyString(value.gestureId);
  const name = nonEmptyString(value.name);
  if (!gestureId || !name) return null;

  return {
    gestureId,
    name,
    calibratedAt: optionalString(value.calibratedAt),
    matchScore: finiteNumber(value.matchScore),
  };
};

const parseBinding = (value: unknown, fallback: number): Binding | null => {
  if (!isRecord(value)) return null;
  const gestureId = nonEmptyString(value.gestureId);
  const key = nonEmptyString(value.key);
  if (!gestureId || !key) return null;

  const threshold = finiteNumber(value.matchThreshold);
  return {
    gestureId,
    key,
    ...(threshold === null
      ? {}
      : { matchThreshold: clampPercentage(threshold, fallback) }),
  };
};

const parseBindings = (value: unknown, fallback: number): Binding[] =>
  Array.isArray(value)
    ? value.flatMap((entry) => {
        const binding = parseBinding(entry, fallback);
        return binding ? [binding] : [];
      })
    : [];

const parsePreset = (value: unknown, fallback: number): Preset | null => {
  if (!isRecord(value)) return null;
  const presetId = nonEmptyString(value.presetId);
  const name = nonEmptyString(value.name);
  if (!presetId || !name || !Array.isArray(value.bindings)) return null;
  return {
    presetId,
    name,
    bindings: parseBindings(value.bindings, fallback),
  };
};

const parsePatient = (value: unknown, fallback: number): Patient | null => {
  if (!isRecord(value) || value.schemaVersion !== 2) return null;
  const patientId = nonEmptyString(value.patientId);
  const patientName = nonEmptyString(value.patientName);
  const notes = optionalString(value.notes);
  const updatedAt = optionalString(value.updatedAt);
  if (!patientId || !patientName || notes === null || updatedAt === null) {
    return null;
  }
  return {
    schemaVersion: 2,
    patientId,
    patientName,
    notes,
    updatedAt,
    keyBindings: parseStringRecord(value.keyBindings),
    matchThresholds: parseThresholdRecord(value.matchThresholds, fallback),
  };
};

const parseSettings = (value: unknown): RuntimeSettings => {
  const settings = isRecord(value) ? value : {};
  const poseModels: PoseModel[] = ["lite", "full", "heavy"];
  const poseModel = poseModels.find((model) => model === settings.poseModel);
  return {
    matchThreshold: boundedNumber(
      settings.matchThreshold,
      DEFAULT_SETTINGS.matchThreshold,
      0,
      100,
    ),
    cooldown: boundedNumber(
      settings.cooldown,
      DEFAULT_SETTINGS.cooldown,
      0,
      10,
    ),
    smoothing: Math.trunc(
      boundedNumber(settings.smoothing, DEFAULT_SETTINGS.smoothing, 0, 4),
    ),
    poseModel: poseModel ?? DEFAULT_SETTINGS.poseModel,
  };
};

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
    const settings = parseSettings(parsed.settings);
    return {
      gestures: parsed.gestures.flatMap((entry) => {
        const gesture = parseGesture(entry);
        return gesture ? [gesture] : [];
      }),
      bindings: parseBindings(parsed.bindings, settings.matchThreshold),
      presets: Array.isArray(parsed.presets)
        ? parsed.presets.flatMap((entry) => {
            const preset = parsePreset(entry, settings.matchThreshold);
            return preset ? [preset] : [];
          })
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
        ? parsed.patients.flatMap((entry) => {
            const patient = parsePatient(entry, settings.matchThreshold);
            return patient ? [patient] : [];
          })
        : [],
      settings,
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
