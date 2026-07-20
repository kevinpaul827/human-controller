import type { GestureSummary, PatientProfile } from "../types/profile";

/** Browser-only data used when Qt WebChannel is unavailable. */
export const SAMPLE_PROFILES: PatientProfile[] = [
  {
    schemaVersion: 2,
    patientId: "patient-a",
    patientName: "Patient A",
    notes: "Working on upper-body mobility and balance.",
    updatedAt: "2026-07-20T08:30:00Z",
    keyBindings: {
      right_arm_raise: "ArrowUp",
      squat: "ArrowDown",
      lean_left: "ArrowLeft",
      lean_right: "ArrowRight",
      hold_pose: "Space",
    },
  },
  {
    schemaVersion: 2,
    patientId: "demo-profile",
    patientName: "Demo Profile",
    notes: "Example profile for local browser preview.",
    updatedAt: "2026-07-20T08:30:00Z",
    keyBindings: {
      gesture1: "Space",
    },
  },
];

export const SAMPLE_GESTURES: GestureSummary[] = [
  { gestureId: "gesture1", name: "Gesture 1", type: "state" },
  { gestureId: "right_arm_raise", name: "Right Arm Raise", type: "state" },
  { gestureId: "squat", name: "Squat", type: "state" },
  { gestureId: "lean_left", name: "Lean Left", type: "state" },
  { gestureId: "lean_right", name: "Lean Right", type: "state" },
  { gestureId: "hold_pose", name: "Hold Pose", type: "state" },
];
