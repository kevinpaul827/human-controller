import type { Page } from "@playwright/test";

type AppState = {
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

const STORAGE_KEY = "human-controller/app-state/v2";

export const createAppState = (): AppState => ({
  gestures: [],
  bindings: [],
  presets: [],
  selectedPatientId: null,
  activePresetId: null,
  patients: [],
  settings: {
    matchThreshold: 75,
    cooldown: 0.5,
    smoothing: 2,
    poseModel: "lite",
  },
});

export const seedAppState = async (page: Page, state: AppState) => {
  await page.addInitScript(
    ({ storageKey, appState }) => {
      window.localStorage.setItem(storageKey, JSON.stringify(appState));
    },
    { storageKey: STORAGE_KEY, appState: state },
  );
};
