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
    | ((event: { 
        state: "idle" | "live" | "error";
        message?: string;
        settingsTarget?: "camera" | "accessibility"; 
      }) => void)
    | null,
  
  gestureListener: null as
    | ((event: {
        gestureId: string | null;
        name: string | null;
        score: number;
        matched: boolean;
        hasTemplates: boolean;
        triggered?: boolean;
        key?: string;
        injectionError?: string;
        keyAction?: "press" | "release" | "reset";
    }) => void)
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

const activeProfileMock = vi.hoisted(() => ({
  activeProfile: {
    patientId: "patient-1",
    patientName: "Patient 1",
  } as {
    patientId: string;
    patientName: string;
  } | null
}));

vi.mock("@/hooks/useActiveProfile", () => ({
  default: () => ({
    activeProfile: activeProfileMock.activeProfile
  }),
}));

const appStateMock = vi.hoisted(() => ({
  bindings: [
    {
      gesture: {
        calibratedAt: "2026",
      }
    }
  ] as Array<{
    gesture: {
      calibratedAt: string | null
    };
  }>
}));

vi.mock("@/state/appStateContext", () => ({
  useAppState: () => ({
    activePreset: null,
    readiness: {
      pending: [],
    },
    bindings: appStateMock.bindings
  }),
}));

vi.mock("@/components/GestureMapping", () => ({
  default: () => null,
}));

vi.mock("@/components/ProfileSwitcher", () => ({
  default: () => null,
}));

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

