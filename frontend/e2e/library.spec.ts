import { expect, test } from "@playwright/test";
import {
  createAppState,
  createBinding,
  createGesture,
  createPatient,
  createPreset,
  openWithAppState,
  readAppState,
  waitForAppState,
} from "./helpers";

test("shows an empty movement library and a zero movement count", async ({
  page,
}) => {
  await openWithAppState(page, "/#/library", createAppState());

  await expect(
    page.getByRole("heading", { name: "Movement library" }),
  ).toBeVisible();
  await expect(page.getByText("0 movements", { exact: true })).toBeVisible();
  await expect(
    page.getByText("No movements yet", { exact: true }),
  ).toBeVisible();
});

test("cancels an empty movement and adds a trimmed pending movement", async ({
  page,
}) => {
  await openWithAppState(page, "/#/library", createAppState());

  await page.getByRole("button", { name: "Record new movement" }).click();
  const dialog = page.getByRole("dialog", { name: "Add movement" });
  const addAndRecord = dialog.getByRole("button", {
    name: "Add and record",
  });

  await expect(dialog).toBeVisible();
  await expect(addAndRecord).toBeDisabled();
  await dialog.getByLabel("Movement name").fill("   ");
  await expect(addAndRecord).toBeDisabled();

  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(dialog).toBeHidden();
  expect((await readAppState(page)).gestures).toEqual([]);

  await page.getByRole("button", { name: "Record new movement" }).click();
  await dialog.getByLabel("Movement name").fill("  Forward Reach  ");
  await expect(addAndRecord).toBeEnabled();
  await addAndRecord.click();

  const persisted = await waitForAppState(
    page,
    (state) =>
      state.gestures.length === 1 &&
      state.gestures[0].name === "Forward Reach" &&
      state.gestures[0].calibratedAt === null,
  );
  await expect(page).toHaveURL(/\/#\/calibrate\?gesture=/);
  expect(new URL(page.url()).hash).toBe(
    `#/calibrate?gesture=${persisted.gestures[0].gestureId}`,
  );
  expect(persisted.gestures[0]).toMatchObject({
    name: "Forward Reach",
    calibratedAt: null,
    matchScore: null,
  });
});

test("routes recorded and pending movements to their matching calibration IDs", async ({
  page,
}) => {
  const recorded = createGesture({
    gestureId: "gesture-recorded",
    name: "Recorded Wave",
    calibratedAt: "2026-06-01T10:00:00.000Z",
    matchScore: 92,
  });
  const pending = createGesture({
    gestureId: "gesture-pending",
    name: "Pending Step",
  });

  await openWithAppState(
    page,
    "/#/library",
    createAppState({ gestures: [recorded, pending] }),
  );

  await expect(page.getByText("2 movements", { exact: true })).toBeVisible();
  await expect(page.getByText(recorded.name, { exact: true })).toBeVisible();
  await expect(page.getByText(pending.name, { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Re-record", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Record", exact: true }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Re-record", exact: true }).click();
  await expect(page).toHaveURL(
    new RegExp(`/#/calibrate\\?gesture=${recorded.gestureId}$`),
  );

  await page.getByRole("link", { name: "Library", exact: true }).click();
  await page.getByRole("button", { name: "Record", exact: true }).click();
  await expect(page).toHaveURL(
    new RegExp(`/#/calibrate\\?gesture=${pending.gestureId}$`),
  );
});

test("deleting a movement cascades through bindings, patients, and presets", async ({
  page,
}) => {
  const deletedGesture = createGesture({
    gestureId: "gesture-retired",
    name: "Retired Movement",
    calibratedAt: "2026-06-01T10:00:00.000Z",
  });
  const retainedGesture = createGesture({
    gestureId: "gesture-retained",
    name: "Retained Movement",
    calibratedAt: "2026-06-02T10:00:00.000Z",
  });
  const deletedBinding = createBinding({
    gestureId: deletedGesture.gestureId,
    key: "R",
    matchThreshold: 82,
  });
  const retainedBinding = createBinding({
    gestureId: retainedGesture.gestureId,
    key: "T",
    matchThreshold: 77,
  });
  const patient = createPatient({
    patientId: "patient-library-cascade",
    patientName: "Morgan Diaz",
    keyBindings: {
      [deletedGesture.gestureId]: deletedBinding.key,
      [retainedGesture.gestureId]: retainedBinding.key,
    },
    matchThresholds: {
      [deletedGesture.gestureId]: deletedBinding.matchThreshold ?? 75,
      [retainedGesture.gestureId]: retainedBinding.matchThreshold ?? 75,
    },
  });
  const preset = createPreset({
    presetId: "preset-library-cascade",
    name: "Two movements",
    bindings: [deletedBinding, retainedBinding],
  });

  await openWithAppState(
    page,
    "/#/library",
    createAppState({
      gestures: [deletedGesture, retainedGesture],
      bindings: [deletedBinding, retainedBinding],
      patients: [patient],
      selectedPatientId: patient.patientId,
      presets: [preset],
      activePresetId: preset.presetId,
    }),
  );

  await page
    .getByRole("button", {
      name: `Delete ${deletedGesture.name}`,
      exact: true,
    })
    .click();

  const persisted = await waitForAppState(page, (state) => {
    const storedPatient = state.patients.find(
      ({ patientId }) => patientId === patient.patientId,
    );
    const storedPreset = state.presets.find(
      ({ presetId }) => presetId === preset.presetId,
    );
    return (
      !state.gestures.some(
        ({ gestureId }) => gestureId === deletedGesture.gestureId,
      ) &&
      !state.bindings.some(
        ({ gestureId }) => gestureId === deletedGesture.gestureId,
      ) &&
      storedPatient !== undefined &&
      !(deletedGesture.gestureId in storedPatient.keyBindings) &&
      !(deletedGesture.gestureId in storedPatient.matchThresholds) &&
      storedPreset !== undefined &&
      !storedPreset.bindings.some(
        ({ gestureId }) => gestureId === deletedGesture.gestureId,
      )
    );
  });

  expect(persisted.gestures.map(({ gestureId }) => gestureId)).toEqual([
    retainedGesture.gestureId,
  ]);
  expect(persisted.bindings).toEqual([retainedBinding]);
  expect(persisted.patients[0].keyBindings).toEqual({
    [retainedGesture.gestureId]: retainedBinding.key,
  });
  expect(persisted.patients[0].matchThresholds).toEqual({
    [retainedGesture.gestureId]: retainedBinding.matchThreshold,
  });
  expect(persisted.presets[0].bindings).toEqual([retainedBinding]);

  await expect(
    page.getByText(deletedGesture.name, { exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByText(retainedGesture.name, { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("1 movement", { exact: true })).toBeVisible();

  await page.reload();
  expect(await readAppState(page)).toMatchObject({
    gestures: [retainedGesture],
    bindings: [retainedBinding],
    patients: [
      {
        patientId: patient.patientId,
        keyBindings: {
          [retainedGesture.gestureId]: retainedBinding.key,
        },
        matchThresholds: {
          [retainedGesture.gestureId]: retainedBinding.matchThreshold,
        },
      },
    ],
    presets: [{ presetId: preset.presetId, bindings: [retainedBinding] }],
  });
});
