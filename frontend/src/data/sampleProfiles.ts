import type { Binding, Gesture, Patient, Preset } from "../types/profile";

const daysAgo = (days: number) =>
  new Date(Date.now() - days * 86_400_000).toISOString();

export const SAMPLE_GESTURES: Gesture[] = [
  {
    gestureId: "ges-right-arm-raise",
    name: "Right Arm Raise",
    calibratedAt: daysAgo(2),
    matchScore: 87,
  },
  {
    gestureId: "ges-squat",
    name: "Squat",
    calibratedAt: daysAgo(2),
    matchScore: 82,
  },
  {
    gestureId: "ges-lean-left",
    name: "Lean Left",
    calibratedAt: daysAgo(9),
    matchScore: 80,
  },
  {
    gestureId: "ges-lean-right",
    name: "Lean Right",
    calibratedAt: null,
    matchScore: null,
  },
  {
    gestureId: "ges-jump",
    name: "Jump",
    calibratedAt: null,
    matchScore: null,
  },
  {
    gestureId: "ges-elbow-curl",
    name: "Elbow Curl",
    calibratedAt: daysAgo(21),
    matchScore: 78,
  },
];

export const SAMPLE_BINDINGS: Binding[] = [
  { gestureId: "ges-right-arm-raise", key: "ArrowUp", matchThreshold: 75 },
  { gestureId: "ges-squat", key: "ArrowDown", matchThreshold: 75 },
  { gestureId: "ges-lean-left", key: "ArrowLeft", matchThreshold: 75 },
];

export const SAMPLE_PRESETS: Preset[] = [
  {
    presetId: "preset-celeste",
    name: "Celeste",
    bindings: [
      { gestureId: "ges-right-arm-raise", key: "ArrowUp", matchThreshold: 75 },
      { gestureId: "ges-squat", key: "ArrowDown", matchThreshold: 75 },
      { gestureId: "ges-lean-left", key: "ArrowLeft", matchThreshold: 75 },
      { gestureId: "ges-lean-right", key: "ArrowRight", matchThreshold: 75 },
    ],
  },
  {
    presetId: "preset-mario",
    name: "Super Mario Bros",
    bindings: [
      { gestureId: "ges-jump", key: "Space", matchThreshold: 75 },
      { gestureId: "ges-elbow-curl", key: "ArrowRight", matchThreshold: 75 },
    ],
  },
];

export const SAMPLE_PATIENTS: Patient[] = [
  {
    schemaVersion: 2,
    patientId: "patient-a",
    patientName: "Patient A",
    notes: "",
    updatedAt: daysAgo(1),
    keyBindings: Object.fromEntries(
      SAMPLE_BINDINGS.map(({ gestureId, key }) => [gestureId, key]),
    ),
    matchThresholds: Object.fromEntries(
      SAMPLE_BINDINGS.map(({ gestureId, matchThreshold }) => [
        gestureId,
        matchThreshold ?? 75,
      ]),
    ),
  },
  {
    schemaVersion: 2,
    patientId: "patient-b",
    patientName: "Patient B",
    notes: "",
    updatedAt: daysAgo(4),
    keyBindings: {},
    matchThresholds: {},
  },
];

/** Browser-only data used when Qt WebChannel is unavailable. */
export const SAMPLE_PROFILES = SAMPLE_PATIENTS;
