export type CalibrateState = "idle" | "live" | "error";

export type CalibrateStatusEvent = {
  state: CalibrateState;

  message?: string;
};

export type CalibrateStatusListener = (event: CalibrateStatusEvent) => void;
export type CalibrateAspectRatioListener = (aspectRatio: number) => void;
export type CapturePhase =
  | "idle"
  | "countdown"
  | "waiting"
  | "recording"
  | "captured";
export type CalibrationUpdateEvent = {
  repCount: number;
  capturing: boolean;
  phase: CapturePhase;
  countdownRemaining: number;
};
export type CalibrationUpdateListener = (event: CalibrationUpdateEvent) => void;
export type CapturedRep = { repCount: number; angles: Record<string, number> };
export type SavedRepResult = {
  gestureId: string;
  name: string;
  repCount: number;
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
  startRep(recordingSeconds: number): Promise<void>;
  cancelRep(): Promise<void>;
  stopRep(): Promise<CapturedRep>;
  resetRep(): Promise<void>;
  saveRep(name: string, gestureId: string): Promise<SavedRepResult>;
  updatePreviewBounds(bounds: CalibratePreviewBounds): Promise<void>;
  openCameraSettings(): Promise<void>;
  onCalibrateStatus(listener: CalibrateStatusListener): () => void;
  onPreviewAspectRatio(listener: CalibrateAspectRatioListener): () => void;
  onCalibrationUpdated(listener: CalibrationUpdateListener): () => void;
}
