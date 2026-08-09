// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import calibrateBridge, {
  resetCalibrateBridgeForTests,
} from "@/services/calibrateBridge";
import { resetQtWebChannelForTests } from "@/services/qtWebChannel";
import type { CalibrateStatusEvent } from "@/types/calibrate";

const installChannel = (objects: Record<string, unknown>) => {
  vi.stubGlobal("qt", { webChannelTransport: {} });
  vi.stubGlobal(
    "QWebChannel",
    class {
      constructor(
        _transport: unknown,
        callback: (channel: { objects: Record<string, unknown> }) => void,
      ) {
        callback({ objects });
      }
    },
  );
};

const baseBridge = () => ({
  startCalibrate: vi.fn(),
  stopCalibrate: vi.fn(),
  updatePreviewBounds: vi.fn(),
});

describe("calibrate bridge", () => {
  afterEach(() => {
    resetCalibrateBridgeForTests();
    resetQtWebChannelForTests();
    vi.unstubAllGlobals();
  });

  it("supports callback, Promise, and synchronous Qt methods", async () => {
    const saved = [{ gestureId: "g1", name: "Wave" }];
    installChannel({
      calibrateBridge: {
        ...baseBridge(),
        listSavedGestures: (callback: (value: typeof saved) => void) =>
          callback(saved),
        getLoadedSessionGestures: () => saved,
        loadSavedGesture: () =>
          Promise.resolve({ gesture: saved[0], loadedGestures: saved }),
      },
    });

    await expect(calibrateBridge.listSavedGestures()).resolves.toEqual(saved);
    await expect(calibrateBridge.getLoadedSessionGestures()).resolves.toEqual(
      saved,
    );
    await expect(calibrateBridge.loadSavedGesture("g1")).resolves.toEqual({
      gesture: saved[0],
      loadedGestures: saved,
    });
  });

  it("forwards calibration, recording, saving, and preview operations", async () => {
    const captured = { repCount: 3, angles: { shoulder: 45 } };
    const savedResult = { gestureId: "g1", name: "Wave", repCount: 3 };
    const loaded = [{ gestureId: "g1", name: "Wave" }];
    const bridge = {
      ...baseBridge(),
      openCameraSettings: vi.fn(() => Promise.resolve()),
      startCalibration: vi.fn(),
      startRep: vi.fn(
        (_seconds: number, callback: (value: { ok: boolean }) => void) =>
          callback({ ok: true }),
      ),
      cancelRep: vi.fn(),
      stopRep: vi.fn(() => captured),
      resetRep: vi.fn(),
      saveRep: vi.fn(
        (
          _name: string,
          _gestureIdOrCallback: string | ((value: typeof savedResult) => void),
          callback?: (value: typeof savedResult) => void,
        ) => {
          const resultCallback =
            typeof _gestureIdOrCallback === "function"
              ? _gestureIdOrCallback
              : callback;
          resultCallback?.(savedResult);
        },
      ),
      getLoadedSessionGestures: vi.fn(() => Promise.resolve(loaded)),
    };
    installChannel({ calibrateBridge: bridge });

    await expect(calibrateBridge.startCalibrate()).resolves.toBeUndefined();
    await expect(calibrateBridge.stopCalibrate()).resolves.toBeUndefined();
    await expect(calibrateBridge.openCameraSettings()).resolves.toBeUndefined();
    await expect(calibrateBridge.startCalibration()).resolves.toBeUndefined();
    await expect(calibrateBridge.startRep(4)).resolves.toBeUndefined();
    await expect(calibrateBridge.cancelRep()).resolves.toBeUndefined();
    await expect(calibrateBridge.stopRep()).resolves.toEqual(captured);
    await expect(calibrateBridge.resetRep()).resolves.toBeUndefined();
    await expect(calibrateBridge.saveRep("Wave")).resolves.toEqual(savedResult);
    await expect(calibrateBridge.saveRep("Wave", "g1")).resolves.toEqual(
      savedResult,
    );
    await expect(calibrateBridge.getLoadedSessionGestures()).resolves.toEqual(
      loaded,
    );
    await expect(
      calibrateBridge.updatePreviewBounds({
        left: 10,
        top: 20,
        width: 640,
        height: 480,
        devicePixelRatio: 2,
      }),
    ).resolves.toBeUndefined();

    expect(bridge.startRep).toHaveBeenCalledWith(4, expect.any(Function));
    expect(bridge.saveRep).toHaveBeenCalledWith("Wave", expect.any(Function));
    expect(bridge.saveRep).toHaveBeenCalledWith(
      "Wave",
      "g1",
      expect.any(Function),
    );
    expect(bridge.updatePreviewBounds).toHaveBeenCalledWith(
      10,
      20,
      640,
      480,
      2,
    );
  });

  it("reports a missing calibrate bridge", async () => {
    installChannel({});

    await expect(calibrateBridge.startCalibrate()).rejects.toThrow(
      "Qt WebChannel calibrate bridge is unavailable.",
    );
  });

  it("reports missing optional methods, bridge errors, and failures", async () => {
    installChannel({ calibrateBridge: baseBridge() });
    await expect(calibrateBridge.openCameraSettings()).rejects.toThrow(
      "Desktop camera settings are unavailable",
    );
    await expect(calibrateBridge.startCalibration()).rejects.toThrow(
      "Calibration controls are unavailable",
    );
    await expect(calibrateBridge.startRep(3)).rejects.toThrow(
      "Recording controls are unavailable",
    );
    await expect(calibrateBridge.cancelRep()).rejects.toThrow(
      "Recording controls are unavailable",
    );
    await expect(calibrateBridge.stopRep()).rejects.toThrow(
      "Recording controls are unavailable",
    );
    await expect(calibrateBridge.resetRep()).rejects.toThrow(
      "Calibration reset is unavailable",
    );
    await expect(calibrateBridge.saveRep("Wave")).rejects.toThrow(
      "Calibration save is unavailable",
    );
    await expect(calibrateBridge.listSavedGestures()).rejects.toThrow(
      "Saved gesture listing is unavailable",
    );
    await expect(calibrateBridge.getLoadedSessionGestures()).rejects.toThrow(
      "Loaded session gestures are unavailable",
    );
    await expect(calibrateBridge.loadSavedGesture("g1")).rejects.toThrow(
      "Saved gesture loading is unavailable",
    );

    resetCalibrateBridgeForTests();
    resetQtWebChannelForTests();
    installChannel({
      calibrateBridge: {
        ...baseBridge(),
        stopRep: () => ({ error: "camera unavailable" }),
        listSavedGestures: () => {
          throw new Error("list thrown");
        },
        getLoadedSessionGestures: () =>
          Promise.reject(new Error("list rejected")),
      },
    });
    await expect(calibrateBridge.stopRep()).rejects.toThrow(
      "camera unavailable",
    );
    await expect(calibrateBridge.listSavedGestures()).rejects.toThrow(
      "list thrown",
    );
    await expect(calibrateBridge.getLoadedSessionGestures()).rejects.toThrow(
      "list rejected",
    );
  });

  it("subscribes, receives, and unsubscribes from Qt signals", async () => {
    let connected: ((event: CalibrateStatusEvent) => void) | undefined;
    const connect = vi.fn((listener: (event: CalibrateStatusEvent) => void) => {
      connected = listener;
    });
    const disconnect = vi.fn();
    installChannel({
      calibrateBridge: {
        ...baseBridge(),
        calibrateStatusChanged: { connect, disconnect },
        getCalibrateState: () => "idle",
      },
    });
    const listener = vi.fn();

    const unsubscribe = calibrateBridge.onCalibrateStatus(listener);
    await vi.waitFor(() => expect(connect).toHaveBeenCalledWith(listener));
    connected?.({ state: "live" });
    expect(listener).toHaveBeenCalledWith({ state: "live" });
    unsubscribe();
    expect(disconnect).toHaveBeenCalledWith(listener);
  });

  it("subscribes and unsubscribes from calibration and preview signals", async () => {
    let calibrationCallback:
      | ((event: {
          repCount: number;
          capturing: boolean;
          phase: "recording";
          countdownRemaining: number;
        }) => void)
      | undefined;
    let previewCallback: ((aspectRatio: number) => void) | undefined;
    const calibrationDisconnect = vi.fn();
    const previewDisconnect = vi.fn();
    const calibrationSignal = {
      connect: vi.fn((callback) => {
        calibrationCallback = callback;
      }),
      disconnect: calibrationDisconnect,
    };
    const previewSignal = {
      connect: vi.fn((callback) => {
        previewCallback = callback;
      }),
      disconnect: previewDisconnect,
    };
    installChannel({
      calibrateBridge: {
        ...baseBridge(),
        calibrationUpdated: calibrationSignal,
        previewAspectRatioChanged: previewSignal,
      },
    });
    const calibrationListener = vi.fn();
    const previewListener = vi.fn();

    const stopCalibration =
      calibrateBridge.onCalibrationUpdated(calibrationListener);
    const stopPreview = calibrateBridge.onPreviewAspectRatio(previewListener);
    await vi.waitFor(() => {
      expect(calibrationSignal.connect).toHaveBeenCalledWith(
        calibrationListener,
      );
      expect(previewSignal.connect).toHaveBeenCalledWith(previewListener);
    });

    const update = {
      repCount: 1,
      capturing: true,
      phase: "recording" as const,
      countdownRemaining: 0,
    };
    calibrationCallback?.(update);
    previewCallback?.(16 / 9);
    expect(calibrationListener).toHaveBeenCalledWith(update);
    expect(previewListener).toHaveBeenCalledWith(16 / 9);

    stopCalibration();
    stopPreview();
    expect(calibrationDisconnect).toHaveBeenCalledWith(calibrationListener);
    expect(previewDisconnect).toHaveBeenCalledWith(previewListener);
  });

  it("does not connect when cleanup happens before WebChannel resolves", async () => {
    let resolveChannel:
      | ((channel: { objects: Record<string, unknown> }) => void)
      | undefined;
    const connect = vi.fn();
    const disconnect = vi.fn();
    const listener = vi.fn();
    vi.stubGlobal("qt", { webChannelTransport: {} });
    vi.stubGlobal(
      "QWebChannel",
      class {
        constructor(
          _transport: unknown,
          callback: (channel: { objects: Record<string, unknown> }) => void,
        ) {
          resolveChannel = callback;
        }
      },
    );

    const unsubscribe = calibrateBridge.onCalibrateStatus(listener);
    unsubscribe();
    resolveChannel?.({
      objects: {
        calibrateBridge: {
          ...baseBridge(),
          calibrateStatusChanged: { connect, disconnect },
        },
      },
    });
    await Promise.resolve();
    await Promise.resolve();
    expect(connect).not.toHaveBeenCalled();
    expect(disconnect).not.toHaveBeenCalled();
    expect(listener).not.toHaveBeenCalled();
  });
});
