// @vitest-environment jsdom

import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AppStateProvider from "@/state/AppStateProvider";
import {
  useAppState,
  type AppStateValue,
} from "@/state/appStateContext";
import {
  initialState,
  STORAGE_KEY,
} from "@/state/appStateModel";
import type { DesktopState } from "@/types/desktopState";

const bridgeMocks = vi.hoisted(() => ({
  getState: vi.fn(),
  saveState: vi.fn(),
  deleteGesture: vi.fn(),
  selectPatient: vi.fn(),
  createProfile: vi.fn(),
  deleteProfile: vi.fn(),
  clearPatientSelection: vi.fn(),
}));

vi.mock("@/services/desktopStateBridge", () => ({
  desktopStateBridge: bridgeMocks,
}));

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

let stateValue: AppStateValue | null = null;

const StateHarness = () => {
  stateValue = useAppState();
  return <output data-testid="ready">ready</output>;
};

const current = () => {
  if (!stateValue) throw new Error("State harness is not ready");
  return stateValue;
};

const seededState = (): DesktopState => {
  const state = initialState();
  const gestures = [
    {
      gestureId: "ges-right-arm-raise",
      name: "Right Arm Raise",
      calibratedAt: "2026-08-08T00:00:00.000Z",
      matchScore: 87,
    },
    {
      gestureId: "ges-squat",
      name: "Squat",
      calibratedAt: "2026-08-08T00:00:00.000Z",
      matchScore: 82,
    },
    {
      gestureId: "ges-jump",
      name: "Jump",
      calibratedAt: "2026-08-08T00:00:00.000Z",
      matchScore: 80,
    },
  ];
  const bindings = [
    {
      gestureId: "ges-right-arm-raise",
      key: "ArrowUp",
      matchThreshold: 75,
    },
    {
      gestureId: "ges-squat",
      key: "ArrowDown",
      matchThreshold: 75,
    },
  ];

  return {
    ...state,
    gestures,
    bindings,
    presets: [
      {
        presetId: "preset-default",
        name: "Default",
        bindings,
      },
    ],
    activePresetId: "preset-default",
    selectedPatientId: "patient-a",
    patients: [
      {
        schemaVersion: 2,
        patientId: "patient-a",
        patientName: "Patient A",
        notes: "",
        updatedAt: "2026-08-08T00:00:00.000Z",
        keyBindings: {
          "ges-right-arm-raise": "ArrowUp",
          "ges-squat": "ArrowDown",
        },
        matchThresholds: {
          "ges-right-arm-raise": 75,
          "ges-squat": 75,
        },
      },
    ],
  };
};

