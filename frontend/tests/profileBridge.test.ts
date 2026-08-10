// @vitest-environment jsdom

import { afterEach, describe, expect, it, vi } from "vitest";

import profileBridge, {
  resetProfileBridgeForTests,
} from "@/services/profileBridge";
import { resetQtWebChannelForTests } from "@/services/qtWebChannel";

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

const response = (data: unknown) => JSON.stringify({ ok: true, data });

describe("profile bridge", () => {
  afterEach(() => {
    resetProfileBridgeForTests();
    resetQtWebChannelForTests();
    vi.unstubAllGlobals();
  });

  it("supports callback, Promise, and synchronous Qt methods", async () => {
    const profile = {
      schemaVersion: 2,
      patientId: "patient-1",
      patientName: "Alex",
      notes: "",
      updatedAt: "2026-08-09T00:00:00.000Z",
      keyBindings: {},
      matchThresholds: {},
    };
    installChannel({
      profileBridge: {
        listProfiles: (callback: (value: string) => void) =>
          callback(response([profile])),
        listGestures: () =>
          Promise.resolve(response([{ gestureId: "g1", name: "Wave" }])),
        createProfile: () => response(profile),
        deleteProfile: () => response("patient-1"),
        setKeyBinding: () => response(profile),
        removeKeyBinding: () => response(profile),
      },
    });

    await expect(profileBridge.listProfiles()).resolves.toEqual([profile]);
    await expect(profileBridge.listGestures()).resolves.toEqual([
      { gestureId: "g1", name: "Wave" },
    ]);
    await expect(profileBridge.createProfile("Alex", "")).resolves.toEqual(
      profile,
    );
  });

  it("forwards delete and key-binding operations", async () => {
    const profile = {
      schemaVersion: 2,
      patientId: "patient-1",
      patientName: "Alex",
      notes: "",
      updatedAt: "2026-08-09T00:00:00.000Z",
      keyBindings: { g1: "Space" },
      matchThresholds: { g1: 75 },
    };
    const deleteProfile = vi.fn(() => response("patient-1"));
    const setKeyBinding = vi.fn(() => Promise.resolve(response(profile)));
    const removeKeyBinding = vi.fn(
      (
        _patientId: string,
        _gestureId: string,
        callback: (value: string) => void,
      ) => callback(response(profile)),
    );
    installChannel({
      profileBridge: { deleteProfile, setKeyBinding, removeKeyBinding },
    });

    await expect(profileBridge.deleteProfile("patient-1")).resolves.toBe(
      "patient-1",
    );
    await expect(
      profileBridge.setKeyBinding("patient-1", "g1", "Space"),
    ).resolves.toEqual(profile);
    await expect(
      profileBridge.removeKeyBinding("patient-1", "g1"),
    ).resolves.toEqual(profile);

    expect(deleteProfile).toHaveBeenCalledWith(
      "patient-1",
      expect.any(Function),
    );
    expect(setKeyBinding).toHaveBeenCalledWith(
      "patient-1",
      "g1",
      "Space",
      expect.any(Function),
    );
    expect(removeKeyBinding).toHaveBeenCalledWith(
      "patient-1",
      "g1",
      expect.any(Function),
    );
  });

  it("reports missing bridges and error or malformed responses", async () => {
    installChannel({});
    await expect(profileBridge.listProfiles()).rejects.toThrow(
      "Qt WebChannel profile bridge is unavailable.",
    );

    resetProfileBridgeForTests();
    resetQtWebChannelForTests();
    installChannel({
      profileBridge: {
        listProfiles: () => JSON.stringify({ ok: false, error: "denied" }),
      },
    });
    await expect(profileBridge.listProfiles()).rejects.toThrow("denied");

    resetProfileBridgeForTests();
    resetQtWebChannelForTests();
    installChannel({ profileBridge: { listProfiles: () => "not-json" } });
    await expect(profileBridge.listProfiles()).rejects.toBeInstanceOf(
      SyntaxError,
    );
  });

  it("passes through thrown exceptions and rejected Promises", async () => {
    installChannel({
      profileBridge: {
        listProfiles: () => {
          throw new Error("thrown profile failure");
        },
        listGestures: () =>
          Promise.reject(new Error("rejected profile failure")),
      },
    });

    await expect(profileBridge.listProfiles()).rejects.toThrow(
      "thrown profile failure",
    );
    await expect(profileBridge.listGestures()).rejects.toThrow(
      "rejected profile failure",
    );
  });
});
