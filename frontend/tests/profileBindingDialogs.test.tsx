import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AddBindingDialog from "../src/components/AddBindingDialog";
import CreateProfileDialog from "../src/components/CreateProfileDialog";
import {
  AppStateContext,
  type AppStateValue,
  type ResolvedBinding,
} from "../src/state/appStateContext";
import type { Gesture } from "../src/types/profile";

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => mocks.navigate,
}));

const makeGesture = (gestureId: string, name: string): Gesture => ({
  gestureId,
  name,
  calibratedAt: "2026-08-09T00:00:00.000Z",
  matchScore: null,
});

const defaultAppState = (
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
  updateSetting: () => {},
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

describe("profile and binding dialogs", () => {
  let container: HTMLDivElement;
  let root: Root;

  const queryButton = (label: string) =>
    Array.from(document.querySelectorAll("button")).find(
      (button) => button.textContent?.trim() === label,
    ) as HTMLButtonElement | undefined;

  const setFieldValue = (
    element: HTMLInputElement | HTMLTextAreaElement,
    value: string,
  ) => {
    const descriptor = Object.getOwnPropertyDescriptor(
      Object.getPrototypeOf(element),
      "value",
    );
    descriptor?.set?.call(element, value);
    element.dispatchEvent(new Event("input", { bubbles: true }));
  };

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

  it("focuses the patient name input when the profile dialog opens", async () => {
    act(() => {
      root.render(
        <CreateProfileDialog
          open
          onClose={vi.fn()}
          onCreate={vi.fn().mockResolvedValue(null)}
        />,
      );
    });
    await flushAsync();

    const input = document.getElementById("profile-patient-name");
    expect(input).toBe(document.activeElement);
  });

  it("uses keyboard capture and confirms binding when valid", async () => {
    const bindGesture = vi.fn();
    const state = defaultAppState({
      unboundGestures: [makeGesture("g-wave", "Wave")],
      bindGesture,
    });
    const onOpenChange = vi.fn();

    act(() => {
      root.render(
        <AppStateContext.Provider value={state}>
          <AddBindingDialog open onOpenChange={onOpenChange} />
        </AppStateContext.Provider>,
      );
    });

    const gestureButton = queryButton("Wave");
    expect(gestureButton).toBeDefined();
    act(() => gestureButton?.click());

    const keyInput = document.querySelector(
      'input[aria-label="Custom key"]',
    ) as HTMLInputElement | null;
    expect(keyInput).not.toBeNull();
    act(() => {
      keyInput?.dispatchEvent(
        new KeyboardEvent("keydown", { key: "q", bubbles: true }),
      );
    });
    expect(keyInput?.value).toBe("Q");

    const addButton = queryButton("Add binding");
    expect(addButton?.hasAttribute("disabled")).toBe(false);
    act(() => addButton?.click());

    expect(bindGesture).toHaveBeenCalledWith("g-wave", "Q");
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it("shows validation for invalid profile input and in-use binding keys", async () => {
    const takenGesture = makeGesture("g-hold", "Hold");
    const inUseBindings: ResolvedBinding[] = [
      { gesture: takenGesture, key: "Q", matchThreshold: 75 },
    ];

    const state = defaultAppState({
      unboundGestures: [makeGesture("g-wave", "Wave")],
      bindings: inUseBindings,
    });

    act(() => {
      root.render(
        <>
          <CreateProfileDialog
            open
            onClose={vi.fn()}
            onCreate={vi.fn().mockResolvedValue(null)}
          />
          <AppStateContext.Provider value={state}>
            <AddBindingDialog open onOpenChange={vi.fn()} />
          </AppStateContext.Provider>
        </>,
      );
    });

    const createButton = queryButton("Create profile");
    expect(createButton).toBeDefined();
    act(() => createButton?.click());
    await flushAsync();
    expect(document.body.textContent).toContain("Patient name is required.");

    const waveButton = queryButton("Wave");
    expect(waveButton).toBeDefined();
    act(() => waveButton?.click());

    const keyInput = document.querySelector(
      'input[aria-label="Custom key"]',
    ) as HTMLInputElement | null;
    act(() => {
      keyInput?.dispatchEvent(
        new KeyboardEvent("keydown", { key: "Q", bubbles: true }),
      );
    });
    await flushAsync();

    expect(document.body.textContent).toContain(
      "That key is already assigned to another movement.",
    );
    const addButton = queryButton("Add binding");
    expect(addButton?.hasAttribute("disabled")).toBe(true);
  });

  it("cancels and confirms profile creation flows", async () => {
    const onClose = vi.fn();
    const onCreate = vi.fn().mockResolvedValue(null);

    act(() => {
      root.render(
        <CreateProfileDialog open onClose={onClose} onCreate={onCreate} />,
      );
    });

    const patientNameInput = document.getElementById(
      "profile-patient-name",
    ) as HTMLInputElement | null;
    const notesInput = document.getElementById(
      "profile-notes",
    ) as HTMLTextAreaElement | null;

    act(() => {
      if (patientNameInput) {
        setFieldValue(patientNameInput, "  Casey  ");
      }
      if (notesInput) {
        setFieldValue(notesInput, "  needs reminders  ");
      }
    });

    const cancelButton = queryButton("Cancel");
    expect(cancelButton).toBeDefined();
    act(() => cancelButton?.click());
    expect(onClose).toHaveBeenCalledTimes(1);

    const createButton = queryButton("Create profile");
    expect(createButton).toBeDefined();
    act(() => createButton?.click());
    await flushAsync();

    expect(onCreate).toHaveBeenCalledWith("Casey", "needs reminders");
  });

  it("surfaces create-profile errors and shows empty-state binding dialog actions", async () => {
    const onCreate = vi.fn().mockResolvedValue("Profile already exists.");
    const onOpenChange = vi.fn();
    const state = defaultAppState({ unboundGestures: [] });

    act(() => {
      root.render(
        <>
          <CreateProfileDialog open onClose={vi.fn()} onCreate={onCreate} />
          <AppStateContext.Provider value={state}>
            <AddBindingDialog open onOpenChange={onOpenChange} />
          </AppStateContext.Provider>
        </>,
      );
    });

    const patientNameInput = document.getElementById(
      "profile-patient-name",
    ) as HTMLInputElement | null;
    act(() => {
      if (patientNameInput) {
        setFieldValue(patientNameInput, "Alex");
      }
    });

    const createButton = queryButton("Create profile");
    expect(createButton).toBeDefined();
    act(() => createButton?.click());
    await flushAsync();
    expect(document.body.textContent).toContain("Profile already exists.");

    expect(document.body.textContent).toContain(
      "Every movement in your library is already bound.",
    );
    const recordNewButton = queryButton("Record a new one");
    expect(recordNewButton).toBeDefined();
    act(() => recordNewButton?.click());
    expect(onOpenChange).toHaveBeenCalledWith(false);
    expect(mocks.navigate).toHaveBeenCalledWith("/calibrate?new=1");
  });
});