describe("Session Camera", () => {
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
    Array.from(document.querySelectorAll("a")).find(
      (link) => link.textContent?.trim() === label,
    );

  const findButton = (label: string) =>
    Array.from(document.querySelectorAll("button")).find((button) =>
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

    sessionBridgeMock.onGestureMatch.mockImplementation((listener) => {
      sessionBridgeMock.gestureListener = listener;
      return () => {
        sessionBridgeMock.gestureListener = null;
      };
    });

    sessionBridgeMock.onPreviewAspectRatio.mockReturnValue(() => {});

    activeProfileMock.activeProfile = {
      patientId: "patient-1",
      patientName: "Patient 1"
    };

    appStateMock.bindings = [
      {
        gesture: {
          calibratedAt: "2026"
        }
      }
    ];

    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);

    await renderNavigation();
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
  });

  it("warning when no profile is selected", async () => {
    activeProfileMock.activeProfile = null;
    await renderNavigation();
    expect(container.textContent).toContain(
      "No patient selected. Add a binding, go to calibration, or choose a profile."
    );

    const startButton = findButton("Start session");
    expect(startButton?.disabled).toBe(true);
  });

  it("warning when no bindings loaded", async () => {
    appStateMock.bindings = [];
    await renderNavigation();
    expect(container.textContent).toContain(
      "This profile has no usable movement key bindings. Please add key bindings or calibrate new gestures."
    );

    const startButton = findButton("Start session");
    expect(startButton?.disabled).toBe(true);
  });

  it("show camera error", async () => {
    sessionBridgeMock.startSession.mockRejectedValue(new Error("Camera unavailable"));
    const startButton = findButton("Start session");
    await act(async () => {
      startButton?.click();
    });

    expect(document.body.textContent).toContain("Camera error");
    expect(document.body.textContent).toContain("Camera unavailable");

    const dismissButton = findButton("Dismiss");
    expect(dismissButton).toBeDefined();

    const cameraSettingsButton = findButton("Open camera settings");
    expect(cameraSettingsButton).toBeDefined();

    await act(async () => {
      cameraSettingsButton?.click();
    });
    expect(sessionBridgeMock.openCameraSettings).toHaveBeenCalledOnce();

    await act(async() => {
      dismissButton?.click();
    });
    expect(sessionBridgeMock.stopSession).toHaveBeenCalledOnce();
  });

  it("show accessibility error", async () => {
    await act(async () => {
      sessionBridgeMock.statusListener?.({
        state: "error",
        message: "Accessibility error",
        settingsTarget: "accessibility"
      });
    });

    expect(document.body.textContent).toContain("Keyboard access required");
    expect(document.body.textContent).toContain("Accessibility error");

    const dismissButton = findButton("Dismiss");
    expect(dismissButton).toBeDefined();

    const accessibilityButton = findButton("Open accessibility settings");
    expect(accessibilityButton).toBeDefined();

    await act(async () => {
      accessibilityButton?.click();
    });
    expect(sessionBridgeMock.openAccessibilitySettings).toHaveBeenCalledOnce();

    await act(async() => {
      dismissButton?.click();
    });
    expect(sessionBridgeMock.stopSession).toHaveBeenCalledOnce();
  });

  it("check camera idle and live", async () => {
    expect(sessionBridgeMock.state).toBe("idle");
    expect(container.textContent).toContain(
      "Starting the session opens the separate camera overlay."
    )
    expect(container.textContent).toContain("Idle")

    let startButton = findButton("Start session");
    expect(startButton).toBeDefined();

    let stopButton = findButton("Stop session");
    expect(stopButton).toBeUndefined();

    await act(async () => {
      startButton?.click();
    });
    expect(sessionBridgeMock.state).toBe("live");
    expect(container.textContent).toContain(
      "Switch to your game; the separate camera window stays on top."
    );
    expect(container.textContent).toContain("REC")
    expect(container.textContent).toContain("Waiting for a movement")

    startButton = findButton("Start session");
    stopButton = findButton("Stop session");

    expect(startButton).toBeUndefined();
    expect(stopButton).toBeDefined();

    await act(async () => {
      stopButton?.click();
    });
    expect(sessionBridgeMock.state).toBe("idle");

    startButton = findButton("Start session");
    stopButton = findButton("Stop session");

    expect(startButton).toBeDefined();
    expect(stopButton).toBeUndefined();
  });

  it("keep session camera live when navigating away", async () => {
    let startButton = findButton("Start session");

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

    const sessionLink = findNavLink("Session");
    expect(sessionLink).toBeDefined();

    await act(async () => {
      sessionLink?.click();
    });
    
    startButton = findButton("Start session");
    const stopButton = findButton("Stop session");

    expect(startButton).toBeUndefined();
    expect(stopButton).toBeDefined();
  });

  it("keep session camera idle when navigating away", async () => {
    let startButton = findButton("Start session");

    await act(async () => {
      startButton?.click();
    });
    expect(sessionBridgeMock.state).toBe("live");

    let stopButton = findButton("Stop session");

    await act(async () => {
      stopButton?.click();
    });
    expect(sessionBridgeMock.state).toBe("idle");

    const profilesLink = findNavLink("Profiles");
    expect(profilesLink).toBeDefined();

    await act(async () => {
      profilesLink?.click();
    });
    expect(sessionBridgeMock.state).toBe("idle");

    const sessionLink = findNavLink("Session");
    expect(sessionLink).toBeDefined();

    await act(async () => {
      sessionLink?.click();
    });

    startButton = findButton("Start session");
    stopButton = findButton("Stop session");

    expect(startButton).toBeDefined();
    expect(stopButton).toBeUndefined();
  });

  it("show detected gesture", async () => {
    const startButton = findButton("Start session");

    await act(async () => {
      startButton?.click();
    });

    const gestureEvent = {
      gestureId: "gesture-1",
      name: "Wave",
      score: 0.9,
      matched: true,
      hasTemplates: true,
      key: "Space",
      keyAction: "press" as const
    };

    await act(async () => sessionBridgeMock.gestureListener?.(gestureEvent));
    expect(container.textContent).toContain("Recognising Wave");

    await act(async () => sessionBridgeMock.gestureListener?.(gestureEvent));
    expect(container.textContent).toContain("Wave → Space held");

    await act(async () => {
      sessionBridgeMock.gestureListener?.({
        gestureId: "gesture-1",
        name: "Wave",
        score: 0,
        matched: false,
        hasTemplates: true,
        key: "Space",
        keyAction: "release"
      });
    });

    expect(container.textContent).not.toContain("Recognising Wave");
    expect(container.textContent).toContain("Waiting for a movement");
  });
});
