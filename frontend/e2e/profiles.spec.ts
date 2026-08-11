import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
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

const headerCreateProfileButton = (page: Page) =>
  page
    .locator("header")
    .filter({
      has: page.getByRole("heading", {
        name: "Patient profiles",
        exact: true,
      }),
    })
    .getByRole("button", { name: "Create profile", exact: true });

test("shows the empty profile state and opens creation from both entry points", async ({
  page,
}) => {
  await openWithAppState(page, "/#/profiles", createAppState());

  await expect(
    page.getByRole("heading", { name: "No patient profiles" }),
  ).toBeVisible();

  const headerCreateButton = headerCreateProfileButton(page);
  const emptyStateCard = page
    .getByRole("heading", { name: "No patient profiles", exact: true })
    .locator("..")
    .locator("..");
  const emptyStateCreateButton = emptyStateCard.getByRole("button", {
    name: "Create profile",
    exact: true,
  });

  const dialog = page.getByRole("dialog", {
    name: "Create patient profile",
  });

  await headerCreateButton.click();
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(dialog).toBeHidden();

  await emptyStateCreateButton.click();
  await expect(dialog).toBeVisible();
  await dialog.getByRole("button", { name: "Close" }).click();
  await expect(dialog).toBeHidden();
});

test("validates profile names and cancellation creates nothing", async ({
  page,
}) => {
  await openWithAppState(page, "/#/profiles", createAppState());

  await headerCreateProfileButton(page).click();

  const dialog = page.getByRole("dialog", {
    name: "Create patient profile",
  });
  const patientName = dialog.getByLabel("Patient name");

  await patientName.fill("   ");
  await dialog
    .getByRole("button", { name: "Create profile", exact: true })
    .click();
  await expect(dialog.getByRole("alert")).toHaveText(
    "Patient name is required.",
  );

  await patientName.fill("P".repeat(81));
  await dialog
    .getByRole("button", { name: "Create profile", exact: true })
    .click();
  await expect(dialog.getByRole("alert")).toHaveText(
    "Patient name cannot exceed 80 characters.",
  );

  await dialog.getByRole("button", { name: "Cancel" }).click();
  await expect(dialog).toBeHidden();
  await expect(
    page.getByRole("heading", { name: "No patient profiles" }),
  ).toBeVisible();
  expect((await readAppState(page)).patients).toEqual([]);
});

