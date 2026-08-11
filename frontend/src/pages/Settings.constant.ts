import type { PoseModel } from "@/types/desktopState";

export const EFFORT_LABELS = [
  "Very gentle",
  "Gentle",
  "Balanced",
  "Precise",
  "Strict",
] as const;

export const TRACKING_MODES: {
  value: PoseModel;
  label: string;
  detail: string;
  ram: string;
}[] = [
  {
    value: "lite",
    label: "Fast",
    detail: "Prioritises smooth frame rate",
    ram: "4 GB+ RAM, 2+ CPU cores",
  },
  {
    value: "full",
    label: "Balanced",
    detail: "Good speed and tracking accuracy",
    ram: "8 GB+ RAM, 4+ CPU cores",
  },
  {
    value: "heavy",
    label: "High accuracy",
    detail: "Prioritises tracking detail",
    ram: "16 GB+ RAM, 8+ CPU cores",
  },
] as const;

export const PAGE_EYEBROW = "Settings";
export const PAGE_TITLE = "Tracking preferences";
export const PAGE_DESCRIPTION = "Changes save automatically.";
export const CAMERA_TRACKING_TITLE = "Camera tracking";
export const MOVEMENT_RESPONSE_TITLE = "Movement response";
export const AUTO_MODE_TITLE = "Optimise for this device";
export const AUTO_MODE_DESCRIPTION =
  "Checks memory and processor capacity, then picks a tracking mode.";
export const CALIBRATE_TRACKING_LABEL = "Calibrate tracking";
export const CALIBRATING_TRACKING_LABEL = "Calibrating…";
export const RECOMMENDATION_ERROR_MESSAGE =
  "Couldn’t check this device. Choose a mode manually.";
export const MANUAL_MODE_SUMMARY_PREFIX = "Choose manually · Current:";
export const TRACKING_MODE_LEGEND = "Tracking mode";
export const DEFAULT_THRESHOLD_LABEL = "Default match threshold";
export const COOLDOWN_LABEL = "Cooldown";
export const STEADINESS_LABEL = "Steadiness";
export const DEFAULT_EFFORT_LABEL = "Balanced";
export const THRESHOLD_MIN = 0;
export const THRESHOLD_MAX = 100;
export const THRESHOLD_STEP = 1;
export const COOLDOWN_MIN = 0;
export const COOLDOWN_MAX = 2;
export const COOLDOWN_STEP = 0.1;
export const SMOOTHING_MIN = 0;
export const SMOOTHING_MAX = 4;
export const SMOOTHING_STEP = 1;
export const RESPONSE_HELPER_TEXT =
  "Applied to new bindings. Existing movements can be adjusted from the Session page.";
