export type SessionState = "idle" | "live" | "error";

export type SessionStatusEvent = {
  state: SessionState;

  message?: string;
  settingsTarget?: "camera" | "accessibility";
};

export type SessionStatusListener = (event: SessionStatusEvent) => void;
export type SessionAspectRatioListener = (aspectRatio: number) => void;
export type GestureMatchEvent = {
  gestureId: string | null;
  name: string | null;
  score: number;
  matched: boolean;
  hasTemplates: boolean;
  triggered?: boolean;
  key?: string;
  injectionError?: string;
  keyAction?: "press" | "release";
};
export type GestureMatchListener = (event: GestureMatchEvent) => void;
export type OverlayVisibilityListener = (visible: boolean) => void;

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
  openAccessibilitySettings(): Promise<void>;
  setOverlayVisible(visible: boolean): Promise<void>;
  onSessionStatus(listener: SessionStatusListener): () => void;
  onPreviewAspectRatio(listener: SessionAspectRatioListener): () => void;
  onGestureMatch(listener: GestureMatchListener): () => void;
  onOverlayVisibility(listener: OverlayVisibilityListener): () => void;
}