test("creates a trimmed profile and retains its selection after reload", async ({
  page,
}) => {
  await openWithAppState(page, "/#/profiles", createAppState());

  await headerCreateProfileButton(page).click();

  const dialog = page.getByRole("dialog", {
    name: "Create patient profile",
  });
  await dialog.getByLabel("Patient name").fill("  Taylor Morgan  ");
  await dialog
    .getByLabel("Notes")
    .fill("  Prefers seated movements and short sessions.  ");
  await dialog
    .getByRole("button", { name: "Create profile", exact: true })
    .click();

  const persisted = await waitForAppState(
    page,
    (state) =>
      state.patients.length === 1 &&
      state.patients[0].patientName === "Taylor Morgan" &&
      state.patients[0].notes ===
        "Prefers seated movements and short sessions." &&
      state.selectedPatientId === state.patients[0].patientId,
  );

  const createdHeading = page.getByRole("heading", {
    name: "Taylor Morgan",
    exact: true,
  });
  const createdNotes = page.getByText(
    "Prefers seated movements and short sessions.",
    { exact: true },
  );
  await expect(createdHeading).toHaveCount(1);
  await expect(createdHeading).toBeVisible();
  await expect(createdNotes).toHaveCount(1);
  await expect(createdNotes).toBeVisible();

  await page.reload();

  await expect(
    page.getByRole("heading", { name: "Taylor Morgan", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Taylor Morgan", exact: true }),
  ).toBeVisible();
  expect(await readAppState(page)).toMatchObject({
    selectedPatientId: persisted.patients[0].patientId,
    patients: [
      {
        patientId: persisted.patients[0].patientId,
        patientName: "Taylor Morgan",
        notes: "Prefers seated movements and short sessions.",
      },
    ],
  });
});

test("adds, changes, removes, and persists profile movement bindings", async ({
  page,
}) => {
  const reach = createGesture({
    gestureId: "gesture-side-reach",
    name: "Side Reach",
    calibratedAt: "2026-06-01T10:00:00.000Z",
  });
  const lift = createGesture({
    gestureId: "gesture-knee-lift",
    name: "Knee Lift",
    calibratedAt: "2026-06-02T10:00:00.000Z",
  });
  const patient = createPatient({
    patientId: "patient-bindings",
    patientName: "Sam Rivera",
  });

  await openWithAppState(
    page,
    "/#/profiles",
    createAppState({
      gestures: [reach, lift],
      patients: [patient],
      selectedPatientId: patient.patientId,
    }),
  );

  await page.getByRole("button", { name: "Manage bindings" }).click();
  await page.getByLabel("Movement").selectOption(reach.gestureId);

  const newKey = page.getByLabel(`Key for ${patient.patientName}`);
  await newKey.press("k");
  await expect(newKey).toHaveValue("K");
  await page.getByRole("button", { name: "Add binding" }).click();

  await expect(page.getByText(reach.name, { exact: true })).toBeVisible();
  await expect(page.getByText("K", { exact: true })).toBeVisible();
  await waitForAppState(page, (state) => {
    const storedPatient = state.patients.find(
      ({ patientId }) => patientId === patient.patientId,
    );
    return (
      storedPatient?.keyBindings[reach.gestureId] === "K" &&
      storedPatient.matchThresholds[reach.gestureId] === 75 &&
      state.bindings.some(
        ({ gestureId, key }) => gestureId === reach.gestureId && key === "K",
      )
    );
  });

  await page.getByRole("button", { name: "Change key" }).click();
  const editedKey = page.getByLabel(`New key for ${reach.name}`);
  await editedKey.press("j");
  await expect(editedKey).toHaveValue("J");
  await page.getByRole("button", { name: "Save", exact: true }).click();

  await expect(page.getByText("J", { exact: true })).toBeVisible();
  await waitForAppState(page, (state) => {
    const storedPatient = state.patients.find(
      ({ patientId }) => patientId === patient.patientId,
    );
    return (
      storedPatient?.keyBindings[reach.gestureId] === "J" &&
      state.bindings.some(
        ({ gestureId, key }) => gestureId === reach.gestureId && key === "J",
      )
    );
  });

  await page.getByRole("button", { name: "Remove", exact: true }).click();
  const removedState = await waitForAppState(page, (state) => {
    const storedPatient = state.patients.find(
      ({ patientId }) => patientId === patient.patientId,
    );
    return (
      storedPatient !== undefined &&
      !(reach.gestureId in storedPatient.keyBindings) &&
      !(reach.gestureId in storedPatient.matchThresholds) &&
      !state.bindings.some(({ gestureId }) => gestureId === reach.gestureId)
    );
  });
  expect(removedState.patients[0].keyBindings).toEqual({});

  await page.reload();
  await page.getByRole("button", { name: "Manage bindings" }).click();
  await expect(
    page.getByText("No movements are bound to this profile yet.", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByLabel("Movement")).toContainText(reach.name);
  expect((await readAppState(page)).bindings).toEqual([]);
});

for (const routeCase of [
  {
    action: "Calibrate",
    destination: /\/#\/calibrate$/,
  },
  {
    action: "Start session",
    destination: /\/#\/$/,
  },
] as const) {
  test(`${routeCase.action} selects the profile and opens its route`, async ({
    page,
  }) => {
    const patient = createPatient({
      patientId: `patient-${routeCase.action.toLowerCase().replace(" ", "-")}`,
      patientName: "Jordan Lee",
    });
    await openWithAppState(
      page,
      "/#/profiles",
      createAppState({ patients: [patient] }),
    );

    await page
      .getByRole("button", { name: routeCase.action, exact: true })
      .click();

    await expect(page).toHaveURL(routeCase.destination);
    await waitForAppState(
      page,
      (state) => state.selectedPatientId === patient.patientId,
    );
    const profileSwitcher = page.getByRole("button", {
      name: patient.patientName,
      exact: true,
    });
    await expect(profileSwitcher).toBeVisible();
  });
}

test("profile deletion respects confirmation and clears selected bindings", async ({
  page,
}) => {
  const gesture = createGesture({
    gestureId: "gesture-delete-profile",
    name: "Shoulder Raise",
    calibratedAt: "2026-06-03T10:00:00.000Z",
  });
  const binding = createBinding({
    gestureId: gesture.gestureId,
    key: "Q",
    matchThreshold: 81,
  });
  const patient = createPatient({
    patientId: "patient-to-delete",
    patientName: "Casey Chen",
    keyBindings: { [gesture.gestureId]: binding.key },
    matchThresholds: { [gesture.gestureId]: binding.matchThreshold ?? 75 },
  });
  const preset = createPreset({
    presetId: "preset-active",
    name: "Active controls",
    bindings: [binding],
  });

  await openWithAppState(
    page,
    "/#/profiles",
    createAppState({
      gestures: [gesture],
      bindings: [binding],
      patients: [patient],
      selectedPatientId: patient.patientId,
      presets: [preset],
      activePresetId: preset.presetId,
    }),
  );

  let dismissedPrompt = "";
  page.once("dialog", async (dialog) => {
    dismissedPrompt = dialog.message();
    await dialog.dismiss();
  });
  await page.getByRole("button", { name: "Delete", exact: true }).click();

  expect(dismissedPrompt).toContain(patient.patientName);
  await expect(
    page.getByRole("heading", { name: patient.patientName, exact: true }),
  ).toBeVisible();
  expect(await readAppState(page)).toMatchObject({
    selectedPatientId: patient.patientId,
    bindings: [binding],
    patients: [{ patientId: patient.patientId }],
  });

  page.once("dialog", async (dialog) => {
    await dialog.accept();
  });
  await page.getByRole("button", { name: "Delete", exact: true }).click();

  const deletedState = await waitForAppState(
    page,
    (state) =>
      state.patients.length === 0 &&
      state.selectedPatientId === null &&
      state.activePresetId === null &&
      state.bindings.length === 0,
  );
  expect(deletedState).toMatchObject({
    patients: [],
    selectedPatientId: null,
    activePresetId: null,
    bindings: [],
  });
  await expect(
    page.getByRole("heading", { name: "No patient profiles" }),
  ).toBeVisible();

  await page.reload();
  expect(await readAppState(page)).toMatchObject({
    patients: [],
    selectedPatientId: null,
    bindings: [],
  });
});
