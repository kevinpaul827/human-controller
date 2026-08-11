import { expect, test } from "@playwright/test";
import { createAppState, seedAppState } from "./helpers";

test("updates tracking mode from the settings page", async ({ page }) => {
  const state = createAppState();
  await seedAppState(page, state);

  await page.goto("/#/settings");

  await page.getByText("Choose manually").click();
  await page.getByRole("radio", { name: /Balanced/i }).check();

  await expect(page.getByRole("radio", { name: /Balanced/i })).toBeChecked();
  await expect(page.getByText("Current: Balanced")).toBeVisible();
});
