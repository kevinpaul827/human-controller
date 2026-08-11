import { expect, test } from "@playwright/test";
import { createAppState, seedAppState } from "./helpers";

test("creates a patient profile in browser fallback mode", async ({ page }) => {
  await seedAppState(page, createAppState());

  await page.goto("/#/profiles");

  await page
    .getByRole("button", { name: "Create profile", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Create patient profile" }),
  ).toBeVisible();

  await page.getByLabel("Patient name").fill("Patient C");
  await page.getByLabel("Notes").fill("Playwright test profile");
  await page.getByRole("button", { name: "Create profile" }).click();

  await expect(
    page.getByRole("heading", { name: "Patient C", exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByText("Playwright test profile").first()).toBeVisible();
});
