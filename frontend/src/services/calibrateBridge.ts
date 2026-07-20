import type {
  CalibrateAspectRatioListener,
  CalibrateBridge,
  CalibrationUpdateListener,
  CalibratePreviewBounds,
  CalibrateStatusEvent,
  CapturedRep,
  SavedRepResult,
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
  startCalibration?: () => void | Promise<void>;
  captureRep?: () => QtCapturedRepResult | Promise<QtCapturedRepResult>;
  resetRep?: () => void | Promise<void>;
  saveRep?: (name: string) => QtSavedRepResult | Promise<QtSavedRepResult>;
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
  calibrationUpdated?: QtSignal<{
    repCount: number;
    capturing: boolean;
  }>;
  previewAspectRatioChanged?: QtSignal<number>;
};

type QtBridgeErrorResult = {
  error?: string;
};

type QtCapturedRepResult = CapturedRep & QtBridgeErrorResult;
type QtSavedRepResult = SavedRepResult & QtBridgeErrorResult;

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

const unwrapBridgeResult = <T extends object>(
  result: (T & QtBridgeErrorResult) | null | undefined,
  fallbackMessage: string,
): T => {
  if (result?.error) {
    throw new Error(result.error);
  }

  if (!result || typeof result !== "object") {
    throw new Error(fallbackMessage);
  }

  return result;
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

  async startCalibration() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.startCalibration) {
      throw new Error("Calibration controls are unavailable in this build.");
    }

    await bridge.startCalibration();
  },

  async captureRep() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.captureRep) {
      throw new Error("Calibration capture is unavailable in this build.");
    }

    return unwrapBridgeResult(
      await bridge.captureRep(),
      "Unable to capture the current gesture rep.",
    );
  },

  async resetRep() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.resetRep) {
      throw new Error("Calibration reset is unavailable in this build.");
    }

    await bridge.resetRep();
  },

  async saveRep(name: string) {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.saveRep) {
      throw new Error("Calibration save is unavailable in this build.");
    }

    return unwrapBridgeResult(
      await bridge.saveRep(name),
      "Unable to save the captured gesture reps.",
    );
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

  onCalibrationUpdated(listener: CalibrationUpdateListener) {
    let active = true;
    let unsubscribe = () => {};

    void getCalibrateBridgeOrThrow()
      .then((bridge) => {
        if (!active) {
          return;
        }

        if (!bridge.calibrationUpdated) {
          return;
        }

        bridge.calibrationUpdated.connect(listener);
        unsubscribe = () => {
          bridge.calibrationUpdated?.disconnect?.(listener);
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
