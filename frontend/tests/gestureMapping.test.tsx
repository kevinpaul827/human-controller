import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import GestureMapping from "../src/components/GestureMapping";
import {
  AppStateContext,
  type AppStateValue,
} from "../src/state/appStateContext";
import type { Gesture, Preset } from "../src/types/profile";

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => mocks.navigate,
}));

vi.mock("@/components/AddBindingDialog", () => ({
  default: ({ open }: { open: boolean }) => (
    <output data-testid="add-binding-dialog-open">{String(open)}</output>
  ),
}));

vi.mock("@/components/KeyPicker", () => ({
  default: ({
    value,
    onChange,
  }: {
    value: string;
    onChange: (key: string) => void;
  }) => (
    <button
      type="button"
      aria-label={`key-picker-${value}`}
      onClick={() => onChange("Z")}
    >
      key-picker-{value}
    </button>
  ),
}));

vi.mock("@/components/ui/brutal-slider", () => ({
  BrutalSlider: ({
    label,
    value,
    onChange,
  }: {
    label: string;
    value: number;
    onChange: (value: number) => void;
  }) => (
    <button
      type="button"
      aria-label={`threshold-${label}`}
      onClick={() => onChange(value + 5)}
    >
      threshold-slider
    </button>
  ),
}));

const makeGesture = (
  gestureId: string,
  name: string,
  calibratedAt: string | null,
): Gesture => ({
  gestureId,
  name,
  calibratedAt,
  matchScore: null,
});

const flushAsync = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

const createState = (
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
    smoothing: 0.5,
    poseModel: "lite",
  },
  addGesture: () => "new-gesture",
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

describe("GestureMapping", () => {
  let container: HTMLDivElement;
  let root: Root;

  const renderMapping = (state: AppStateValue) => {
    act(() => {
      root.render(
        <AppStateContext.Provider value={state}>
          <GestureMapping />
        </AppStateContext.Provider>,
      );
    });
  };

  const getButtonByText = (label: string) =>
    Array.from(document.querySelectorAll("button")).find(
      (button) => button.textContent?.trim() === label,
    ) as HTMLButtonElement | undefined;

  beforeEach(() => {
    mocks.navigate.mockReset();
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

  it("renders calibrated, pending, and missing gestures and routes pending records to calibrate", () => {
    const state = createState({
      bindings: [
        {
          gesture: makeGesture(
            "ges-calibrated",
            "Calibrated wave",
            "2026-08-01",
          ),
          key: "Q",
          matchThreshold: 75,
        },
        {
          gesture: makeGesture("ges-pending", "Pending squat", null),
          key: "E",
          matchThreshold: 70,
        },
        {
          gesture: makeGesture(
            "ges-missing",
            "Missing movement (ges-missing)",
            null,
          ),
          key: "Space",
          matchThreshold: 65,
        },
      ],
    });

    renderMapping(state);

    expect(document.body.textContent).toContain("Calibrated wave");
    expect(document.body.textContent).toContain("Pending squat");
    expect(document.body.textContent).toContain(
      "Missing movement (ges-missing)",
    );

    const recordButtons = document.querySelectorAll(
      'button[title="Record this movement"]',
    );
    expect(recordButtons).toHaveLength(2);
    act(() => {
      (recordButtons[0] as HTMLButtonElement).click();
    });
    expect(mocks.navigate).toHaveBeenCalledWith(
      "/calibrate?gesture=ges-pending",
    );
  });

  it("updates thresholds through the threshold control", async () => {
    const setBindingThreshold = vi.fn();
    const state = createState({
      bindings: [
        {
          gesture: makeGesture("ges-wave", "Wave", "2026-08-01"),
          key: "Q",
          matchThreshold: 75,
        },
      ],
      setBindingThreshold,
    });

    renderMapping(state);

    const thresholdTrigger = document.querySelector(
      'button[aria-label="Adjust match threshold for Wave"]',
    ) as HTMLButtonElement | null;
    expect(thresholdTrigger).not.toBeNull();
    act(() => thresholdTrigger?.click());
    await flushAsync();

    const sliderButton = document.querySelector(
      'button[aria-label="threshold-Match threshold"]',
    ) as HTMLButtonElement | null;
    expect(sliderButton).not.toBeNull();
    act(() => sliderButton?.click());

    expect(setBindingThreshold).toHaveBeenCalledWith("ges-wave", 80);
  });

  it("rebinding via key picker calls rebindKey with the new value", () => {
    const rebindKey = vi.fn();
    const state = createState({
      bindings: [
        {
          gesture: makeGesture("ges-wave", "Wave", "2026-08-01"),
          key: "Q",
          matchThreshold: 75,
        },
      ],
      rebindKey,
    });

    renderMapping(state);

    const keyPicker = document.querySelector(
      'button[aria-label="key-picker-Q"]',
    ) as HTMLButtonElement | null;
    expect(keyPicker).not.toBeNull();
    act(() => keyPicker?.click());

    expect(rebindKey).toHaveBeenCalledWith("ges-wave", "Z");
  });

  it("deletes bindings through the remove action", () => {
    const unbindGesture = vi.fn();
    const state = createState({
      bindings: [
        {
          gesture: makeGesture("ges-wave", "Wave", "2026-08-01"),
          key: "Q",
          matchThreshold: 75,
        },
      ],
      unbindGesture,
    });

    renderMapping(state);

    const removeButton = document.querySelector(
      'button[aria-label="Remove Wave binding"]',
    ) as HTMLButtonElement | null;
    expect(removeButton).not.toBeNull();
    act(() => removeButton?.click());

    expect(unbindGesture).toHaveBeenCalledWith("ges-wave");
  });

  it("shows empty-state and disables save while no bindings exist", () => {
    const samplePreset: Preset = {
      presetId: "preset-1",
      name: "Starter",
      bindings: [],
    };
    const state = createState({
      presets: [samplePreset],
      bindings: [],
    });

    renderMapping(state);

    expect(document.body.textContent).toContain("Nothing bound yet");

    const saveButton = document.querySelector(
      'button[aria-label="Save bindings as preset"]',
    ) as HTMLButtonElement | null;
    expect(saveButton?.hasAttribute("disabled")).toBe(true);

    const addBindingButton = getButtonByText("Add binding");
    expect(addBindingButton).toBeDefined();
    act(() => addBindingButton?.click());

    const addBindingDialogState = document.querySelector(
      '[data-testid="add-binding-dialog-open"]',
    );
    expect(addBindingDialogState?.textContent).toBe("true");
  });
});
