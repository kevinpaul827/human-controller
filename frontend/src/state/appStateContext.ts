import { createContext, useContext } from "react";
import type { Gesture, Patient, Preset } from "@/types/profile";
import type { RuntimeSettings } from "@/types/desktopState";
import type { SavedRepResult } from "@/types/calibrate";

export type ResolvedBinding = {
  gesture: Gesture;
  key: string;
  matchThreshold: number;
};

export type Readiness = {
  total: number;
  recorded: number;

  pending: Gesture[];
  isReady: boolean;
};

export type AppStateValue = {
  gestures: Gesture[];
  bindings: ResolvedBinding[];

  unboundGestures: Gesture[];
  presets: Preset[];
  patients: Patient[];
  selectedPatient: Patient | null;
  activePreset: Preset | null;

  hasUnsavedChanges: boolean;
  readiness: Readiness;
  undoLabel: string | null;
  settings: RuntimeSettings;

  addGesture: (name: string) => string;
  renameGesture: (gestureId: string, name: string) => void;
  deleteGesture: (gestureId: string) => void;
  completeRecording: (
    previousGestureId: string,
    result: SavedRepResult,
  ) => void;

  bindGesture: (gestureId: string, key: string) => void;
  rebindKey: (gestureId: string, key: string) => void;
  setBindingThreshold: (gestureId: string, threshold: number) => void;
  unbindGesture: (gestureId: string) => void;
  setPatientBinding: (
    patientId: string,
    gestureId: string,
    key: string,
  ) => void;
  removePatientBinding: (patientId: string, gestureId: string) => void;

  savePreset: (name: string) => void;
  loadPreset: (presetId: string) => void;
  deletePreset: (presetId: string) => void;

  selectPatient: (patientId: string) => Promise<void>;
  createPatient: (
    patientName: string,
    notes?: string,
  ) => Promise<Patient | null>;
  deletePatient: (patientId: string) => Promise<void>;
  clearPatientSelection: () => Promise<void>;
  refreshState: () => Promise<void>;
  saveSettings: (settings: RuntimeSettings) => void;
  undo: () => void;
  dismissUndo: () => void;
};

export const AppStateContext = createContext<AppStateValue | null>(null);

export const useAppState = () => {
  const value = useContext(AppStateContext);
  if (!value) {
    throw new Error("useAppState must be used inside <AppStateProvider>");
  }
  return value;
};
