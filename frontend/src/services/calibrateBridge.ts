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

type QtSignal<T> = {
  connect(callback: (payload: T) => void): void;
  disconnect?(callback: (payload: T) => void): void;
};

type QtCalibrateBridgeObject = {
  startCalibrate: () => void | Promise<void>;
  stopCalibrate: () => void | Promise<void>;
  startCalibration?: () => void | Promise<void>;
  captureRep?: () =>
    | (CapturedRep & { error?: string })
    | Promise<CapturedRep & { error?: string }>;
  startRep?: (
    recordingSeconds: number,
  ) =>
    | { ok?: boolean; error?: string }
    | Promise<{ ok?: boolean; error?: string }>;
  cancelRep?: () => void | Promise<void>;
  stopRep?: () =>
    | (CapturedRep & { error?: string })
    | Promise<CapturedRep & { error?: string }>;
  resetRep?: () => void | Promise<void>;
  saveRep?: (
    name: string,
    gestureId: string,
  ) =>
    | (SavedRepResult & { error?: string })
    | Promise<SavedRepResult & { error?: string }>;
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
    phase: "idle" | "countdown" | "waiting" | "recording" | "captured";
    countdownRemaining: number;
  }>;
  previewAspectRatioChanged?: QtSignal<number>;
};

const BRIDGE_NAME = "calibrateBridge";
const BRIDGE_ERROR = "Qt WebChannel calibrate bridge is unavailable.";

let bridgePromise: Promise<QtCalibrateBridgeObject> | null = null;

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

  async startCalibration() {
    const bridge = await getCalibrateBridgeOrThrow();
    if (!bridge.startCalibration)
      throw new Error("Calibration controls are unavailable.");
    await bridge.startCalibration();
  },

  async captureRep() {
    const bridge = await getCalibrateBridgeOrThrow();
    if (!bridge.captureRep)
      throw new Error("Calibration capture is unavailable.");
    const result = await bridge.captureRep();
    if (result?.error) throw new Error(result.error);
    return result;
  },

  async startRep(recordingSeconds) {
    const bridge = await getCalibrateBridgeOrThrow();
    if (!bridge.startRep)
      throw new Error("Recording controls are unavailable.");
    const result = await bridge.startRep(recordingSeconds);
    if (result?.error) throw new Error(result.error);
  },

  async cancelRep() {
    const bridge = await getCalibrateBridgeOrThrow();
    if (!bridge.cancelRep)
      throw new Error("Recording controls are unavailable.");
    await bridge.cancelRep();
  },

  async stopRep() {
    const bridge = await getCalibrateBridgeOrThrow();
    if (!bridge.stopRep) throw new Error("Recording controls are unavailable.");
    const result = await bridge.stopRep();
    if (result?.error) throw new Error(result.error);
    return result;
  },

  async resetRep() {
    const bridge = await getCalibrateBridgeOrThrow();
    if (!bridge.resetRep) throw new Error("Calibration reset is unavailable.");
    await bridge.resetRep();
  },

  async saveRep(name, gestureId) {
    const bridge = await getCalibrateBridgeOrThrow();
    if (!bridge.saveRep) throw new Error("Calibration save is unavailable.");
    const result = await bridge.saveRep(name, gestureId);
    if (result?.error) throw new Error(result.error);
    return result;
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

  onCalibrationUpdated(listener: CalibrationUpdateListener) {
    let active = true;
    let unsubscribe = () => {};
    void getCalibrateBridgeOrThrow()
      .then((bridge) => {
        if (!active || !bridge.calibrationUpdated) return;
        bridge.calibrationUpdated.connect(listener);
        unsubscribe = () => bridge.calibrationUpdated?.disconnect?.(listener);
      })
      .catch(() => {});
    return () => {
      active = false;
      unsubscribe();
    };
  },
};

export default calibrateBridge;
