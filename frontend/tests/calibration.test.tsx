import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import Calibrate from "../src/pages/Calibrate";

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

const routerMocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  searchParams: new URLSearchParams(),
}));

const appStateMocks = vi.hoisted(() => ({
  gestures: [] as Array<{ gestureId: string; name: string }>,
  addGesture: vi.fn(),
  completeRecording: vi.fn(),
}));

const bridgeListeners = vi.hoisted(() => {
  let statusListener:
    | ((event: { state: string; message?: string }) => void)
    | null = null;
  let updateListener:
    | ((
        event: {
          repCount: number;
          capturing: boolean;
          phase: "idle" | "countdown" | "waiting" | "recording" | "captured";
          countdownRemaining: number;
        },
      ) => void)
    | null = null;

  return {
    setStatusListener: (listener: typeof statusListener) => {
      statusListener = listener;
    },
    setUpdateListener: (listener: typeof updateListener) => {
      updateListener = listener;
    },
    emitStatus(event: { state: string; message?: string }) {
      statusListener?.(event);
    },
    emitUpdate(event: {
      repCount: number;
      capturing: boolean;
      phase: "idle" | "countdown" | "waiting" | "recording" | "captured";
      countdownRemaining: number;
    }) {
      updateListener?.(event);
    },
    reset() {
      statusListener = null;
      updateListener = null;
    },
  };
});

const bridgeMocks = vi.hoisted(() => ({
  startCalibrate: vi.fn(),
  stopCalibrate: vi.fn(),
  startCalibration: vi.fn(),
  cancelRep: vi.fn(),
  startRep: vi.fn(),
  resetRep: vi.fn(),
  saveRep: vi.fn(),
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => routerMocks.navigate,
  useSearchParams: () => [routerMocks.searchParams] as const,
}));

vi.mock("@/hooks/useActiveProfile", () => ({
  default: () => ({
    activeProfile: { patientId: "patient-1", patientName: "Alex" },
  }),
}));

vi.mock("@/state/appStateContext", () => ({
  useAppState: () => ({
    gestures: appStateMocks.gestures,
    addGesture: appStateMocks.addGesture,
    completeRecording: appStateMocks.completeRecording,
  }),
}));

vi.mock("@/hooks/useDesktopCameraPreview", () => ({
  default: () => ({
    previewAspectRatio: 4 / 3,
    previewViewportRef: { current: null },
    elapsed: 0,
    setElapsed: vi.fn(),
  }),
}));

vi.mock("@/services/calibrateBridge", () => ({
  default: {
    startCalibrate: bridgeMocks.startCalibrate,
    stopCalibrate: bridgeMocks.stopCalibrate,
    startCalibration: bridgeMocks.startCalibration,
    cancelRep: bridgeMocks.cancelRep,
    startRep: bridgeMocks.startRep,
    resetRep: bridgeMocks.resetRep,
    saveRep: bridgeMocks.saveRep,
    onCalibrateStatus: (listener: (event: { state: string }) => void) => {
      bridgeListeners.setStatusListener(listener);
      return () => bridgeListeners.setStatusListener(null);
    },
    onCalibrationUpdated: (
      listener: (event: {
        repCount: number;
        capturing: boolean;
        phase: "idle" | "countdown" | "waiting" | "recording" | "captured";
        countdownRemaining: number;
      }) => void,
    ) => {
      bridgeListeners.setUpdateListener(listener);
      return () => bridgeListeners.setUpdateListener(null);
    },
  },
}));

const flushAsync = async () => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
};

