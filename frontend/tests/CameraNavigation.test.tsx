// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Header from "@/components/Header";
import Session from "@/pages/Session";

const sessionBridgeMock = vi.hoisted(() => ({
  state: "idle" as "idle" | "live" | "error",
  statusListener: null as
    | ((event: { state: "idle" | "live" | "error" }) => void)
    | null,

  loadProfile: vi.fn(),
  startSession: vi.fn(),
  stopSession: vi.fn(),
  updatePreviewBounds: vi.fn(),
  openCameraSettings: vi.fn(),
  openAccessibilitySettings: vi.fn(),
  onSessionStatus: vi.fn(),
  onPreviewAspectRatio: vi.fn(),
  onGestureMatch: vi.fn(),
}));

vi.mock("@/services/sessionBridge", () => ({
  default: sessionBridgeMock,
}));

vi.mock("@/hooks/useActiveProfile", () => ({
  default: () => ({
    activeProfile: {
      patientId: "patient-1",
      patientName: "Patient 1",
    },
  }),
}));

vi.mock("@/state/appStateContext", () => ({
  useAppState: () => ({
    activePreset: null,
    readiness: {
      pending: [],
    },
    bindings: [
      {
        gesture: {
          calibratedAt: "2026",
        },
      },
    ],
  }),
}));

vi.mock("@/components/GestureMapping", () => ({
  default: () => null,
}));

vi.mock("@/components/ProfileSwitcher", () => ({
  default: () => null,
}));

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

describe("Session Navigation", () => {
  let container: HTMLDivElement;
  let root: Root;

  const renderNavigation = async () => {
    await act(async () => {
      root.render(
        <MemoryRouter initialEntries={["/"]}>
          <Header />

          <Routes>
            <Route path="/" element={<Session />} />
            <Route path="/profiles" element={<div>Profiles</div>} />
          </Routes>
        </MemoryRouter>,
      );
    });
  };

  const findNavLink = (label: string) =>
    Array.from(container.querySelectorAll("a")).find(
      (link) => link.textContent?.trim() === label,
    );

  const findButton = (label: string) =>
    Array.from(container.querySelectorAll("button")).find((button) =>
      button.textContent?.includes(label),
    );

  beforeEach(async () => {
    sessionBridgeMock.state = "idle";
    sessionBridgeMock.statusListener = null;
    vi.clearAllMocks();

    sessionBridgeMock.loadProfile.mockResolvedValue({
      patientId: "patient-1",
      gestures: [
        {
          gestureId: "gesture-1",
          name: "Wave",
          key: "Space",
        },
      ],
      missingGestureIds: [],
    });

    sessionBridgeMock.startSession.mockImplementation(async () => {
      sessionBridgeMock.state = "live";
      sessionBridgeMock.statusListener?.({ state: "live" });
    });

    sessionBridgeMock.stopSession.mockImplementation(async () => {
      sessionBridgeMock.state = "idle";
      sessionBridgeMock.statusListener?.({ state: "idle" });
    });

    sessionBridgeMock.onSessionStatus.mockImplementation((listener) => {
      sessionBridgeMock.statusListener = listener;

      listener({ state: sessionBridgeMock.state });

      return () => {
        if (sessionBridgeMock.statusListener == listener) {
          sessionBridgeMock.statusListener = null;
        }
      };
    });

    sessionBridgeMock.onPreviewAspectRatio.mockReturnValue(() => {});
    sessionBridgeMock.onGestureMatch.mockReturnValue(() => {});

    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);

    await renderNavigation();
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  it("Keep desktop session live when navigating away", async () => {
    expect(sessionBridgeMock.state).toBe("idle");

    const startButton = findButton("Start session");
    expect(startButton).toBeDefined();

    await act(async () => {
      startButton?.click();
    });
    expect(sessionBridgeMock.state).toBe("live");

    const profilesLink = findNavLink("Profiles");
    expect(profilesLink).toBeDefined();

    await act(async () => {
      profilesLink?.click();
    });
    expect(container.textContent).toContain("Profiles");
    expect(sessionBridgeMock.state).toBe("live");
  });

  it("Keep desktop session idle when navigating away", async () => {
    expect(sessionBridgeMock.state).toBe("idle");

    const startButton = findButton("Start session");
    expect(startButton).toBeDefined();

    await act(async () => {
      startButton?.click();
    });
    expect(sessionBridgeMock.state).toBe("live");

    const stopButton = findButton("Stop session");
    expect(stopButton).toBeDefined();

    await act(async () => {
      stopButton?.click();
    });
    expect(sessionBridgeMock.state).toBe("idle");

    const profilesLink = findNavLink("Profiles");
    expect(profilesLink).toBeDefined();

    await act(async () => {
      profilesLink?.click();
    });
    expect(container.textContent).toContain("Profiles");
    expect(sessionBridgeMock.state).toBe("idle");
  });
});
