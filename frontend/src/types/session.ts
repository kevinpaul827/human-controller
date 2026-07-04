export type SessionState = "idle" | "live" | "error";

/**
 * Status payload emitted by the desktop-managed session bridge.
 */
export type SessionStatusEvent = {
  /** The current state of the session. */
  state: SessionState;
  /** A message providing additional context about the session status. */
  message?: string;
};

export type SessionStatusListener = (event: SessionStatusEvent) => void;

export type SessionPreviewBounds = {
  left: number;
  top: number;
  width: number;
  height: number;
  devicePixelRatio?: number;
};

export interface SessionBridge {
  startSession(): Promise<void>;
  stopSession(): Promise<void>;
  updatePreviewBounds(bounds: SessionPreviewBounds): Promise<void>;
  openCameraSettings(): Promise<void>;
  onSessionStatus(listener: SessionStatusListener): () => void;
}
