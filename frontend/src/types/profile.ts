export type PatientProfile = {
  schemaVersion: 2;
  patientId: string;
  patientName: string;
  notes: string;
  updatedAt: string;
  keyBindings: Record<string, string>;
};

export type GestureSummary = {
  gestureId: string;
  name: string;
  type: string;
};
