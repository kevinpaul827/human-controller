// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AppStateProvider from "@/state/AppStateProvider";
import { useAppState } from "@/state/appStateContext";

vi.mock("@/services/desktopStateBridge", () => ({
  desktopStateBridge: {
    getState: vi.fn().mockRejectedValue(new Error("Browser preview")),
    saveState: vi.fn(),
    deleteGesture: vi.fn(),
  },
}));

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

const StateHarness = () => {
  const { bindGesture, bindings, readiness } = useAppState();
  return (
    <div>
      <output data-testid="binding-count">{bindings.length}</output>
      <output data-testid="ready">{String(readiness.isReady)}</output>
      <button onClick={() => bindGesture("ges-jump", "Space")}>
        Bind jump
      </button>
    </div>
  );
};

describe("AppStateProvider", () => {
  let container: HTMLDivElement;
  let root: Root;
  const storedValues = new Map<string, string>();

  beforeEach(() => {
    storedValues.clear();
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: {
        clear: () => storedValues.clear(),
        getItem: (key: string) => storedValues.get(key) ?? null,
        setItem: (key: string, value: string) => storedValues.set(key, value),
      },
    });
    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);
  });

  afterEach(() => {
    if (root) {
      act(() => root.unmount());
    }
    container?.remove();
  });

  it("updates rendered readiness after a browser user binds a recorded gesture", async () => {
    storedValues.set(
      "human-controller/app-state/v2",
      JSON.stringify({
        gestures: [
          {
            gestureId: "ges-jump",
            name: "Jump",
            calibratedAt: "2026-08-08T00:00:00.000Z",
            matchScore: null,
          },
        ],
        bindings: [],
        presets: [],
        patients: [],
        selectedPatientId: null,
        activePresetId: null,
        settings: {},
      }),
    );
    await act(async () => {
      root.render(
        <AppStateProvider>
          <StateHarness />
        </AppStateProvider>,
      );
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(
      container.querySelector('[data-testid="binding-count"]')?.textContent,
    ).toBe("0");
    expect(container.querySelector('[data-testid="ready"]')?.textContent).toBe(
      "false",
    );

    const button = container.querySelector("button");
    expect(button).not.toBeNull();
    act(() => button?.click());

    expect(
      container.querySelector('[data-testid="binding-count"]')?.textContent,
    ).toBe("1");
    expect(container.querySelector('[data-testid="ready"]')?.textContent).toBe(
      "true",
    );
  });
});
