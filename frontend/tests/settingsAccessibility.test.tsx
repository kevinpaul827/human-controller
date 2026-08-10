import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import SessionCameraErrorModal from "../src/components/modals/SessionCameraErrorModal";
import Settings from "../src/pages/Settings";
import {
  AppStateContext,
  type AppStateValue,
} from "../src/state/appStateContext";

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

const bridgeMocks = vi.hoisted(() => ({
  recommendPoseModel: vi.fn(),
}));

vi.mock("../src/services/desktopStateBridge", () => ({
  desktopStateBridge: {
    recommendPoseModel: bridgeMocks.recommendPoseModel,
  },
}));

const createAppState = (
  overrides: Partial<AppStateValue> = {},
): AppStateValue => ({
  gestures: [],
  bindings: [],
  unboundGestures: [],
  presets: [],
  patients: [],
  selectedPatient: null,
  activePreset: null,
  hasUnsavedChanges: false,
  readiness: { total: 0, recorded: 0, pending: [], isReady: false },
  undoLabel: null,
  settings: {
    matchThreshold: 75,
    holdDuration: 0.5,
    cooldown: 0.3,
    smoothing: 2,
    poseModel: "lite",
  },
  addGesture: () => "gesture-id",
  renameGesture: () => {},
  deleteGesture: () => {},
  completeRecording: () => {},
  bindGesture: () => {},
  rebindKey: () => {},
  setBindingThreshold: () => {},
  unbindGesture: () => {},
  setPatientBinding: () => {},
  removePatientBinding: () => {},
  savePreset: () => {},
  loadPreset: () => {},
  deletePreset: () => {},
  selectPatient: async () => {},
  createPatient: async () => null,
  deletePatient: async () => {},
  clearPatientSelection: async () => {},
  refreshState: async () => {},
  updateSetting: (() => {}) as AppStateValue["updateSetting"],
  undo: () => {},
  dismissUndo: () => {},
  ...overrides,
});

const flushAsync = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

describe("Settings and accessibility", () => {
  let container: HTMLDivElement;
  let root: Root;

  const renderSettings = (state: AppStateValue) => {
    act(() => {
      root.render(
        <AppStateContext.Provider value={state}>
          <Settings />
        </AppStateContext.Provider>,
      );
    });
  };

  const clickButton = (label: string) => {
    const button = Array.from(document.querySelectorAll("button")).find(
      (candidate) => candidate.textContent?.trim() === label,
    ) as HTMLButtonElement | undefined;
    if (!button) {
      throw new Error(`Button "${label}" not found.`);
    }
    act(() => button.click());
    return button;
  };

  const getButton = (label: string) =>
    Array.from(document.querySelectorAll("button")).find(
      (candidate) => candidate.textContent?.trim() === label,
    ) as HTMLButtonElement | undefined;

  beforeEach(() => {
    vi.clearAllMocks();
    bridgeMocks.recommendPoseModel.mockResolvedValue({
      poseModel: "full",
      ramGb: 16,
      physicalCpuCount: 8,
      logicalCpuCount: 16,
    });
    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container?.remove();
  });

  it("handles recommendation success with a live status update", async () => {
    const updateSetting = vi.fn();
    renderSettings(createAppState({ updateSetting }));

    clickButton("Calibrate tracking");
    await flushAsync();

    expect(bridgeMocks.recommendPoseModel).toHaveBeenCalledTimes(1);
    expect(updateSetting).toHaveBeenCalledWith("poseModel", "full");

    const status = document.querySelector('[role="status"]');
    expect(status).not.toBeNull();
    expect(status?.getAttribute("aria-live")).toBe("polite");
    expect(status?.textContent).toContain("Balanced selected");
    expect(status?.textContent).toContain("16 GB RAM");
    expect(status?.textContent).toContain("8 physical CPU cores");
  });

  it("handles recommendation failure by showing alert and opening manual selection", async () => {
    bridgeMocks.recommendPoseModel.mockRejectedValueOnce(
      new Error("No bridge"),
    );
    renderSettings(createAppState());

    clickButton("Calibrate tracking");
    await flushAsync();

    const alert = document.querySelector('[role="alert"]');
    expect(alert).not.toBeNull();
    expect(alert?.textContent).toContain(
      "Couldn’t check this device. Choose a mode manually.",
    );

    const details = document.querySelector(
      "details",
    ) as HTMLDetailsElement | null;
    expect(details?.open).toBe(true);
  });

  it("allows manually selecting a pose model and supports keyboard focus flow", () => {
    const updateSetting = vi.fn();
    renderSettings(createAppState({ updateSetting }));

    const calibrateButton = getButton("Calibrate tracking");
    expect(calibrateButton).toBeDefined();

    const summary = document.querySelector("summary") as HTMLElement | null;
    expect(summary).not.toBeNull();

    const relation = calibrateButton?.compareDocumentPosition(summary as Node);
    expect(
      relation && relation & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();

    act(() => {
      summary?.focus();
      summary?.click();
    });
    expect(document.activeElement).toBe(summary);

    const heavyRadio = document.querySelector(
      'input[name="tracking-mode"][value="heavy"]',
    ) as HTMLInputElement | null;
    expect(heavyRadio).not.toBeNull();

    act(() => {
      heavyRadio?.click();
    });

    expect(updateSetting).toHaveBeenCalledWith("poseModel", "heavy");
  });

  it("exposes labels for settings controls and does not rely on color alone for status", () => {
    renderSettings(createAppState());

    const ranges = Array.from(
      document.querySelectorAll('input[type="range"]'),
    ) as HTMLInputElement[];

    expect(ranges.length).toBeGreaterThanOrEqual(3);

    for (const range of ranges) {
      expect(range.id).toBeTruthy();
      const label = document.querySelector(`label[for="${range.id}"]`);
      expect(label).toBeDefined();
      expect(label?.textContent?.trim().length).toBeGreaterThan(0);
    }

    expect(document.body.textContent).toContain("Camera tracking");
    expect(document.body.textContent).toContain("Current:");
  });

  it("supports dialog actions for accessibility errors", () => {
    const onCancel = vi.fn();
    const onConfigure = vi.fn();

    act(() => {
      root.render(
        <SessionCameraErrorModal
          open
          kind="accessibility"
          onCancel={onCancel}
          onConfigure={onConfigure}
        />,
      );
    });

    expect(document.body.textContent).toContain("Keyboard access required");

    const dismissButton = Array.from(document.querySelectorAll("button")).find(
      (button) => button.textContent?.trim() === "Dismiss",
    ) as HTMLButtonElement | undefined;
    expect(dismissButton).toBeDefined();

    act(() => {
      dismissButton?.focus();
      dismissButton?.click();
    });
    expect(document.activeElement).toBe(dismissButton);
    expect(onCancel).toHaveBeenCalledTimes(1);

    const configureButton = Array.from(
      document.querySelectorAll("button"),
    ).find(
      (button) => button.textContent?.trim() === "Open accessibility settings",
    ) as HTMLButtonElement | undefined;
    expect(configureButton).toBeDefined();

    act(() => {
      configureButton?.focus();
      configureButton?.click();
    });
    expect(document.activeElement).toBe(configureButton);
    expect(onConfigure).toHaveBeenCalledTimes(1);
  });
});
