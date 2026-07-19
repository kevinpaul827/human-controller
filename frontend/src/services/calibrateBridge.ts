import type {
  CalibrateAspectRatioListener,
  CalibrateBridge,
  CalibratePreviewBounds,
  CalibrateStatusEvent,
} from "../types/calibrate";

/**
 * Wrapper around the PySide6 Qt WebChannel calibrate bridge.
 */
type QtSignal<T> = {
  connect(callback: (payload: T) => void): void;
  disconnect?(callback: (payload: T) => void): void;
};

type QtCalibrateBridgeObject = {
  startCalibrate: () => void | Promise<void>;
  stopCalibrate: () => void | Promise<void>;
  getCalibrateState?: () => CalibrateStatusEvent["state"];
  updatePreviewBounds: (
    left: number,
    top: number,
    width: number,
    height: number,
    devicePixelRatio: number,
  ) => void | Promise<void>;
  openCameraSettings?: () => void | Promise<void>;
  calibrateStatusChanged?: QtSignal<CalibrateStatusEvent>;
  previewAspectRatioChanged?: QtSignal<number>;
};

const BRIDGE_NAME = "calibrateBridge";
const BRIDGE_ERROR = "Qt WebChannel calibrate bridge is unavailable.";

let bridgePromise: Promise<QtCalibrateBridgeObject> | null = null;

/**
 * Resolves the desktop bridge exposed by PySide6.
 */
const getCalibrateBridgeOrThrow = () => {
  bridgePromise ??= new Promise<QtCalibrateBridgeObject>((resolve, reject) => {
    if (!window.qt?.webChannelTransport || !window.QWebChannel) {
      reject(new Error(BRIDGE_ERROR));
      return;
    }

    new window.QWebChannel(window.qt.webChannelTransport, (channel) => {
      const bridge = channel.objects[BRIDGE_NAME] as
        | QtCalibrateBridgeObject
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

const calibrateBridge: CalibrateBridge = {
  async startCalibrate() {
    const bridge = await getCalibrateBridgeOrThrow();
    await bridge.startCalibrate();
  },

  async stopCalibrate() {
    const bridge = await getCalibrateBridgeOrThrow();
    await bridge.stopCalibrate();
  },

  async updatePreviewBounds(bounds: CalibratePreviewBounds) {
    const bridge = await getCalibrateBridgeOrThrow();
    await bridge.updatePreviewBounds(
      bounds.left,
      bounds.top,
      bounds.width,
      bounds.height,
      bounds.devicePixelRatio ?? window.devicePixelRatio ?? 1,
    );
  },

  async openCameraSettings() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.openCameraSettings) {
      throw new Error("Desktop camera settings are unavailable in this build.");
    }

    await bridge.openCameraSettings();
  },

  onCalibrateStatus(listener) {
    let unsubscribe = () => {};

    void getCalibrateBridgeOrThrow()
      .then((bridge) => {
        if (!bridge.calibrateStatusChanged) {
          listener({ state: "error", message: BRIDGE_ERROR });
          return;
        }

        bridge.calibrateStatusChanged.connect(listener);
        const currentState = bridge.getCalibrateState?.();
        if (currentState) {
          listener({ state: currentState });
        }
        unsubscribe = () => {
          bridge.calibrateStatusChanged?.disconnect?.(listener);
        };
      })
      .catch((error: Error) => {
        listener({ state: "error", message: error.message });
      });

    return () => unsubscribe();
  },

  onPreviewAspectRatio(listener: CalibrateAspectRatioListener) {
    let unsubscribe = () => {};

    void getCalibrateBridgeOrThrow()
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

export default calibrateBridge;
