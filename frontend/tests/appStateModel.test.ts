import { describe, expect, it } from "vitest";

import {
  bindingsForPatient,
  initialState,
  parseStoredState,
  readinessFor,
  resolveBindings,
  sameBindings,
  withSelectedPatientBindings,
} from "@/state/appStateModel";

describe("app state model", () => {
  it("falls back to a valid initial state for corrupt browser data", () => {
    const state = parseStoredState("{not-json");

    expect(state.settings.poseModel).toBe("lite");
    expect(state.gestures.length).toBeGreaterThan(0);
    expect(state.bindings.length).toBeGreaterThan(0);
  });

  it("returns isolated initial state objects", () => {
    const first = initialState();
    const second = initialState();

    first.bindings[0].key = "Changed";
    first.patients[0].keyBindings.extra = "X";

    expect(second.bindings[0].key).not.toBe("Changed");
    expect(second.patients[0].keyBindings.extra).toBeUndefined();
  });

  it("resolves missing gestures and replaces invalid thresholds", () => {
    const state = initialState();
    state.settings.matchThreshold = 68;
    state.bindings = [
      {
        gestureId: "missing-gesture",
        key: "Space",
        matchThreshold: Number.NaN,
      },
    ];

    const [binding] = resolveBindings(state);

    expect(binding.gesture.name).toBe("Missing movement (missing-gesture)");
    expect(binding.matchThreshold).toBe(68);
    expect(readinessFor([binding])).toEqual({
      total: 1,
      recorded: 0,
      pending: [binding.gesture],
      isReady: false,
    });
  });

  it("compares bindings independently of order", () => {
    const left = [
      { gestureId: "a", key: "A", matchThreshold: 70 },
      { gestureId: "b", key: "B" },
    ];
    const right = [left[1], left[0]];

    expect(sameBindings(left, right, 75)).toBe(true);
    expect(sameBindings(left, [{ ...right[0], key: "C" }, right[1]], 75)).toBe(
      false,
    );
  });

  it("keeps selected patient bindings and thresholds in sync", () => {
    const state = initialState();
    const selected = state.patients[0];
    state.selectedPatientId = selected.patientId;
    const bindings = [
      { gestureId: "elbow", key: "E", matchThreshold: 150 },
      { gestureId: "squat", key: "S" },
    ];

    const updated = withSelectedPatientBindings(
      state,
      bindings,
      "2026-08-08T00:00:00.000Z",
    );
    const patient = updated.patients.find(
      (item) => item.patientId === selected.patientId,
    );

    expect(patient?.keyBindings).toEqual({ elbow: "E", squat: "S" });
    expect(patient?.matchThresholds).toEqual({ elbow: 100, squat: 75 });
    expect(patient?.updatedAt).toBe("2026-08-08T00:00:00.000Z");
    expect(bindingsForPatient(patient, 75)).toEqual([
      { gestureId: "elbow", key: "E", matchThreshold: 100 },
      { gestureId: "squat", key: "S", matchThreshold: 75 },
    ]);
  });
});
