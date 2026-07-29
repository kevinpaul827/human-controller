import type {
  CalibrateAspectRatioListener,
  CalibrateBridge,
  CalibrationUpdateListener,
  CalibratePreviewBounds,
  CalibrateStatusEvent,
  CapturedRep,
  LoadSavedGestureResult,
  SavedRepResult,
  SavedGestureSummary,
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
  captureRep?: (
    callback?: (result: QtCapturedRepResult) => void,
  ) => QtCapturedRepResult | Promise<QtCapturedRepResult> | void;
  startRep?: (
    recordingSeconds: number,
    callback?: (result: QtBridgeAck) => void,
  ) => QtBridgeAck | Promise<QtBridgeAck> | void;
  cancelRep?: () => void | Promise<void>;
  stopRep?: (
    callback?: (result: QtCapturedRepResult) => void,
  ) => QtCapturedRepResult | Promise<QtCapturedRepResult> | void;
  resetRep?: () => void | Promise<void>;
  saveRep?: (
    name: string,
    gestureIdOrCallback?:
      | string
      | ((result: QtSavedRepResult) => void),
    callback?: (result: QtSavedRepResult) => void,
  ) => QtSavedRepResult | Promise<QtSavedRepResult> | void;
  listSavedGestures?: (
    callback?: (gestures: SavedGestureSummary[]) => void,
  ) => SavedGestureSummary[] | Promise<SavedGestureSummary[]> | void;
  getLoadedSessionGestures?: (
    callback?: (gestures: SavedGestureSummary[]) => void,
  ) => SavedGestureSummary[] | Promise<SavedGestureSummary[]> | void;
  loadSavedGesture?: (
    gestureId: string,
    callback?: (result: QtLoadSavedGestureResult) => void,
  ) => QtLoadSavedGestureResult | Promise<QtLoadSavedGestureResult> | void;
  getCalibrateState?: (
    callback?: (state: CalibrateStatusEvent["state"]) => void,
  ) =>
    | CalibrateStatusEvent["state"]
    | Promise<CalibrateStatusEvent["state"]>
    | void;
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

type QtBridgeErrorResult = {
  error?: string;
};

type QtBridgeAck = { ok?: boolean } & QtBridgeErrorResult;
type QtCapturedRepResult = CapturedRep & QtBridgeErrorResult;
type QtSavedRepResult = SavedRepResult & QtBridgeErrorResult;
type QtLoadSavedGestureResult = LoadSavedGestureResult & QtBridgeErrorResult;

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

const invokeWithResult = <T>(
  invoke: (callback: (result: T) => void) => unknown,
) =>
  new Promise<T>((resolve, reject) => {
    let settled = false;
    const settle = (result: T) => {
      if (settled) return;
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
            if (settled) return;
            settled = true;
            reject(error);
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
      await invokeWithResult<QtCapturedRepResult>((callback) =>
        bridge.captureRep?.(callback),
      ),
      "Unable to capture the current gesture rep.",
    );
  },

  async startRep(recordingSeconds: number) {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.startRep) {
      throw new Error("Recording controls are unavailable in this build.");
    }

    unwrapBridgeResult(
      await invokeWithResult<QtBridgeAck>((callback) =>
        bridge.startRep?.(recordingSeconds, callback),
      ),
      "Unable to start recording.",
    );
  },

  async cancelRep() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.cancelRep) {
      throw new Error("Recording controls are unavailable in this build.");
    }

    await bridge.cancelRep();
  },

  async stopRep() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.stopRep) {
      throw new Error("Recording controls are unavailable in this build.");
    }

    return unwrapBridgeResult(
      await invokeWithResult<QtCapturedRepResult>((callback) =>
        bridge.stopRep?.(callback),
      ),
      "Unable to stop recording.",
    );
  },

  async resetRep() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.resetRep) {
      throw new Error("Calibration reset is unavailable in this build.");
    }

    await bridge.resetRep();
  },

  async saveRep(name: string, gestureId?: string) {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.saveRep) {
      throw new Error("Calibration save is unavailable in this build.");
    }

    return unwrapBridgeResult(
      await invokeWithResult<QtSavedRepResult>((callback) =>
        gestureId
          ? bridge.saveRep?.(name, gestureId, callback)
          : bridge.saveRep?.(name, callback),
      ),
      "Unable to save the captured gesture reps.",
    );
  },

  async listSavedGestures() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.listSavedGestures) {
      throw new Error("Saved gesture listing is unavailable in this build.");
    }

    return (
      (await invokeWithResult<SavedGestureSummary[]>((callback) =>
        bridge.listSavedGestures?.(callback),
      )) ?? []
    );
  },

  async getLoadedSessionGestures() {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.getLoadedSessionGestures) {
      throw new Error("Loaded session gestures are unavailable in this build.");
    }

    return (
      (await invokeWithResult<SavedGestureSummary[]>((callback) =>
        bridge.getLoadedSessionGestures?.(callback),
      )) ?? []
    );
  },

  async loadSavedGesture(gestureId: string) {
    const bridge = await getCalibrateBridgeOrThrow();

    if (!bridge.loadSavedGesture) {
      throw new Error("Saved gesture loading is unavailable in this build.");
    }

    return unwrapBridgeResult(
      await invokeWithResult<QtLoadSavedGestureResult>((callback) =>
        bridge.loadSavedGesture?.(gestureId, callback),
      ),
      "Unable to load the selected saved gesture.",
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
        if (bridge.getCalibrateState) {
          void invokeWithResult<CalibrateStatusEvent["state"]>((callback) =>
            bridge.getCalibrateState?.(callback),
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
