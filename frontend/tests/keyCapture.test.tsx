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
): PatientProfile => ({
  schemaVersion: 2,
  patientId: "patient-1",
  patientName: "Alex",
  notes: "",
  updatedAt: "2026-08-09T00:00:00.000Z",
  keyBindings,
  matchThresholds: {},
});

const flushAsync = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

describe("key capture interactions", () => {
  let container: HTMLDivElement;
  let root: Root;

  const getButton = (label: string) =>
    Array.from(container.querySelectorAll("button")).find(
      (button) => button.textContent?.trim() === label,
    ) as HTMLButtonElement | undefined;

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

  const renderCard = ({
    profile,
    onSetBinding = vi.fn().mockResolvedValue(null),
  }: {
    profile: PatientProfile;
    onSetBinding?: (gestureId: string, key: string) => Promise<string | null>;
  }) => {
    act(() => {
      root.render(
        <PatientCard
          profile={profile}
          gestures={sampleGestures}
          expanded
          onExpandChange={() => {}}
          onSetBinding={onSetBinding}
          onRemoveBinding={vi.fn().mockResolvedValue(null)}
          onCalibrate={() => {}}
          onStartSession={() => {}}
          onDelete={vi.fn().mockResolvedValue(undefined)}
        />,
      );
    });
    return { onSetBinding };
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
  });

  it("captures key aliases such as Space when adding a binding", async () => {
    const { onSetBinding } = renderCard({ profile: buildProfile() });

    setSelectValue("g-jump");
    const keyInput = pressKey("Key for Alex", " ");
    expect(keyInput.value).toBe("Space");

    const addButton = getButton("Add binding");
    expect(addButton).toBeDefined();
    act(() => addButton?.click());
    await flushAsync();

    expect(onSetBinding).toHaveBeenCalledWith("g-jump", "Space");
  });

  it("shows an error when a captured key is unsupported", async () => {
    const onSetBinding = vi
      .fn()
      .mockResolvedValue("Unsupported key: use a letter, arrow, or Space.");
    renderCard({
      profile: buildProfile({ "g-wave": "Q" }),
      onSetBinding,
    });

    const changeButton = getButton("Change key");
    expect(changeButton).toBeDefined();
    act(() => changeButton?.click());

    pressKey("New key for Wave", "F13");

    const saveButton = getButton("Save");
    expect(saveButton).toBeDefined();
    act(() => saveButton?.click());
    await flushAsync();

    expect(onSetBinding).toHaveBeenCalledWith("g-wave", "F13");
    expect(container.textContent).toContain("Unsupported key");
  });

  it("replaces an existing binding key with the newly captured value", async () => {
    const { onSetBinding } = renderCard({
      profile: buildProfile({ "g-wave": "Q" }),
    });

    const changeButton = getButton("Change key");
    expect(changeButton).toBeDefined();
    act(() => changeButton?.click());

    pressKey("New key for Wave", "e");

    const saveButton = getButton("Save");
    expect(saveButton).toBeDefined();
    act(() => saveButton?.click());
    await flushAsync();

    expect(onSetBinding).toHaveBeenCalledWith("g-wave", "E");
    const editInput = container.querySelector(
      'input[aria-label="New key for Wave"]',
    );
    expect(editInput).toBeNull();
  });

  it("clears captured form values after successfully adding a binding", async () => {
    renderCard({ profile: buildProfile() });

    const select = setSelectValue("g-squat");
    const keyInput = pressKey("Key for Alex", "z");
    expect(select.value).toBe("g-squat");
    expect(keyInput.value).toBe("Z");

    const addButton = getButton("Add binding");
    expect(addButton).toBeDefined();
    act(() => addButton?.click());
    await flushAsync();

    expect(select.value).toBe("");
    expect(keyInput.value).toBe("");
  });
});
