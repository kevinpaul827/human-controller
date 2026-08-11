import type {
  SessionAspectRatioListener,
  SessionBridge,
  SessionGestureMapping,
  SessionProfileData,
  SessionPreviewBounds,
  SessionStatusEvent,
  GestureMatchEvent,
  GestureMatchListener,
} from "../types/session";

import {
  createBridgeResolver,
  invokeWithResult,
  type QtSignal,
} from "./qtBridgeUtils";

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
  sessionStatusChanged?: QtSignal<SessionStatusEvent>;
  previewAspectRatioChanged?: QtSignal<number>;
  gestureMatchUpdated?: QtSignal<GestureMatchEvent>;
};

const BRIDGE_ERROR = "Qt WebChannel session bridge is unavailable.";

const sessionBridgeResolver = createBridgeResolver<QtSessionBridgeObject>(
  "sessionBridge",
  BRIDGE_ERROR,
);

const parseProfileResult = (result: SessionProfileResult) => {
  if (!result.ok || !result.data) {
    throw new Error(result.error || "Unable to load the patient profile.");
  }
  return result.data;
};

/** Promise-based wrapper around the session bridge and its live events. */
const sessionBridge: SessionBridge = {
  async loadProfile(patientId) {
    const bridge = await sessionBridgeResolver.get();
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
    const bridge = await sessionBridgeResolver.get();
    await bridge.startSession();
  },

  async stopSession() {
    const bridge = await sessionBridgeResolver.get();
    await bridge.stopSession();
  },

  async getLoadedSessionGestures() {
    const bridge = await sessionBridgeResolver.get();
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
    const bridge = await sessionBridgeResolver.get();
    await bridge.updatePreviewBounds(
      bounds.left,
      bounds.top,
      bounds.width,
      bounds.height,
      bounds.devicePixelRatio ?? window.devicePixelRatio ?? 1,
    );
  },

  async openCameraSettings() {
    const bridge = await sessionBridgeResolver.get();

    if (!bridge.openCameraSettings) {
      throw new Error("Desktop camera settings are unavailable in this build.");
    }

    await bridge.openCameraSettings();
  },

  async openAccessibilitySettings() {
    const bridge = await sessionBridgeResolver.get();

    if (!bridge.openAccessibilitySettings) {
      throw new Error(
        "Desktop accessibility settings are unavailable in this build.",
      );
    }

    await bridge.openAccessibilitySettings();
  },

  onSessionStatus(listener) {
    let active = true;
    let unsubscribe = () => {};

    void sessionBridgeResolver
      .get()
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

    void sessionBridgeResolver
      .get()
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
    void sessionBridgeResolver
      .get()
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
};

export default sessionBridge;

/** @internal Reset cached bridge state between isolated tests. */
export const resetSessionBridgeForTests = () => {
  sessionBridgeResolver.reset();
};
