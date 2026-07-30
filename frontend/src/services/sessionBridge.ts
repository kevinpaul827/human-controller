import type {
  SessionAspectRatioListener,
  SessionBridge,
  SessionGestureMapping,
  SessionProfileData,
  SessionPreviewBounds,
  SessionStatusEvent,
  GestureMatchEvent,
  GestureMatchListener,
  OverlayVisibilityListener,
} from "../types/session";

import { getQtWebChannel } from "./qtWebChannel";

/**
 * Wrapper around the PySide6 Qt WebChannel session bridge.
 */
type QtSignal<T> = {
  connect(callback: (payload: T) => void): void;
  disconnect?(callback: (payload: T) => void): void;
};

type SessionProfileResult = {
  ok: boolean;
  data?: SessionProfileData;
  error?: string;
};

type QtSessionBridgeObject = {
  loadProfile?: (
    patientId: string,
    callback?: (result: SessionProfileResult) => void,
  ) => SessionProfileResult | Promise<SessionProfileResult> | void;
  startSession: () => void | Promise<void>;
  stopSession: () => void | Promise<void>;
  getSessionState?: (
    callback?: (state: SessionStatusEvent["state"]) => void,
  ) =>
    | SessionStatusEvent["state"]
    | Promise<SessionStatusEvent["state"]>
    | void;
  getLoadedSessionGestures?: (
    callback?: (gestures: SessionGestureMapping[]) => void,
  ) => SessionGestureMapping[] | Promise<SessionGestureMapping[]> | void;
  updatePreviewBounds: (
    left: number,
    top: number,
    width: number,
    height: number,
    devicePixelRatio: number,
  ) => void | Promise<void>;
  openCameraSettings?: () => void | Promise<void>;
  openAccessibilitySettings?: () => void | Promise<void>;
  setOverlayVisible?: (visible: boolean) => void | Promise<void>;
  getOverlayVisible?: (
    callback?: (visible: boolean) => void,
  ) => boolean | Promise<boolean> | void;
  sessionStatusChanged?: QtSignal<SessionStatusEvent>;
  previewAspectRatioChanged?: QtSignal<number>;
  gestureMatchUpdated?: QtSignal<GestureMatchEvent>;
  overlayVisibilityChanged?: QtSignal<boolean>;
};

const BRIDGE_NAME = "sessionBridge";
const BRIDGE_ERROR = "Qt WebChannel session bridge is unavailable.";

let bridgePromise: Promise<QtSessionBridgeObject> | null = null;

/**
 * Resolves the desktop bridge exposed by PySide6.
 */
const getSessionBridgeOrThrow = () => {
  bridgePromise ??= getQtWebChannel().then((channel) => {
    const bridge = channel.objects[BRIDGE_NAME] as
      | QtSessionBridgeObject
      | undefined;

    if (!bridge) {
      throw new Error(BRIDGE_ERROR);
    }

    return bridge;
  });

  return bridgePromise;
};

const invokeWithResult = <T>(
  invoke: (callback: (result: T) => void) => unknown,
) =>
  new Promise<T>((resolve, reject) => {
    let settled = false;

    const settle = (result: T) => {
      if (settled) {
        return;
      }
      settled = true;
      resolve(result);
    };

    try {
      const maybePromise = invoke(settle);
      if (
        maybePromise != null &&
        typeof (maybePromise as PromiseLike<T>).then === "function"
      ) {
        void Promise.resolve(maybePromise as PromiseLike<T>).then(
          settle,
          (error: unknown) => {
            if (!settled) {
              settled = true;
              reject(error);
            }
          },
        );
      } else if (maybePromise !== undefined) {
        settle(maybePromise as T);
      }
    } catch (error) {
      if (!settled) {
        settled = true;
        reject(error);
      }
    }
  });

const parseProfileResult = (result: SessionProfileResult) => {
  if (!result.ok || !result.data) {
    throw new Error(result.error || "Unable to load the patient profile.");
  }
  return result.data;
};

