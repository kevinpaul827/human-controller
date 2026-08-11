import { expect, test } from "@playwright/test";
import {
  createAppState,
  createBinding,
  createGesture,
  createPatient,
  openWithAppState,
  readAppState,
  waitForAppState,
} from "./helpers";
import type { AppState, BindingState, GestureState } from "./helpers";

const PATIENT_ID = "patient-session";
const RECORDED_AT = "2026-08-01T10:00:00.000Z";

const createSelectedState = ({
  gestures,
  bindings,
  presets = [],
  activePresetId = null,
}: {
  gestures: GestureState[];
  bindings: BindingState[];
  presets?: AppState["presets"];
  activePresetId?: string | null;
}) =>
  createAppState({
    gestures,
    bindings,
    presets,
    selectedPatientId: PATIENT_ID,
    activePresetId,
    patients: [
      createPatient({
        patientId: PATIENT_ID,
        patientName: "Alex Morgan",
        notes: "Session fixture",
        keyBindings: Object.fromEntries(
          bindings.map(({ gestureId, key }) => [gestureId, key]),
        ),
        matchThresholds: Object.fromEntries(
          bindings.map(({ gestureId, matchThreshold }) => [
            gestureId,
            matchThreshold ?? 75,
          ]),
        ),
      }),
    ],
  });

test("shows the empty session state", async ({ page }) => {
  await openWithAppState(page, "/#/", createAppState());

  await expect(
    page.getByText(
      "No patient selected. Add a binding, go to calibration, or choose a profile.",
    ),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Start session" }),
  ).toBeDisabled();
  await expect(
    page.getByText("Nothing bound yet", { exact: true }),
  ).toBeVisible();
});

