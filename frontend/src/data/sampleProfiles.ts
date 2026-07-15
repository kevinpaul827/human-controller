import type { PatientProfile } from "../types/profile";

/** Sample data for Sprint 1 UI — replace with ProfileBridge in Sprint 2. */
export const SAMPLE_PROFILES: PatientProfile[] = [
  {
    schemaVersion: 1,
    patientId: "patient-a",
    patientName: "Patient A",
    lastSessionGame: "Celeste — Rehab 1",
    gameProfiles: [
      {
        gameName: "Celeste — Rehab 1",
        gestures: [
          { name: "Right Arm Raise", key: "ArrowUp", threshold: 0.87 },
          { name: "Squat", key: "ArrowDown", threshold: 0.82 },
          { name: "Lean Left", key: "ArrowLeft", threshold: 0.8 },
          { name: "Lean Right", key: "ArrowRight", threshold: 0.8 },
          { name: "Hold Pose", key: "Space", threshold: 0.9 },
        ],
      },
      {
        gameName: "Super Mario Bros",
        gestures: [
          { name: "Jump", key: "Space", threshold: 0.78 },
          { name: "Run", key: "ArrowRight", threshold: 0.75 },
        ],
      },
    ],
  },
  {
    schemaVersion: 1,
    patientId: "demo-profile",
    patientName: "Demo Profile",
    gameProfiles: [
      {
        gameName: "Celeste — Rehab Mode",
        gestures: [
          { name: "Right Arm Raise", key: "ArrowUp", threshold: 0.75 },
          { name: "Squat", key: "ArrowDown", threshold: 0.75 },
        ],
      },
    ],
  },
];
