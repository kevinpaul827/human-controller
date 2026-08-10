import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import PatientCard from "../src/components/PatientCard";
import type { GestureSummary, PatientProfile } from "../src/types/profile";

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

const sampleGestures: GestureSummary[] = [
  { gestureId: "g-wave", name: "Wave" },
  { gestureId: "g-squat", name: "Squat" },
  { gestureId: "g-jump", name: "Jump" },
];

const buildProfile = (
  keyBindings: Record<string, string> = {},
  updatedAt = "2026-08-09T00:00:00.000Z",
): PatientProfile => ({
  schemaVersion: 2,
  patientId: "patient-1",
  patientName: "Alex",
  notes: "",
  updatedAt,
  keyBindings,
  matchThresholds: {},
});

const flushAsync = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

describe("PatientCard", () => {
  let container: HTMLDivElement;
  let root: Root;

  const getButton = (label: string) =>
    Array.from(container.querySelectorAll("button")).find(
      (button) => button.textContent?.trim() === label,
    ) as HTMLButtonElement | undefined;

  const pressKey = (label: string, key: string) => {
    const input = container.querySelector(`input[aria-label="${label}"]`);
    if (!(input instanceof HTMLInputElement)) {
      throw new Error(`Key input "${label}" not found.`);
    }
    act(() => {
      input.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true }));
    });
    return input;
  };

  const setSelectValue = (value: string) => {
    const select = container.querySelector("select");
    if (!(select instanceof HTMLSelectElement)) {
      throw new Error("Movement select not found.");
    }
    act(() => {
      select.value = value;
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
    return select;
  };

  const renderCard = ({
    profile = buildProfile(),
    gestures = sampleGestures,
    onSetBinding = vi.fn().mockResolvedValue(null),
    onRemoveBinding = vi.fn().mockResolvedValue(null),
    onDelete = vi.fn().mockResolvedValue(undefined),
  }: {
    profile?: PatientProfile;
    gestures?: GestureSummary[];
    onSetBinding?: (gestureId: string, key: string) => Promise<string | null>;
    onRemoveBinding?: (gestureId: string) => Promise<string | null>;
    onDelete?: () => Promise<void>;
  } = {}) => {
    act(() => {
      root.render(
        <PatientCard
          profile={profile}
          gestures={gestures}
          expanded
          onExpandChange={() => {}}
          onSetBinding={onSetBinding}
          onRemoveBinding={onRemoveBinding}
          onCalibrate={() => {}}
          onStartSession={() => {}}
          onDelete={onDelete}
        />,
      );
    });

    return { onSetBinding, onRemoveBinding, onDelete };
  };

  beforeEach(() => {
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
    vi.restoreAllMocks();
  });

  it("selects a movement and adds a binding from captured key input", async () => {
    const { onSetBinding } = renderCard({ profile: buildProfile() });

    const select = setSelectValue("g-squat");
    const input = pressKey("Key for Alex", "e");

    expect(select.value).toBe("g-squat");
    expect(input.value).toBe("E");

    const addBindingButton = getButton("Add binding");
    expect(addBindingButton).toBeDefined();
    act(() => addBindingButton?.click());
    await flushAsync();

    expect(onSetBinding).toHaveBeenCalledWith("g-squat", "E");
    expect(select.value).toBe("");
    expect(input.value).toBe("");
  });

  it("edits an existing binding and saves a replacement key", async () => {
    const { onSetBinding } = renderCard({
      profile: buildProfile({ "g-wave": "Q" }),
    });

    const changeButton = getButton("Change key");
    expect(changeButton).toBeDefined();
    act(() => changeButton?.click());

    const editInput = pressKey("New key for Wave", "r");
    expect(editInput.value).toBe("R");

    const saveButton = getButton("Save");
    expect(saveButton).toBeDefined();
    act(() => saveButton?.click());
    await flushAsync();

    expect(onSetBinding).toHaveBeenCalledWith("g-wave", "R");
    expect(
      container.querySelector('input[aria-label="New key for Wave"]'),
    ).toBe(null);
  });

  it("runs delete confirmation before deleting a patient card", async () => {
    const performDelete = vi.fn().mockResolvedValue(undefined);
    const confirmSpy = vi
      .spyOn(window, "confirm")
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true);

    const onDelete = vi.fn(async () => {
      if (window.confirm("Delete this profile?")) {
        await performDelete();
      }
    });

    renderCard({ onDelete });

    const deleteButton = getButton("Delete");
    expect(deleteButton).toBeDefined();

    act(() => deleteButton?.click());
    await flushAsync();
    expect(performDelete).not.toHaveBeenCalled();

    act(() => deleteButton?.click());
    await flushAsync();
    expect(performDelete).toHaveBeenCalledTimes(1);
    expect(confirmSpy).toHaveBeenCalledTimes(2);
  });

  it("surfaces binding change errors from failed actions", async () => {
    const { onRemoveBinding } = renderCard({
      profile: buildProfile({ "g-wave": "Q" }),
      onRemoveBinding: vi
        .fn()
        .mockResolvedValue("Unable to remove binding right now."),
    });

    const removeButton = getButton("Remove");
    expect(removeButton).toBeDefined();
    act(() => removeButton?.click());
    await flushAsync();

    expect(onRemoveBinding).toHaveBeenCalledWith("g-wave");
    expect(container.textContent).toContain(
      "Unable to remove binding right now.",
    );
  });

  it("shows patient-card empty states for no bindings and no gestures", () => {
    renderCard({
      profile: buildProfile(),
      gestures: [],
    });

    expect(container.textContent).toContain(
      "No movements are bound to this profile yet.",
    );
    expect(container.textContent).toContain(
      "No calibrated movements are available yet.",
    );
  });
});
