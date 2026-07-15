export type GestureBinding = {
  name: string;
  key: string;
  threshold: number;
};

export type GameProfile = {
  gameName: string;
  gestures: GestureBinding[];
};

export type PatientProfile = {
  schemaVersion: 1;
  patientId: string;
  patientName: string;
  notes?: string;
  lastSessionGame?: string | null;
  gameProfiles: GameProfile[];
};
