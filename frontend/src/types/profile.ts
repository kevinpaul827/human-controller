export type Gesture = {
  gestureId: string;
  name: string;

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

export type Patient = {
  patientId: string;
  patientName: string;
};