const sessionBridge: SessionBridge = {
  async loadProfile(patientId) {
    const bridge = await getSessionBridgeOrThrow();
    if (!bridge.loadProfile) {
      throw new Error("Profile-aware sessions are unavailable in this build.");
    }
    return parseProfileResult(
      await invokeWithResult<SessionProfileResult>((callback) =>
        bridge.loadProfile?.(patientId, callback),
      ),
    );
  },

  async startSession() {
    const bridge = await getSessionBridgeOrThrow();
    await bridge.startSession();
  },

  async stopSession() {
    const bridge = await getSessionBridgeOrThrow();
    await bridge.stopSession();
  },

  async getLoadedSessionGestures() {
    const bridge = await getSessionBridgeOrThrow();
    if (!bridge.getLoadedSessionGestures) {
      throw new Error("Loaded session gestures unavailable in this build.");
    }

    return (
      (await invokeWithResult<SessionGestureMapping[]>((callback) =>
        bridge.getLoadedSessionGestures?.(callback),
      )) ?? []
    );
  },

  async updatePreviewBounds(bounds: SessionPreviewBounds) {
    const bridge = await getSessionBridgeOrThrow();
    await bridge.updatePreviewBounds(
      bounds.left,
      bounds.top,
      bounds.width,
      bounds.height,
      bounds.devicePixelRatio ?? window.devicePixelRatio ?? 1,
    );
  },

  async openCameraSettings() {
    const bridge = await getSessionBridgeOrThrow();

    if (!bridge.openCameraSettings) {
      throw new Error("Desktop camera settings are unavailable in this build.");
    }

    await bridge.openCameraSettings();
  },

  async openAccessibilitySettings() {
    const bridge = await getSessionBridgeOrThrow();

    if (!bridge.openAccessibilitySettings) {
      throw new Error(
        "Desktop accessibility settings are unavailable in this build.",
      );
    }

    await bridge.openAccessibilitySettings();
  },

  async setOverlayVisible(visible) {
    const bridge = await getSessionBridgeOrThrow();
    if (!bridge.setOverlayVisible) {
      throw new Error("Desktop game overlay is unavailable in this build.");
    }
    await bridge.setOverlayVisible(visible);
  },

  onSessionStatus(listener) {
    let active = true;
    let unsubscribe = () => {};

    void getSessionBridgeOrThrow()
      .then((bridge) => {
        if (!active) {
          return;
        }

        if (!bridge.sessionStatusChanged) {
          listener({ state: "error", message: BRIDGE_ERROR });
          return;
        }

        bridge.sessionStatusChanged.connect(listener);
        unsubscribe = () => {
          bridge.sessionStatusChanged?.disconnect?.(listener);
        };
        if (bridge.getSessionState) {
          void invokeWithResult<SessionStatusEvent["state"]>((callback) =>
            bridge.getSessionState?.(callback),
          )
            .then((currentState) => {
              if (active && currentState) {
                listener({ state: currentState });
              }
            })
            .catch(() => {});
        }
      })
      .catch((error: Error) => {
        if (!active) {
          return;
        }
        listener({ state: "error", message: error.message });
      });

    return () => {
      active = false;
      unsubscribe();
    };
  },

  onPreviewAspectRatio(listener: SessionAspectRatioListener) {
    let active = true;
    let unsubscribe = () => {};

    void getSessionBridgeOrThrow()
      .then((bridge) => {
        if (!active) {
          return;
        }

        if (!bridge.previewAspectRatioChanged) {
          return;
        }

        bridge.previewAspectRatioChanged.connect(listener);
        unsubscribe = () => {
          bridge.previewAspectRatioChanged?.disconnect?.(listener);
        };
      })
      .catch(() => {});

    return () => {
      active = false;
      unsubscribe();
    };
  },

  onGestureMatch(listener: GestureMatchListener) {
    let active = true;
    let unsubscribe = () => {};
    void getSessionBridgeOrThrow()
      .then((bridge) => {
        if (!active || !bridge.gestureMatchUpdated) return;
        bridge.gestureMatchUpdated.connect(listener);
        unsubscribe = () => bridge.gestureMatchUpdated?.disconnect?.(listener);
      })
      .catch(() => {});
    return () => {
      active = false;
      unsubscribe();
    };
  },

  onOverlayVisibility(listener: OverlayVisibilityListener) {
    let active = true;
    let unsubscribe = () => {};
    void getSessionBridgeOrThrow()
      .then((bridge) => {
        if (!active || !bridge.overlayVisibilityChanged) return;
        bridge.overlayVisibilityChanged.connect(listener);
        unsubscribe = () =>
          bridge.overlayVisibilityChanged?.disconnect?.(listener);
        if (bridge.getOverlayVisible) {
          void invokeWithResult<boolean>((callback) =>
            bridge.getOverlayVisible?.(callback),
          )
            .then((visible) => {
              if (active) listener(Boolean(visible));
            })
            .catch(() => {});
        }
      })
      .catch(() => {});
    return () => {
      active = false;
      unsubscribe();
    };
  },
};

export default sessionBridge;