test("routes an unrecorded bound movement to calibration", async ({ page }) => {
  const pendingGesture = createGesture({
    gestureId: "gesture-pending",
    name: "Seated reach",
    calibratedAt: null,
  });
  const binding = createBinding({
    gestureId: pendingGesture.gestureId,
    key: "E",
  });

  await openWithAppState(
    page,
    "/#/",
    createSelectedState({ gestures: [pendingGesture], bindings: [binding] }),
  );

  await expect(
    page.getByText("1 movement not recorded", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Record now" }).click();
  await expect(page).toHaveURL(/\/#\/calibrate\?gesture=gesture-pending$/);
});

test("adds a binding and rejects a duplicate key", async ({ page }) => {
  const boundGesture = createGesture({
    gestureId: "gesture-bound",
    name: "Lean left",
    calibratedAt: RECORDED_AT,
  });
  const unboundGesture = createGesture({
    gestureId: "gesture-unbound",
    name: "Step right",
    calibratedAt: RECORDED_AT,
  });
  const existingBinding = createBinding({
    gestureId: boundGesture.gestureId,
    key: "Q",
    matchThreshold: 72,
  });

  await openWithAppState(
    page,
    "/#/",
    createSelectedState({
      gestures: [boundGesture, unboundGesture],
      bindings: [existingBinding],
    }),
  );

  await page.getByRole("button", { name: "Add binding" }).click();
  const dialog = page.getByRole("dialog", { name: "Add a binding" });
  await dialog.getByRole("button", { name: "Step right", exact: true }).click();

  const customKey = dialog.getByRole("textbox", { name: "Custom key" });
  await customKey.press("q");
  await expect(
    dialog.getByText("That key is already assigned to another movement."),
  ).toBeVisible();
  await expect(
    dialog.getByRole("button", { name: "Add binding" }),
  ).toBeDisabled();
  await expect(
    dialog.getByRole("button", { name: "Q (in use)", exact: true }),
  ).toBeDisabled();

  await customKey.press("k");
  await expect(
    dialog.getByText("That key is already assigned to another movement."),
  ).toBeHidden();
  await dialog.getByRole("button", { name: "Add binding" }).click();

  await expect(
    page.getByRole("button", { name: "Key: K. Change" }),
  ).toBeVisible();
  await waitForAppState(page, (state) => {
    const added = state.bindings.find(
      (item) => item.gestureId === unboundGesture.gestureId,
    );
    const patient = state.patients.find(
      (item) => item.patientId === PATIENT_ID,
    );
    return (
      added?.key === "K" &&
      added.matchThreshold === 75 &&
      patient?.keyBindings[unboundGesture.gestureId] === "K" &&
      patient.matchThresholds[unboundGesture.gestureId] === 75
    );
  });
});

test("persists an edited key and match threshold across reload", async ({
  page,
}) => {
  const gesture = createGesture({
    gestureId: "gesture-edit",
    name: "Raise arm",
    calibratedAt: RECORDED_AT,
  });
  const binding = createBinding({
    gestureId: gesture.gestureId,
    key: "Q",
    matchThreshold: 74,
  });

  await openWithAppState(
    page,
    "/#/",
    createSelectedState({ gestures: [gesture], bindings: [binding] }),
  );

  await page.getByRole("button", { name: "Key: Q. Change" }).click();
  await page.getByRole("menuitem", { name: "Z" }).click();
  await waitForAppState(
    page,
    (state) =>
      state.bindings[0]?.key === "Z" &&
      state.patients[0]?.keyBindings[gesture.gestureId] === "Z",
  );

  await page
    .getByRole("button", { name: "Adjust match threshold for Raise arm" })
    .click();
  const threshold = page.getByRole("slider", { name: "Match threshold" });
  await threshold.fill("83");
  await expect(threshold).toHaveValue("83");

  await waitForAppState(
    page,
    (state) =>
      state.bindings[0]?.matchThreshold === 83 &&
      state.patients[0]?.matchThresholds[gesture.gestureId] === 83,
  );

  await page.reload();

  await expect(
    page.getByRole("button", { name: "Key: Z. Change" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Adjust match threshold for Raise arm" })
    .click();
  await expect(
    page.getByRole("slider", { name: "Match threshold" }),
  ).toHaveValue("83");
  const reloadedState = await readAppState(page);
  expect(reloadedState.bindings[0]).toMatchObject({
    gestureId: gesture.gestureId,
    key: "Z",
    matchThreshold: 83,
  });
  expect(reloadedState.patients[0].keyBindings[gesture.gestureId]).toBe("Z");
  expect(reloadedState.patients[0].matchThresholds[gesture.gestureId]).toBe(83);
});

test("removes, restores, and dismisses a binding through the undo bar", async ({
  page,
}) => {
  const gesture = createGesture({
    gestureId: "gesture-undo",
    name: "Shoulder roll",
    calibratedAt: RECORDED_AT,
  });
  const binding = createBinding({
    gestureId: gesture.gestureId,
    key: "E",
  });

  await openWithAppState(
    page,
    "/#/",
    createSelectedState({ gestures: [gesture], bindings: [binding] }),
  );

  await page
    .getByRole("button", { name: "Remove Shoulder roll binding" })
    .click();
  const undoStatus = page.getByRole("status");
  await expect(undoStatus).toContainText("Removed Shoulder roll");
  await waitForAppState(
    page,
    (state) =>
      state.bindings.length === 0 &&
      !(gesture.gestureId in state.patients[0].keyBindings),
  );

  await undoStatus.getByRole("button", { name: "Undo" }).click();
  await expect(undoStatus).toBeHidden();
  await waitForAppState(
    page,
    (state) =>
      state.bindings[0]?.gestureId === gesture.gestureId &&
      state.patients[0]?.keyBindings[gesture.gestureId] === "E",
  );

  await page
    .getByRole("button", { name: "Remove Shoulder roll binding" })
    .click();
  await page
    .getByRole("status")
    .getByRole("button", { name: "Dismiss" })
    .click();
  await expect(page.getByRole("status")).toBeHidden();
  await waitForAppState(page, (state) => state.bindings.length === 0);
});

test("saves, edits, and loads a preset and retains it across reload", async ({
  page,
}) => {
  const gesture = createGesture({
    gestureId: "gesture-preset",
    name: "Hand wave",
    calibratedAt: RECORDED_AT,
  });
  const binding = createBinding({
    gestureId: gesture.gestureId,
    key: "Q",
    matchThreshold: 76,
  });

  await openWithAppState(
    page,
    "/#/",
    createSelectedState({ gestures: [gesture], bindings: [binding] }),
  );

  await page.getByRole("button", { name: "Save bindings as preset" }).click();
  const saveDialog = page.getByRole("dialog", { name: "Save as preset" });
  await saveDialog
    .getByRole("textbox", { name: "Preset name" })
    .fill("Rehab controls");
  await saveDialog.getByRole("button", { name: "Save", exact: true }).click();

  const savedState = await waitForAppState(
    page,
    (state) =>
      state.presets.some((preset) => preset.name === "Rehab controls") &&
      state.activePresetId !== null,
  );
  const presetId = savedState.presets.find(
    (preset) => preset.name === "Rehab controls",
  )?.presetId;
  expect(presetId).toBeTruthy();

  await page.getByRole("button", { name: "Key: Q. Change" }).click();
  await page.getByRole("menuitem", { name: "Z" }).click();
  await expect(page.getByText("Edited", { exact: true })).toBeVisible();
  await waitForAppState(page, (state) => state.bindings[0]?.key === "Z");

  await page.getByRole("button", { name: "Load preset" }).click();
  await page.getByRole("menuitem", { name: /Rehab controls/ }).click();
  await expect(
    page.getByRole("button", { name: "Key: Q. Change" }),
  ).toBeVisible();
  await expect(page.getByText("Edited", { exact: true })).toBeHidden();
  await waitForAppState(
    page,
    (state) =>
      state.activePresetId === presetId &&
      state.bindings[0]?.key === "Q" &&
      state.patients[0]?.keyBindings[gesture.gestureId] === "Q",
  );

  await page.reload();

  await expect(
    page.getByRole("heading", { name: "Rehab controls", exact: true }),
  ).toHaveCount(2);
  await expect(
    page.getByRole("button", { name: "Key: Q. Change" }),
  ).toBeVisible();
  const reloadedState = await readAppState(page);
  expect(reloadedState.activePresetId).toBe(presetId);
});

test("reports the unavailable Qt bridge when starting a browser session", async ({
  page,
}) => {
  const gesture = createGesture({
    gestureId: "gesture-start",
    name: "Clap",
    calibratedAt: RECORDED_AT,
  });
  const binding = createBinding({
    gestureId: gesture.gestureId,
    key: "Space",
  });

  await openWithAppState(
    page,
    "/#/",
    createSelectedState({ gestures: [gesture], bindings: [binding] }),
  );

  const startSession = page.getByRole("button", { name: "Start session" });
  const errorDialog = page.getByRole("dialog", { name: "Camera error" });

  await expect(errorDialog).toBeHidden();
  await expect(startSession).toBeEnabled();
  await startSession.click();

  await expect(errorDialog).toBeVisible();
  await expect(errorDialog).toContainText("Qt WebChannel is unavailable.");
});
