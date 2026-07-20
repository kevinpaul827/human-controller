export type CalibrateState = "idle" | "live" | "error";

/**
 * Status payload emitted by the desktop-managed calibrate bridge.
 */
export type CalibrateStatusEvent = {
  /** The current state of the calibration. */
  state: CalibrateState;
  /** A message providing additional context about the calibrate status. */
  message?: string;
};

export type CalibrateStatusListener = (event: CalibrateStatusEvent) => void;
export type CalibrateAspectRatioListener = (aspectRatio: number) => void;
export type CalibrationUpdateEvent = {
  repCount: number;
  capturing: boolean;
};
export type CalibrationUpdateListener = (event: CalibrationUpdateEvent) => void;

export type CapturedRep = {
  repCount: number;
  angles: Record<string, number>;
};

export type SavedGestureSummary = {
  gestureId: string;
  name: string;
};

export type SavedRepResult = {
  gestureId: string;
  name: string;
  repCount: number;
  loadedGestures?: SavedGestureSummary[];
};

export type LoadSavedGestureResult = {
  gesture: SavedGestureSummary;
  loadedGestures: SavedGestureSummary[];
};

export type CalibratePreviewBounds = {
  left: number;
  top: number;
  width: number;
  height: number;
  devicePixelRatio?: number;
};

export interface CalibrateBridge {
  startCalibrate(): Promise<void>;
  stopCalibrate(): Promise<void>;
  startCalibration(): Promise<void>;
  captureRep(): Promise<CapturedRep>;
  resetRep(): Promise<void>;
  saveRep(name: string): Promise<SavedRepResult>;
  listSavedGestures(): Promise<SavedGestureSummary[]>;
  getLoadedSessionGestures(): Promise<SavedGestureSummary[]>;
  loadSavedGesture(gestureId: string): Promise<LoadSavedGestureResult>;
  updatePreviewBounds(bounds: CalibratePreviewBounds): Promise<void>;
  openCameraSettings(): Promise<void>;
  onCalibrateStatus(listener: CalibrateStatusListener): () => void;
  onPreviewAspectRatio(listener: CalibrateAspectRatioListener): () => void;
  onCalibrationUpdated(listener: CalibrationUpdateListener): () => void;
}
