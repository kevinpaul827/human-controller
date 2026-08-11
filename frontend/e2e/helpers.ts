import { expect } from "@playwright/test";
import type { Page } from "@playwright/test";

export type AppState = {
  gestures: Array<{
    gestureId: string;
    name: string;
    calibratedAt: string | null;
    matchScore: number | null;
  }>;
  bindings: Array<{
    gestureId: string;
    key: string;
    matchThreshold?: number;
  }>;
  presets: Array<{
    presetId: string;
    name: string;
    bindings: Array<{
      gestureId: string;
      key: string;
      matchThreshold?: number;
    }>;
  }>;
  selectedPatientId: string | null;
  activePresetId: string | null;
  patients: Array<{
    schemaVersion: 2;
    patientId: string;
    patientName: string;
    notes: string;
    updatedAt: string;
    keyBindings: Record<string, string>;
    matchThresholds: Record<string, number>;
  }>;
  settings: {
    matchThreshold: number;
    cooldown: number;
    smoothing: number;
    poseModel: "lite" | "full" | "heavy";
  };
};

export type GestureState = AppState["gestures"][number];
export type BindingState = AppState["bindings"][number];
export type PresetState = AppState["presets"][number];
export type PatientState = AppState["patients"][number];

type AppStateOverrides = Partial<Omit<AppState, "settings">> & {
  settings?: Partial<AppState["settings"]>;
};

type AppStatePredicate = (
  state: AppState,
) => boolean | void | Promise<boolean | void>;

const STORAGE_KEY = "human-controller/app-state/v2";
const SEED_MARKER_KEY = "human-controller/e2e-state-seeded";
const DEFAULT_UPDATED_AT = "2026-01-01T00:00:00.000Z";

let factorySequence = 0;

const nextFactoryId = (prefix: string) => `${prefix}-${++factorySequence}`;

export const createGesture = (
  overrides: Partial<GestureState> = {},
): GestureState => ({
  gestureId: nextFactoryId("gesture"),
  name: "Test movement",
  calibratedAt: null,
  matchScore: null,
  ...overrides,
});

export const createBinding = (
  overrides: Partial<BindingState> = {},
): BindingState => ({
  gestureId: nextFactoryId("gesture"),
  key: "A",
  matchThreshold: 75,
  ...overrides,
});

export const createPreset = (
  overrides: Partial<PresetState> = {},
): PresetState => ({
  presetId: nextFactoryId("preset"),
  name: "Test preset",
  bindings: [],
  ...overrides,
});

export const createPatient = (
  overrides: Partial<PatientState> = {},
): PatientState => ({
  schemaVersion: 2,
  patientId: nextFactoryId("patient"),
  patientName: "Test patient",
  notes: "",
  updatedAt: DEFAULT_UPDATED_AT,
  keyBindings: {},
  matchThresholds: {},
  ...overrides,
});

export const createAppState = (
  overrides: AppStateOverrides = {},
): AppState => ({
  gestures: [],
  bindings: [],
  presets: [],
  selectedPatientId: null,
  activePresetId: null,
  patients: [],
  ...overrides,
  settings: {
    matchThreshold: 75,
    cooldown: 0.5,
    smoothing: 2,
    poseModel: "lite",
    ...overrides.settings,
  },
});

/**
 * Seeds browser fallback state before React initializes. The session marker is
 * retained across reloads, so mutations written by the app are not replaced by
 * the original fixture on later navigations in the same tab.
 */
export const seedAppState = async (page: Page, state: AppState) => {
  await page.addInitScript(
    ({ storageKey, markerKey, appState }) => {
      if (window.sessionStorage.getItem(markerKey)) return;
      window.localStorage.setItem(storageKey, JSON.stringify(appState));
      window.sessionStorage.setItem(markerKey, "true");
    },
    { storageKey: STORAGE_KEY, markerKey: SEED_MARKER_KEY, appState: state },
  );
};

export const readAppState = async (page: Page): Promise<AppState> =>
  page.evaluate((storageKey) => {
    const rawState = window.localStorage.getItem(storageKey);
    if (!rawState) {
      throw new Error(`No app state found in localStorage at ${storageKey}`);
    }
    return JSON.parse(rawState) as AppState;
  }, STORAGE_KEY);

export const waitForAppState = async (
  page: Page,
  predicate: AppStatePredicate,
): Promise<AppState> => {
  let latestState: AppState | undefined;

  await expect
    .poll(async () => {
      latestState = await readAppState(page);
      try {
        return (await predicate(latestState)) !== false;
      } catch {
        return false;
      }
    })
    .toBe(true);

  return latestState ?? readAppState(page);
};

export const openWithAppState = async (
  page: Page,
  path: string,
  state: AppState,
) => {
  await seedAppState(page, state);
  await page.goto(path);
};
