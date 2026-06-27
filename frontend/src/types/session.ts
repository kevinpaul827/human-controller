export type SessionState = "idle" | "starting" | "live" | "error";

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

export interface SessionBridge {
  startSession(): Promise<void>;
  stopSession(): Promise<void>;
  onSessionStatus(listener: SessionStatusListener): () => void;
}
