import { describe, expect, it } from "vitest";

import {
  bindingsForPatient,
  clampPercentage,
  initialState,
  parseStoredState,
  readinessFor,
  resolveBindings,
  sameBindings,
  withSelectedPatientBindings,
} from "@/state/appStateModel";

describe("app state model", () => {
  it("loads valid saved browser state", () => {
    const saved = initialState();
    saved.settings.poseModel = "heavy";
    saved.selectedPatientId = "patient-a";

    expect(parseStoredState(JSON.stringify(saved))).toEqual(saved);
  });

  it("fills optional fields in a partial saved browser state", () => {
    const state = parseStoredState(
      JSON.stringify({
        gestures: [],
        bindings: [],
        settings: { poseModel: "full" },
      }),
    );

    expect(state.presets).toEqual([]);
    expect(state.selectedPatientId).toBeNull();
    expect(state.activePresetId).toBeNull();
    expect(state.patients).toEqual([]);
    expect(state.settings).toEqual(
      expect.objectContaining({ poseModel: "full", matchThreshold: 75 }),
    );
  });

  it("uses defaults for missing and structurally invalid browser state", () => {
    expect(parseStoredState(null)).toEqual(initialState());
    expect(parseStoredState(JSON.stringify({ gestures: "invalid" }))).toEqual(
      initialState(),
    );
  });

  it("normalizes malformed nested browser state at the storage boundary", () => {
    const state = parseStoredState(
      JSON.stringify({
        gestures: [
          {
            gestureId: "wave",
            name: "Wave",
            calibratedAt: 42,
            matchScore: "high",
          },
          { gestureId: "", name: "Invalid" },
          null,
        ],
        bindings: [
          { gestureId: "wave", key: "W", matchThreshold: 140 },
          { gestureId: "wave", key: null },
        ],
        presets: [
          {
            presetId: "default",
            name: "Default",
            bindings: [{ gestureId: "wave", key: "W" }, null],
          },
          { presetId: "broken", name: "Broken", bindings: null },
        ],
        patients: [
          {
            schemaVersion: 2,
            patientId: "patient-a",
            patientName: "Patient A",
            notes: "",
            updatedAt: "2026-08-08T00:00:00.000Z",
            keyBindings: { wave: "W", broken: null },
            matchThresholds: { wave: -10, broken: "high" },
          },
          { schemaVersion: 1, patientId: "legacy" },
        ],
        settings: {
          matchThreshold: 150,
          cooldown: -2,
          smoothing: 3.8,
          poseModel: "unsupported",
        },
      }),
    );

    expect(state.gestures).toEqual([
      {
        gestureId: "wave",
        name: "Wave",
        calibratedAt: null,
        matchScore: null,
      },
    ]);
    expect(state.bindings).toEqual([
      { gestureId: "wave", key: "W", matchThreshold: 100 },
    ]);
    expect(state.presets).toEqual([
      {
        presetId: "default",
        name: "Default",
        bindings: [{ gestureId: "wave", key: "W" }],
      },
    ]);
    expect(state.patients).toHaveLength(1);
    expect(state.patients[0].keyBindings).toEqual({ wave: "W" });
    expect(state.patients[0].matchThresholds).toEqual({ wave: 0 });
    expect(state.settings).toEqual({
      matchThreshold: 100,
      cooldown: 0,
      smoothing: 3,
      poseModel: "lite",
    });
  });

  it("falls back to a valid initial state for corrupt browser data", () => {
    const state = parseStoredState("{not-json");

    expect(state.settings.poseModel).toBe("lite");
    expect(state.gestures).toEqual([]);
    expect(state.bindings).toEqual([]);
  });

  it("clamps gesture thresholds to their allowed range", () => {
    expect(clampPercentage(-10, 75)).toBe(0);
    expect(clampPercentage(140, 75)).toBe(100);
    expect(clampPercentage("not-a-number", 75)).toBe(75);
  });

  it("returns isolated initial state objects", () => {
    const first = initialState();
    const second = initialState();

    first.bindings.push({ gestureId: "gesture", key: "Changed" });
    first.patients.push({
      schemaVersion: 2,
      patientId: "patient",
      patientName: "Patient",
      notes: "",
      updatedAt: "2026-08-08T00:00:00.000Z",
      keyBindings: { extra: "X" },
      matchThresholds: {},
    });

    expect(second.bindings).toEqual([]);
    expect(second.patients).toEqual([]);
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
    const selected = {
      schemaVersion: 2,
      patientId: "patient",
      patientName: "Patient",
      notes: "",
      updatedAt: "2026-08-08T00:00:00.000Z",
      keyBindings: {},
      matchThresholds: {},
    };
    state.patients = [selected];
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
