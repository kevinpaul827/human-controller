import type {
  CalibrateAspectRatioListener,
  CalibrateBridge,
  CalibratePreviewBounds,
  CalibrateStatusEvent,
} from "../types/calibrate";

import { getQtWebChannel } from "./qtWebChannel";

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
  bridgePromise ??= getQtWebChannel().then((channel) => {
    const bridge = channel.objects[BRIDGE_NAME] as
      | QtCalibrateBridgeObject
      | undefined;

    if (!bridge) {
      throw new Error(BRIDGE_ERROR);
    }

    return bridge;
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
    let active = true;
    let unsubscribe = () => {};

    void getCalibrateBridgeOrThrow()
      .then((bridge) => {
        if (!active) {
          return;
        }

        if (!bridge.calibrateStatusChanged) {
          listener({ state: "error", message: BRIDGE_ERROR });
          return;
        }

        bridge.calibrateStatusChanged.connect(listener);
        unsubscribe = () => {
          bridge.calibrateStatusChanged?.disconnect?.(listener);
        };
        const currentState = bridge.getCalibrateState?.();
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

  onPreviewAspectRatio(listener: CalibrateAspectRatioListener) {
    let active = true;
    let unsubscribe = () => {};

    void getCalibrateBridgeOrThrow()
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

export default calibrateBridge;
