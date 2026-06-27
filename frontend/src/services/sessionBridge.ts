import type { SessionBridge, SessionStatusEvent } from "../types/session";

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
  sessionStatusChanged?: QtSignal<SessionStatusEvent>;
};

const BRIDGE_NAME = "sessionBridge";
const BRIDGE_ERROR =
  "Qt WebChannel session bridge is unavailable. TODO: connect the PySide6 desktop bridge.";

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

  onSessionStatus(listener) {
    let unsubscribe = () => {};

    void getSessionBridgeOrThrow()
      .then((bridge) => {
        if (!bridge.sessionStatusChanged) {
          listener({ state: "error", message: BRIDGE_ERROR });
          return;
        }

        bridge.sessionStatusChanged.connect(listener);
        unsubscribe = () => {
          bridge.sessionStatusChanged?.disconnect?.(listener);
        };
      })
      .catch((error: Error) => {
        listener({ state: "error", message: error.message });
      });

    return () => unsubscribe();
  },
};

export default sessionBridge;
