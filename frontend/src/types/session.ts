export type SessionState = "idle" | "live" | "error";

/**
 * Status payload emitted by the desktop-managed session bridge.
 */
export type SessionStatusEvent = {
  /** The current state of the session. */
  state: SessionState;
  /** A message providing additional context about the session status. */
  message?: string;
  settingsTarget?: "camera" | "accessibility";
};

export type SessionStatusListener = (event: SessionStatusEvent) => void;
export type SessionAspectRatioListener = (aspectRatio: number) => void;

export type SessionPreviewBounds = {
  left: number;
  top: number;
  width: number;
  height: number;
  devicePixelRatio?: number;
};

export type GestureMatchEvent = {
  gestureId: string | null;
  name: string | null;
  score: number;
  matched: boolean;
  hasTemplates: boolean;
  triggered?: boolean;
  key?: string;
  injectionError?: string;
  keyAction?: "press" | "release" | "reset";
};
export type GestureMatchListener = (event: GestureMatchEvent) => void;

export type SessionGestureMapping = {
  gestureId: string;
  name: string;
  key: string;
};

export type SessionProfileData = {
  patientId: string;
  gestures: SessionGestureMapping[];
  missingGestureIds: string[];
};

export interface SessionBridge {
  loadProfile(patientId: string): Promise<SessionProfileData>;
  startSession(): Promise<void>;
  stopSession(): Promise<void>;
  getLoadedSessionGestures(): Promise<SessionGestureMapping[]>;
  updatePreviewBounds(bounds: SessionPreviewBounds): Promise<void>;
  openCameraSettings(): Promise<void>;
  openAccessibilitySettings(): Promise<void>;
  onSessionStatus(listener: SessionStatusListener): () => void;
  onPreviewAspectRatio(listener: SessionAspectRatioListener): () => void;
  onGestureMatch(listener: GestureMatchListener): () => void;
}
