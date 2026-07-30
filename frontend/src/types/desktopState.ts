import type { Binding, Gesture, Patient, Preset } from "./profile";

export type RuntimeSettings = {
  matchThreshold: number;
  holdDuration: number;
  cooldown: number;
  smoothing: number;
};

export type DesktopState = {
  gestures: Gesture[];
  bindings: Binding[];
  presets: Preset[];
  patients: Patient[];
  selectedPatientId: string | null;
  activePresetId: string | null;
  settings: RuntimeSettings;
};
