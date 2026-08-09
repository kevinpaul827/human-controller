// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import {
  desktopStateBridge,
  resetDesktopStateBridgeForTests,
} from "@/services/desktopStateBridge";
import { resetQtWebChannelForTests } from "@/services/qtWebChannel";
import { initialState } from "@/state/appStateModel";

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

describe("desktop state bridge", () => {
  afterEach(() => {
    resetDesktopStateBridgeForTests();
    resetQtWebChannelForTests();
    vi.unstubAllGlobals();
    Reflect.deleteProperty(window.navigator, "deviceMemory");
    Reflect.deleteProperty(window.navigator, "hardwareConcurrency");
  });

  it("supports callback, Promise, and synchronous Qt methods", async () => {
    const state = initialState();
    const saved = { ...state, selectedPatientId: "patient-1" };
    installChannel({
      stateBridge: {
        getState: (callback: (value: typeof state) => void) => callback(state),
        saveState: () => Promise.resolve(saved),
        selectPatient: () => saved,
      },
    });

    await expect(desktopStateBridge.getState()).resolves.toBe(state);
    await expect(desktopStateBridge.saveState(state)).resolves.toBe(saved);
    await expect(desktopStateBridge.selectPatient("patient-1")).resolves.toBe(
      saved,
    );
  });

  it("selects lite, full, and heavy browser pose recommendations", async () => {
    const setHardware = (logicalCpus: number, ramGb: number) => {
      Object.defineProperty(window.navigator, "hardwareConcurrency", {
        configurable: true,
        value: logicalCpus,
      });
      Object.defineProperty(window.navigator, "deviceMemory", {
        configurable: true,
        value: ramGb,
      });
    };

    setHardware(0, 0);
    await expect(desktopStateBridge.recommendPoseModel()).resolves.toEqual({
      poseModel: "lite",
      ramGb: null,
      physicalCpuCount: null,
      logicalCpuCount: null,
    });

    setHardware(8, 8);
    await expect(
      desktopStateBridge.recommendPoseModel(),
    ).resolves.toMatchObject({
      poseModel: "full",
      ramGb: 8,
      logicalCpuCount: 8,
    });

    setHardware(12, 16);
    await expect(
      desktopStateBridge.recommendPoseModel(),
    ).resolves.toMatchObject({
      poseModel: "heavy",
      ramGb: 16,
      logicalCpuCount: 12,
    });
  });

  it("uses the Qt pose recommendation in the desktop runtime", async () => {
    const recommendation = {
      poseModel: "heavy" as const,
      ramGb: 32,
      physicalCpuCount: 8,
      logicalCpuCount: 16,
    };
    const recommendPoseModel = vi.fn(
      (callback: (value: typeof recommendation) => void) =>
        callback(recommendation),
    );
    installChannel({ stateBridge: { recommendPoseModel } });

    await expect(desktopStateBridge.recommendPoseModel()).resolves.toEqual(
      recommendation,
    );
    expect(recommendPoseModel).toHaveBeenCalledWith(expect.any(Function));
  });

  it("forwards profile and gesture state operations", async () => {
    const state = initialState();
    const createProfile = vi.fn(
      (
        _name: string,
        _notes: string,
        callback: (value: typeof state) => void,
      ) => callback(state),
    );
    const deleteProfile = vi.fn(() => Promise.resolve(state));
    const clearPatientSelection = vi.fn(() => state);
    const deleteGesture = vi.fn(
      (_gestureId: string, callback: (value: typeof state) => void) =>
        callback(state),
    );
    installChannel({
      stateBridge: {
        createProfile,
        deleteProfile,
        clearPatientSelection,
        deleteGesture,
      },
    });

    await expect(desktopStateBridge.createProfile("Taylor")).resolves.toBe(
      state,
    );
    await expect(desktopStateBridge.deleteProfile("patient-1")).resolves.toBe(
      state,
    );
    await expect(desktopStateBridge.clearPatientSelection()).resolves.toBe(
      state,
    );
    await expect(desktopStateBridge.deleteGesture("gesture-1")).resolves.toBe(
      state,
    );

    expect(createProfile).toHaveBeenCalledWith(
      "Taylor",
      "",
      expect.any(Function),
    );
    expect(deleteProfile).toHaveBeenCalledWith(
      "patient-1",
      expect.any(Function),
    );
    expect(clearPatientSelection).toHaveBeenCalledWith(expect.any(Function));
    expect(deleteGesture).toHaveBeenCalledWith(
      "gesture-1",
      expect.any(Function),
    );
  });

  it("reports missing bridges and passes through failures", async () => {
    installChannel({});
    await expect(desktopStateBridge.getState()).rejects.toThrow(
      "Desktop state bridge is unavailable.",
    );

    resetDesktopStateBridgeForTests();
    resetQtWebChannelForTests();
    installChannel({
      stateBridge: {
        getState: () => {
          throw new Error("state thrown");
        },
        saveState: () => Promise.reject(new Error("state rejected")),
      },
    });
    await expect(desktopStateBridge.getState()).rejects.toThrow("state thrown");
    await expect(desktopStateBridge.saveState(initialState())).rejects.toThrow(
      "state rejected",
    );
  });
});
