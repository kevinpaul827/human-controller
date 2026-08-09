export type PatientProfile = {
  schemaVersion: 2;
  patientId: string;
  patientName: string;
  notes: string;
  updatedAt: string;
  keyBindings: Record<string, string>;
  matchThresholds: Record<string, number>;
};

export type GestureSummary = {
  gestureId: string;
  name: string;
};

export type Gesture = GestureSummary & {
  calibratedAt: string | null;
  matchScore: number | null;
};

export type Binding = {
  gestureId: string;
  key: string;
  matchThreshold?: number;
};

export type Preset = {
  presetId: string;
  name: string;
  bindings: Binding[];
};

export type Patient = PatientProfile;