describe("Calibration flow", () => {
  let container: HTMLDivElement;
  let root: Root;

  const setInputValue = (
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

  const buttonByLabel = (label: string) =>
    Array.from(document.querySelectorAll("button")).find(
      (button) => button.textContent?.trim() === label,
    ) as HTMLButtonElement | undefined;

  const beginCalibrationRecordingStep = async () => {
    const nameInput = document.getElementById(
      "gesture-name",
    ) as HTMLInputElement | null;
    if (!(nameInput instanceof HTMLInputElement)) {
      throw new Error("Movement name input not found.");
    }

    act(() => {
      setInputValue(nameInput, "  Wave  ");
    });

    const nextButton = buttonByLabel("Next");
    if (!nextButton) {
      throw new Error("Next button not found.");
    }

    act(() => nextButton.click());
    await flushAsync();
  };

  const emitStatus = (state: string, message?: string) => {
    act(() => {
      bridgeListeners.emitStatus({ state, message });
    });
  };

  const emitCalibrationUpdate = (event: {
    repCount: number;
    capturing: boolean;
    phase: "idle" | "countdown" | "waiting" | "recording" | "captured";
    countdownRemaining: number;
  }) => {
    act(() => {
      bridgeListeners.emitUpdate(event);
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
    bridgeListeners.reset();
    routerMocks.searchParams = new URLSearchParams();
    appStateMocks.gestures = [];
    appStateMocks.addGesture.mockReturnValue("ges-wave");

    bridgeMocks.startCalibrate.mockResolvedValue(undefined);
    bridgeMocks.stopCalibrate.mockResolvedValue(undefined);
    bridgeMocks.startCalibration.mockResolvedValue(undefined);
    bridgeMocks.startRep.mockResolvedValue(undefined);
    bridgeMocks.cancelRep.mockResolvedValue(undefined);
    bridgeMocks.resetRep.mockResolvedValue(undefined);
    bridgeMocks.saveRep.mockResolvedValue({
      gestureId: "ges-wave",
      name: "Wave",
      repCount: 1,
    });

    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);

    act(() => {
      root.render(<Calibrate />);
    });
  });

  afterEach(() => {
    if (root) {
      act(() => {
        root.unmount();
      });
    }
    container?.remove();
  });

  it("transitions through countdown, waiting, recording, and captured states", async () => {
    await beginCalibrationRecordingStep();

    emitStatus("live");

    emitCalibrationUpdate({
      repCount: 0,
      capturing: true,
      phase: "countdown",
      countdownRemaining: 3,
    });
    expect(document.body.textContent).toContain("Get ready — 3");

    emitCalibrationUpdate({
      repCount: 0,
      capturing: false,
      phase: "waiting",
      countdownRemaining: 0,
    });
    expect(document.body.textContent).toContain("Ready — move now");

    emitCalibrationUpdate({
      repCount: 0,
      capturing: true,
      phase: "recording",
      countdownRemaining: 2,
    });
    expect(document.body.textContent).toContain("Movement detected — 2");

    emitCalibrationUpdate({
      repCount: 1,
      capturing: false,
      phase: "captured",
      countdownRemaining: 0,
    });
    expect(document.body.textContent).toContain("Movement captured");
  });

  it("cancels an in-progress recording when cancel is pressed", async () => {
    await beginCalibrationRecordingStep();

    emitStatus("live");
    emitCalibrationUpdate({
      repCount: 0,
      capturing: true,
      phase: "recording",
      countdownRemaining: 2,
    });

    const cancelButton = buttonByLabel("Cancel recording");
    expect(cancelButton).toBeDefined();
    act(() => cancelButton?.click());
    await flushAsync();

    expect(bridgeMocks.cancelRep).toHaveBeenCalledTimes(1);
  });

  it("manually stops the calibration runtime on unmount", async () => {
    await beginCalibrationRecordingStep();

    expect(bridgeMocks.startCalibrate).toHaveBeenCalledTimes(1);
    expect(bridgeMocks.startCalibration).toHaveBeenCalledTimes(1);

    act(() => {
      root.unmount();
    });

    expect(bridgeMocks.stopCalibrate).toHaveBeenCalledTimes(1);
  });

  it("shows save failure and stays in review when saving fails", async () => {
    bridgeMocks.saveRep.mockRejectedValueOnce(
      new Error("Unable to save this movement."),
    );

    await beginCalibrationRecordingStep();
    emitStatus("live");
    emitCalibrationUpdate({
      repCount: 1,
      capturing: false,
      phase: "captured",
      countdownRemaining: 0,
    });

    const reviewButton = buttonByLabel("Review");
    expect(reviewButton).toBeDefined();
    act(() => reviewButton?.click());

    const saveButton = buttonByLabel("Save to library");
    expect(saveButton).toBeDefined();
    act(() => saveButton?.click());
    await flushAsync();

    expect(bridgeMocks.saveRep).toHaveBeenCalledWith("Wave", "ges-wave");
    expect(document.body.textContent).toContain("Unable to save this movement.");
    expect(routerMocks.navigate).not.toHaveBeenCalled();
    expect(appStateMocks.completeRecording).not.toHaveBeenCalled();
  });

  it("supports re-recording after capture review", async () => {
    await beginCalibrationRecordingStep();
    emitStatus("live");
    emitCalibrationUpdate({
      repCount: 2,
      capturing: false,
      phase: "captured",
      countdownRemaining: 0,
    });

    const reviewButton = buttonByLabel("Review");
    expect(reviewButton).toBeDefined();
    act(() => reviewButton?.click());

    const recordAgainButton = buttonByLabel("Record again");
    expect(recordAgainButton).toBeDefined();
    act(() => recordAgainButton?.click());
    await flushAsync();

    expect(bridgeMocks.resetRep).toHaveBeenCalledTimes(1);
    expect(document.body.textContent).toContain("Ready to record");
    expect(document.body.textContent).toContain("0 captured");
  });
});