describe("AppStateProvider", () => {
  let container: HTMLDivElement;
  let root: Root;
  let storedValues: Map<string, string>;
  let setItem: ReturnType<typeof vi.fn>;

  const renderProvider = async () => {
    await act(async () => {
      root.render(
        <AppStateProvider>
          <StateHarness />
        </AppStateProvider>,
      );
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(container.querySelector('[data-testid="ready"]')).not.toBeNull();
  };

  beforeEach(() => {
    stateValue = null;
    storedValues = new Map();
    setItem = vi.fn((key: string, value: string) =>
      storedValues.set(key, value),
    );
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: {
        clear: () => storedValues.clear(),
        getItem: (key: string) => storedValues.get(key) ?? null,
        setItem,
      },
    });
    storedValues.set(STORAGE_KEY, JSON.stringify(seededState()));
    bridgeMocks.getState.mockRejectedValue(new Error("Browser preview"));
    bridgeMocks.saveState.mockResolvedValue(initialState());
    container = document.createElement("div");
    document.body.append(container);
    root = createRoot(container);
  });

  afterEach(() => {
    act(() => root.unmount());
    container.remove();
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it("makes a recorded browser gesture ready when bound", async () => {
    const state = initialState();
    state.gestures = [
      {
        gestureId: "ges-jump",
        name: "Jump",
        calibratedAt: "2026-08-08T00:00:00.000Z",
        matchScore: null,
      },
    ];
    storedValues.set(STORAGE_KEY, JSON.stringify(state));

    await renderProvider();

    expect(current().bindings).toHaveLength(0);
    expect(current().readiness.isReady).toBe(false);

    act(() => current().bindGesture("ges-jump", "Space"));

    expect(current().bindings).toHaveLength(1);
    expect(current().readiness.isReady).toBe(true);
  });

  it("loads browser state and tolerates local storage quota errors", async () => {
    const saved = seededState();
    saved.settings.poseModel = "full";
    storedValues.set(STORAGE_KEY, JSON.stringify(saved));
    setItem.mockImplementation(() => {
      throw new DOMException("Quota exceeded", "QuotaExceededError");
    });

    await renderProvider();
    expect(current().settings.poseModel).toBe("full");

    expect(() => {
      act(() => current().updateSetting("smoothing", 4));
    }).not.toThrow();
  });

  it("tolerates ordinary local storage write errors", async () => {
    await renderProvider();
    setItem.mockImplementation(() => {
      throw new Error("storage write failed");
    });

    expect(() => {
      act(() => current().updateSetting("cooldown", 1));
    }).not.toThrow();
  });

  it("creates, selects, clears, and deletes browser patient profiles", async () => {
    await renderProvider();

    let createdId = "";
    await act(async () => {
      expect(await current().createPatient("   ")).toBeNull();
      const created = await current().createPatient("  Taylor  ", " notes ");
      createdId = created?.patientId ?? "";
    });
    expect(current().selectedPatient?.patientName).toBe("Taylor");
    expect(current().selectedPatient?.notes).toBe("notes");

    await act(async () => current().clearPatientSelection());
    expect(current().selectedPatient).toBeNull();

    await act(async () => current().selectPatient(createdId));
    expect(current().selectedPatient?.patientId).toBe(createdId);

    await act(async () => current().deletePatient(createdId));
    expect(
      current().patients.some((item) => item.patientId === createdId),
    ).toBe(false);
    expect(current().selectedPatient).toBeNull();
  });

  it("adds and removes bindings for the selected browser patient", async () => {
    await renderProvider();
    await act(async () => current().selectPatient("patient-a"));

    act(() => current().setPatientBinding("patient-a", "ges-jump", "Space"));
    expect(current().selectedPatient?.keyBindings["ges-jump"]).toBe("Space");
    expect(
      current().bindings.find((item) => item.gesture.gestureId === "ges-jump")
        ?.key,
    ).toBe("Space");

    act(() => current().removePatientBinding("patient-a", "ges-jump"));
    expect(current().selectedPatient?.keyBindings["ges-jump"]).toBeUndefined();
    expect(
      current().bindings.some((item) => item.gesture.gestureId === "ges-jump"),
    ).toBe(false);
  });

  it("adds, renames, records, binds, rebinds, and removes gestures", async () => {
    await renderProvider();

    let temporaryId = "";
    act(() => {
      temporaryId = current().addGesture("Temporary wave");
      current().renameGesture(temporaryId, "Wave");
      current().bindGesture(temporaryId, "A");
    });
    expect(
      current().bindings.find((item) => item.gesture.gestureId === temporaryId)
        ?.key,
    ).toBe("A");

    act(() => current().rebindKey(temporaryId, "B"));
    expect(
      current().bindings.find((item) => item.gesture.gestureId === temporaryId)
        ?.key,
    ).toBe("B");

    act(() =>
      current().completeRecording(temporaryId, {
        gestureId: "recorded-wave",
        name: "Recorded wave",
        repCount: 3,
      }),
    );
    expect(
      current().gestures.some((item) => item.gestureId === temporaryId),
    ).toBe(false);
    expect(
      current().bindings.some(
        (item) => item.gesture.gestureId === "recorded-wave",
      ),
    ).toBe(true);

    act(() => current().unbindGesture("recorded-wave"));
    expect(current().undoLabel).toContain("Removed");
    expect(
      current().bindings.some(
        (item) => item.gesture.gestureId === "recorded-wave",
      ),
    ).toBe(false);

    act(() => current().undo());
    expect(
      current().bindings.some(
        (item) => item.gesture.gestureId === "recorded-wave",
      ),
    ).toBe(true);
  });

  it("clamps binding thresholds at both limits", async () => {
    await renderProvider();

    act(() => current().setBindingThreshold("ges-squat", -1));
    expect(
      current().bindings.find((item) => item.gesture.gestureId === "ges-squat")
        ?.matchThreshold,
    ).toBe(0);

    act(() => current().setBindingThreshold("ges-squat", 101));
    expect(
      current().bindings.find((item) => item.gesture.gestureId === "ges-squat")
        ?.matchThreshold,
    ).toBe(100);
  });

  it("creates, overwrites, loads, deletes, and undoes presets", async () => {
    await renderProvider();

    act(() => current().savePreset("Custom"));
    const presetId = current().activePreset?.presetId ?? "";
    const presetCount = current().presets.length;

    act(() => current().rebindKey("ges-squat", "S"));
    expect(current().hasUnsavedChanges).toBe(true);

    act(() => current().savePreset("custom"));
    expect(current().presets).toHaveLength(presetCount);
    expect(
      current().activePreset?.bindings.find(
        (binding) => binding.gestureId === "ges-squat",
      )?.key,
    ).toBe("S");

    act(() => current().rebindKey("ges-squat", "X"));
    act(() => current().loadPreset(presetId));
    expect(
      current().bindings.find((item) => item.gesture.gestureId === "ges-squat")
        ?.key,
    ).toBe("S");

    act(() => current().undo());
    expect(
      current().bindings.find((item) => item.gesture.gestureId === "ges-squat")
        ?.key,
    ).toBe("X");

    act(() => current().deletePreset(presetId));
    expect(current().presets.some((item) => item.presetId === presetId)).toBe(
      false,
    );

    act(() => current().undo());
    expect(current().presets.some((item) => item.presetId === presetId)).toBe(
      true,
    );
  });

  it("removes deleted gestures from bindings, patients, and presets", async () => {
    await renderProvider();
    act(() => current().deleteGesture("ges-squat"));

    expect(
      current().gestures.some((item) => item.gestureId === "ges-squat"),
    ).toBe(false);
    expect(
      current().bindings.some((item) => item.gesture.gestureId === "ges-squat"),
    ).toBe(false);
    expect(
      current().patients.every(
        (patient) => patient.keyBindings["ges-squat"] === undefined,
      ),
    ).toBe(true);
    expect(
      current().presets.every((preset) =>
        preset.bindings.every((binding) => binding.gestureId !== "ges-squat"),
      ),
    ).toBe(true);
  });

  it("loads desktop state and debounces saves using the latest state", async () => {
    vi.useFakeTimers();
    const desktopState = seededState();
    desktopState.settings.poseModel = "heavy";
    bridgeMocks.getState.mockResolvedValue(desktopState);

    await renderProvider();
    expect(current().settings.poseModel).toBe("heavy");
    bridgeMocks.saveState.mockClear();

    act(() => current().updateSetting("smoothing", 3));
    act(() => vi.advanceTimersByTime(50));
    act(() => current().updateSetting("smoothing", 5));
    act(() => vi.advanceTimersByTime(99));
    expect(bridgeMocks.saveState).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(1));
    expect(bridgeMocks.saveState).toHaveBeenCalledTimes(1);
    expect(bridgeMocks.saveState).toHaveBeenCalledWith(
      expect.objectContaining({
        settings: expect.objectContaining({ smoothing: 5 }),
      }),
    );
  });

  it("delegates desktop patient, refresh, and gesture operations", async () => {
    const loaded = seededState();
    const selected = {
      ...loaded,
      selectedPatientId: "patient-a",
      bindings: [
        { gestureId: "ges-right-arm-raise", key: "W", matchThreshold: 80 },
      ],
    };
    const createdPatient = {
      schemaVersion: 2 as const,
      patientId: "patient-new",
      patientName: "Taylor",
      notes: "notes",
      updatedAt: "2026-08-09T00:00:00.000Z",
      keyBindings: {},
      matchThresholds: {},
    };
    const created = {
      ...selected,
      patients: [...selected.patients, createdPatient],
      selectedPatientId: createdPatient.patientId,
      bindings: [],
    };
    const cleared = {
      ...created,
      selectedPatientId: null,
      bindings: [],
    };
    const deleted = {
      ...cleared,
      patients: cleared.patients.filter(
        (patient) => patient.patientId !== createdPatient.patientId,
      ),
    };
    const refreshed = {
      ...deleted,
      settings: { ...deleted.settings, poseModel: "full" as const },
    };
    const withoutSquat = {
      ...refreshed,
      gestures: refreshed.gestures.filter(
        (gesture) => gesture.gestureId !== "ges-squat",
      ),
      bindings: refreshed.bindings.filter(
        (binding) => binding.gestureId !== "ges-squat",
      ),
    };

    bridgeMocks.getState.mockResolvedValue(loaded);
    bridgeMocks.selectPatient.mockResolvedValue(selected);
    bridgeMocks.createProfile.mockResolvedValue(created);
    bridgeMocks.clearPatientSelection.mockResolvedValue(cleared);
    bridgeMocks.deleteProfile.mockResolvedValue(deleted);
    bridgeMocks.deleteGesture.mockResolvedValue(withoutSquat);

    await renderProvider();

    await act(async () => current().selectPatient("patient-a"));
    expect(bridgeMocks.selectPatient).toHaveBeenCalledWith("patient-a");
    expect(current().selectedPatient?.patientId).toBe("patient-a");

    let returnedPatientId = "";
    await act(async () => {
      returnedPatientId =
        (await current().createPatient(" Taylor ", "notes"))?.patientId ?? "";
    });
    expect(bridgeMocks.createProfile).toHaveBeenCalledWith("Taylor", "notes");
    expect(returnedPatientId).toBe("patient-new");

    await act(async () => current().clearPatientSelection());
    expect(bridgeMocks.clearPatientSelection).toHaveBeenCalledOnce();
    expect(current().selectedPatient).toBeNull();

    await act(async () => current().deletePatient("patient-new"));
    expect(bridgeMocks.deleteProfile).toHaveBeenCalledWith("patient-new");
    expect(
      current().patients.some((patient) => patient.patientId === "patient-new"),
    ).toBe(false);

    bridgeMocks.getState.mockResolvedValue(refreshed);
    await act(async () => current().refreshState());
    expect(current().settings.poseModel).toBe("full");

    await act(async () => {
      current().deleteGesture("ges-squat");
      await Promise.resolve();
    });
    expect(bridgeMocks.deleteGesture).toHaveBeenCalledWith("ges-squat");
    expect(
      current().gestures.some((gesture) => gesture.gestureId === "ges-squat"),
    ).toBe(false);
  });

  it("ignores a delayed desktop load after the provider unmounts", async () => {
    let resolveState:
      | ((state: ReturnType<typeof initialState>) => void)
      | null = null;
    bridgeMocks.getState.mockReturnValue(
      new Promise((resolve) => {
        resolveState = resolve;
      }),
    );

    await act(async () => {
      root.render(
        <AppStateProvider>
          <StateHarness />
        </AppStateProvider>,
      );
      await Promise.resolve();
    });

    act(() => root.render(null));
    await act(async () => {
      resolveState?.(seededState());
      await Promise.resolve();
    });
    expect(bridgeMocks.saveState).not.toHaveBeenCalled();
  });

  it("removes deleted gestures from bindings, patients, and presets", async () => {
    await renderProvider();
    act(() => current().deleteGesture("ges-squat"));

    expect(
      current().gestures.some((item) => item.gestureId === "ges-squat"),
    ).toBe(false);
    expect(
      current().bindings.some((item) => item.gesture.gestureId === "ges-squat"),
    ).toBe(false);
    expect(
      current().patients.every(
        (patient) => patient.keyBindings["ges-squat"] === undefined,
      ),
    ).toBe(true);
    expect(
      current().presets.every((preset) =>
        preset.bindings.every((binding) => binding.gestureId !== "ges-squat"),
      ),
    ).toBe(true);
  });

  it("loads desktop state and debounces saves using the latest state", async () => {
    vi.useFakeTimers();
    const desktopState = initialState();
    desktopState.settings.poseModel = "heavy";
    bridgeMocks.getState.mockResolvedValue(desktopState);

    await renderProvider();
    expect(current().settings.poseModel).toBe("heavy");
    bridgeMocks.saveState.mockClear();

    act(() => current().updateSetting("smoothing", 3));
    act(() => vi.advanceTimersByTime(50));
    act(() => current().updateSetting("smoothing", 5));
    act(() => vi.advanceTimersByTime(99));
    expect(bridgeMocks.saveState).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));
    expect(bridgeMocks.saveState).toHaveBeenCalledTimes(1);
    expect(bridgeMocks.saveState).toHaveBeenCalledWith(
      expect.objectContaining({
        settings: expect.objectContaining({ smoothing: 5 }),
      }),
    );
  });

  it("delegates desktop patient, refresh, and gesture operations", async () => {
    const loaded = initialState();
    const selected = {
      ...loaded,
      selectedPatientId: "patient-a",
      bindings: [
        { gestureId: "ges-right-arm-raise", key: "W", matchThreshold: 80 },
      ],
    };
    const createdPatient = {
      schemaVersion: 2 as const,
      patientId: "patient-new",
      patientName: "Taylor",
      notes: "notes",
      updatedAt: "2026-08-09T00:00:00.000Z",
      keyBindings: {},
      matchThresholds: {},
    };
    const created = {
      ...selected,
      patients: [...selected.patients, createdPatient],
      selectedPatientId: createdPatient.patientId,
      bindings: [],
    };
    const cleared = {
      ...created,
      selectedPatientId: null,
      bindings: [],
    };
    const deleted = {
      ...cleared,
      patients: cleared.patients.filter(
        (patient) => patient.patientId !== createdPatient.patientId,
      ),
    };
    const refreshed = {
      ...deleted,
      settings: { ...deleted.settings, poseModel: "full" as const },
    };
    const withoutSquat = {
      ...refreshed,
      gestures: refreshed.gestures.filter(
        (gesture) => gesture.gestureId !== "ges-squat",
      ),
      bindings: refreshed.bindings.filter(
        (binding) => binding.gestureId !== "ges-squat",
      ),
    };
    bridgeMocks.getState.mockResolvedValue(loaded);
    bridgeMocks.selectPatient.mockResolvedValue(selected);
    bridgeMocks.createProfile.mockResolvedValue(created);
    bridgeMocks.clearPatientSelection.mockResolvedValue(cleared);
    bridgeMocks.deleteProfile.mockResolvedValue(deleted);
    bridgeMocks.deleteGesture.mockResolvedValue(withoutSquat);

    await renderProvider();

    await act(async () => current().selectPatient("patient-a"));
    expect(bridgeMocks.selectPatient).toHaveBeenCalledWith("patient-a");
    expect(current().selectedPatient?.patientId).toBe("patient-a");

    let returnedPatientId = "";
    await act(async () => {
      returnedPatientId =
        (await current().createPatient(" Taylor ", "notes"))?.patientId ?? "";
    });
    expect(bridgeMocks.createProfile).toHaveBeenCalledWith("Taylor", "notes");
    expect(returnedPatientId).toBe("patient-new");

    await act(async () => current().clearPatientSelection());
    expect(bridgeMocks.clearPatientSelection).toHaveBeenCalledOnce();
    expect(current().selectedPatient).toBeNull();

    await act(async () => current().deletePatient("patient-new"));
    expect(bridgeMocks.deleteProfile).toHaveBeenCalledWith("patient-new");
    expect(
      current().patients.some((patient) => patient.patientId === "patient-new"),
    ).toBe(false);

    bridgeMocks.getState.mockResolvedValue(refreshed);
    await act(async () => current().refreshState());
    expect(current().settings.poseModel).toBe("full");

    await act(async () => {
      current().deleteGesture("ges-squat");
      await Promise.resolve();
    });
    expect(bridgeMocks.deleteGesture).toHaveBeenCalledWith("ges-squat");
    expect(
      current().gestures.some((gesture) => gesture.gestureId === "ges-squat"),
    ).toBe(false);
  });

  it("ignores a delayed desktop load after the provider unmounts", async () => {
    let resolveState:
      | ((state: ReturnType<typeof initialState>) => void)
      | null = null;
    bridgeMocks.getState.mockReturnValue(
      new Promise((resolve) => {
        resolveState = resolve;
      }),
    );
    await act(async () => {
      root.render(
        <AppStateProvider>
          <StateHarness />
        </AppStateProvider>,
      );
      await Promise.resolve();
    });
    act(() => root.render(null));
    await act(async () => {
      resolveState?.(initialState());
      await Promise.resolve();
    });
    expect(bridgeMocks.saveState).not.toHaveBeenCalled();
  });
});
