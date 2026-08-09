import type { Binding, Gesture, Patient, Preset } from "./profile";

export type PoseModel = "lite" | "full" | "heavy";

export type PoseModelRecommendation = {
  poseModel: PoseModel;
  ramGb: number | null;
  physicalCpuCount: number | null;
  logicalCpuCount: number | null;
};

export type RuntimeSettings = {
  matchThreshold: number;
  cooldown: number;
  smoothing: number;
  poseModel: PoseModel;
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
