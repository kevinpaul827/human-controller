// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import sessionBridge, {
  resetSessionBridgeForTests,
} from "@/services/sessionBridge";
import { resetQtWebChannelForTests } from "@/services/qtWebChannel";
import type { SessionStatusEvent } from "@/types/session";

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
  startSession: vi.fn(),
  stopSession: vi.fn(),
  updatePreviewBounds: vi.fn(),
});

describe("session bridge", () => {
  afterEach(() => {
    resetSessionBridgeForTests();
    resetQtWebChannelForTests();
    vi.unstubAllGlobals();
  });

  it("supports callback, Promise, and synchronous Qt methods", async () => {
    const data = {
      patientId: "patient-1",
      gestures: [{ gestureId: "g1", name: "Wave", key: "Space" }],
      missingGestureIds: [],
    };
    installChannel({
      sessionBridge: {
        ...baseBridge(),
        loadProfile: (
          _id: string,
          callback: (value: { ok: boolean; data: typeof data }) => void,
        ) => callback({ ok: true, data }),
        getLoadedSessionGestures: () => data.gestures,
        openCameraSettings: () => Promise.resolve(),
      },
    });

    await expect(sessionBridge.loadProfile("patient-1")).resolves.toEqual(data);
    await expect(sessionBridge.getLoadedSessionGestures()).resolves.toEqual(
      data.gestures,
    );
    await expect(sessionBridge.openCameraSettings()).resolves.toBeUndefined();
  });

  it("forwards session controls, accessibility, and preview bounds", async () => {
    const bridge = {
      ...baseBridge(),
      startSession: vi.fn(() => Promise.resolve()),
      stopSession: vi.fn(),
      openAccessibilitySettings: vi.fn(() => Promise.resolve()),
    };
    installChannel({ sessionBridge: bridge });

    await expect(sessionBridge.startSession()).resolves.toBeUndefined();
    await expect(sessionBridge.stopSession()).resolves.toBeUndefined();
    await expect(
      sessionBridge.openAccessibilitySettings(),
    ).resolves.toBeUndefined();
    await expect(
      sessionBridge.updatePreviewBounds({
        left: 1,
        top: 2,
        width: 1280,
        height: 720,
        devicePixelRatio: 1.5,
      }),
    ).resolves.toBeUndefined();

    expect(bridge.startSession).toHaveBeenCalledOnce();
    expect(bridge.stopSession).toHaveBeenCalledOnce();
    expect(bridge.openAccessibilitySettings).toHaveBeenCalledOnce();
    expect(bridge.updatePreviewBounds).toHaveBeenCalledWith(
      1,
      2,
      1280,
      720,
      1.5,
    );
  });

  it("reports a missing session bridge", async () => {
    installChannel({});

    await expect(sessionBridge.startSession()).rejects.toThrow(
      "Qt WebChannel session bridge is unavailable.",
    );
  });

  it("reports missing optional methods, error payloads, and failures", async () => {
    installChannel({ sessionBridge: baseBridge() });
    await expect(sessionBridge.loadProfile("patient-1")).rejects.toThrow(
      "Profile-aware sessions are unavailable",
    );
    await expect(sessionBridge.getLoadedSessionGestures()).rejects.toThrow(
      "Loaded session gestures unavailable",
    );
    await expect(sessionBridge.openCameraSettings()).rejects.toThrow(
      "Desktop camera settings are unavailable",
    );
    await expect(sessionBridge.openAccessibilitySettings()).rejects.toThrow(
      "Desktop accessibility settings are unavailable",
    );

    resetSessionBridgeForTests();
    resetQtWebChannelForTests();
    installChannel({
      sessionBridge: {
        ...baseBridge(),
        loadProfile: () => ({ ok: false, error: "patient missing" }),
        getLoadedSessionGestures: () => {
          throw new Error("gesture list thrown");
        },
        openCameraSettings: () => Promise.reject(new Error("camera rejected")),
      },
    });
    await expect(sessionBridge.loadProfile("patient-1")).rejects.toThrow(
      "patient missing",
    );
    await expect(sessionBridge.getLoadedSessionGestures()).rejects.toThrow(
      "gesture list thrown",
    );
    await expect(sessionBridge.openCameraSettings()).rejects.toThrow(
      "camera rejected",
    );
  });

  it("subscribes, receives, and unsubscribes from status signals", async () => {
    let connected: ((event: SessionStatusEvent) => void) | undefined;
    const connect = vi.fn((listener: (event: SessionStatusEvent) => void) => {
      connected = listener;
    });
    const disconnect = vi.fn();
    installChannel({
      sessionBridge: {
        ...baseBridge(),
        sessionStatusChanged: { connect, disconnect },
        getSessionState: () => Promise.resolve("idle"),
      },
    });
    const listener = vi.fn();

    const unsubscribe = sessionBridge.onSessionStatus(listener);
    await vi.waitFor(() => expect(connect).toHaveBeenCalledWith(listener));
    connected?.({ state: "live" });
    expect(listener).toHaveBeenCalledWith({ state: "live" });
    unsubscribe();
    expect(disconnect).toHaveBeenCalledWith(listener);
  });

  it("subscribes and unsubscribes from gesture and preview signals", async () => {
    let gestureCallback:
      | ((event: {
          gestureId: string;
          name: string;
          score: number;
          matched: boolean;
          hasTemplates: boolean;
        }) => void)
      | undefined;
    let previewCallback: ((aspectRatio: number) => void) | undefined;
    const gestureDisconnect = vi.fn();
    const previewDisconnect = vi.fn();
    const gestureSignal = {
      connect: vi.fn((callback) => {
        gestureCallback = callback;
      }),
      disconnect: gestureDisconnect,
    };
    const previewSignal = {
      connect: vi.fn((callback) => {
        previewCallback = callback;
      }),
      disconnect: previewDisconnect,
    };
    installChannel({
      sessionBridge: {
        ...baseBridge(),
        gestureMatchUpdated: gestureSignal,
        previewAspectRatioChanged: previewSignal,
      },
    });
    const gestureListener = vi.fn();
    const previewListener = vi.fn();

    const stopGesture = sessionBridge.onGestureMatch(gestureListener);
    const stopPreview = sessionBridge.onPreviewAspectRatio(previewListener);
    await vi.waitFor(() => {
      expect(gestureSignal.connect).toHaveBeenCalledWith(gestureListener);
      expect(previewSignal.connect).toHaveBeenCalledWith(previewListener);
    });

    const match = {
      gestureId: "g1",
      name: "Wave",
      score: 0.95,
      matched: true,
      hasTemplates: true,
    };
    gestureCallback?.(match);
    previewCallback?.(4 / 3);
    expect(gestureListener).toHaveBeenCalledWith(match);
    expect(previewListener).toHaveBeenCalledWith(4 / 3);

    stopGesture();
    stopPreview();
    expect(gestureDisconnect).toHaveBeenCalledWith(gestureListener);
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

    const unsubscribe = sessionBridge.onSessionStatus(listener);
    unsubscribe();
    resolveChannel?.({
      objects: {
        sessionBridge: {
          ...baseBridge(),
          sessionStatusChanged: { connect, disconnect },
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
