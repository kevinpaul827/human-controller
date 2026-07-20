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
  updatePreviewBounds(bounds: CalibratePreviewBounds): Promise<void>;
  openCameraSettings(): Promise<void>;
  onCalibrateStatus(listener: CalibrateStatusListener): () => void;
  onPreviewAspectRatio(listener: CalibrateAspectRatioListener): () => void;
}
