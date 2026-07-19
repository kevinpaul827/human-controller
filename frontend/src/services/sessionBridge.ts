import type {
  SessionAspectRatioListener,
  SessionBridge,
  SessionPreviewBounds,
  SessionStatusEvent,
} from "../types/session";
import type { SaveGesturePayload, SavedGesture } from "../types/gesture";

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
  listGestures?: () => SavedGesture[] | Promise<SavedGesture[]>;
  saveGesture?: (payloadJson: string) => { ok: boolean; message?: string; gesture?: SavedGesture } | Promise<{ ok: boolean; message?: string; gesture?: SavedGesture }>;
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
  bridgePromise ??= new Promise<QtSessionBridgeObject>((resolve, reject) => {
    if (!window.qt?.webChannelTransport || !window.QWebChannel) {
      reject(new Error(BRIDGE_ERROR));
      return;
    }

    new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
      const bridge = channel.objects[BRIDGE_NAME] as
        | QtSessionBridgeObject
        | undefined;

      if (!bridge) {
        reject(new Error(BRIDGE_ERROR));
        return;
      }

      resolve(bridge);
    });
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

  async listGestures() {
    const bridge = await getSessionBridgeOrThrow();

    if (!bridge.listGestures) {
      return [];
    }

    return (await bridge.listGestures()) ?? [];
  },

  async saveGesture(payload: SaveGesturePayload) {
    const bridge = await getSessionBridgeOrThrow();

    if (!bridge.saveGesture) {
      throw new Error("Desktop gesture saving is unavailable in this build.");
    }

    const result = await bridge.saveGesture(JSON.stringify(payload));
    if (!result?.ok || !result.gesture) {
      throw new Error(result?.message ?? "Unable to save gesture.");
    }

    return result.gesture;
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
    let unsubscribe = () => {};

    void getSessionBridgeOrThrow()
      .then((bridge) => {
        if (!bridge.sessionStatusChanged) {
          listener({ state: "error", message: BRIDGE_ERROR });
          return;
        }

        bridge.sessionStatusChanged.connect(listener);
        const currentState = bridge.getSessionState?.();
        if (currentState) {
          listener({ state: currentState });
        }
        unsubscribe = () => {
          bridge.sessionStatusChanged?.disconnect?.(listener);
        };
      })
      .catch((error: Error) => {
        listener({ state: "error", message: error.message });
      });

    return () => unsubscribe();
  },

  onPreviewAspectRatio(listener: SessionAspectRatioListener) {
    let unsubscribe = () => {};

    void getSessionBridgeOrThrow()
      .then((bridge) => {
        if (!bridge.previewAspectRatioChanged) {
          return;
        }

        bridge.previewAspectRatioChanged.connect(listener);
        unsubscribe = () => {
          bridge.previewAspectRatioChanged?.disconnect?.(listener);
        };
      })
      .catch(() => {});

    return () => unsubscribe();
  },
};

export default sessionBridge;
