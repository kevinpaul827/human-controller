import { expect, test } from "@playwright/test";
import {
  createAppState,
  createGesture,
  openWithAppState,
  readAppState,
} from "./helpers";

test("requires a movement name before advancing to recording", async ({
  page,
}) => {
  await openWithAppState(page, "/#/calibrate", createAppState());

  const nextButton = page.getByRole("button", { name: "Next" });
  await expect(nextButton).toBeDisabled();

  await page.getByLabel("Movement name").fill("Side reach");
  await expect(nextButton).toBeEnabled();
  await nextButton.click();

  await expect(page.getByRole("list", { name: "Step 2 of 3" })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Side reach", exact: true }),
  ).toBeVisible();
});

test("returns to the Library without creating a movement", async ({ page }) => {
  await openWithAppState(page, "/#/calibrate", createAppState());

  await page.getByLabel("Movement name").fill("Do not save");
  await page.getByRole("button", { name: "Back" }).click();

  await expect(page).toHaveURL(/\/#\/library$/);
  await expect(
    page.getByRole("heading", { name: "Movement library", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("No movements yet", { exact: true }),
  ).toBeVisible();
  expect((await readAppState(page)).gestures).toEqual([]);
});

test("reports the unavailable Qt bridge in browser recording mode", async ({
  page,
}) => {
  await openWithAppState(page, "/#/calibrate", createAppState());

  await page.getByLabel("Movement name").fill("Browser bridge check");
  await page.getByRole("button", { name: "Next" }).click();

  await expect(page.getByRole("list", { name: "Step 2 of 3" })).toBeVisible();
  await expect(
    page.getByText("Qt WebChannel is unavailable.", { exact: true }),
  ).toBeVisible();
});

test("loads an existing movement from the gesture query parameter", async ({
  page,
}) => {
  const gesture = createGesture({
    gestureId: "gesture-existing-reach",
    name: "Existing shoulder reach",
    calibratedAt: "2026-01-02T03:04:05.000Z",
    matchScore: 0.92,
  });
  const state = createAppState({ gestures: [gesture] });

  await openWithAppState(
    page,
    `/#/calibrate?gesture=${gesture.gestureId}`,
    state,
  );

  await expect(
    page.getByRole("heading", {
      name: `Record “${gesture.name}”`,
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: gesture.name, exact: true }),
  ).toBeVisible();
  await expect(page.getByRole("list", { name: "Step 2 of 3" })).toBeVisible();
});
