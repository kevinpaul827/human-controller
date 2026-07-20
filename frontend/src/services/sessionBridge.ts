import { SavedGestureSummary } from "../types/calibrate";
import type {
  SessionAspectRatioListener,
  SessionBridge,
  SessionPreviewBounds,
  SessionStatusEvent,
} from "../types/session";

import { getQtWebChannel } from "./qtWebChannel";

/**
 * Wrapper around the PySide6 Qt WebChannel session bridge.
 */
type QtSignal<T> = {
  connect(callback: (payload: T) => void): void;
  disconnect?(callback: (payload: T) => void): void;
};

type QtSessionBridgeObject = {
  startSession: () => void | Promise<void>;
  stopSession: () => void | Promise<void>;
  getSessionState?: () => SessionStatusEvent["state"];
  getLoadedSessionGestures?: () =>
    | SavedGestureSummary[]
    | Promise<SavedGestureSummary[]>
  updatePreviewBounds: (
    left: number,
    top: number,
    width: number,
    height: number,
    devicePixelRatio: number,
  ) => void | Promise<void>;
  openCameraSettings?: () => void | Promise<void>;
  sessionStatusChanged?: QtSignal<SessionStatusEvent>;
  previewAspectRatioChanged?: QtSignal<number>;
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

const sessionBridge: SessionBridge = {
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
      throw new Error("Loaded session gestures unavailable in this build.")
    }

    return (await bridge.getLoadedSessionGestures()) ?? [];
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
        const currentState = bridge.getSessionState?.();
        if (active && currentState) {
          listener({ state: currentState });
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
};

export default sessionBridge;
