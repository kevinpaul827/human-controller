export const STEP_LABELS = ["Name it", "Record it", "Save it"] as const;
export const NAME_STEP = 1;
export const RECORD_STEP = 2;
export const SAVE_STEP = 3;
export const DEFAULT_RECORDING_DURATION = "10";
export const MIN_RECORDING_DURATION_SECONDS = 1;
export const MAX_RECORDING_DURATION_SECONDS = 60;
export const EMPTY_REP_COUNT = 0;
export const DEFAULT_MOVEMENT_NAME = "New movement";
export const NO_PROFILE_SELECTED = "No profile selected";
export const START_CAMERA_ERROR = "Unable to start the camera.";
export const START_CALIBRATION_ERROR = "Unable to start calibration.";
export const TOGGLE_RECORDING_ERROR = "Unable to change the recording state.";
export const RESET_RECORDING_ERROR = "Unable to reset this recording.";
export const SAVE_MOVEMENT_ERROR = "Unable to save this movement.";
export const CALIBRATION_INSTRUCTIONS = [
  "Keep your whole body visible.",
  "Press Start recording and hold the starting pose through the 3-second countdown.",
  "Move when “Ready — move now” appears, then hold the final pose. Start and finish are detected automatically.",
] as const;
