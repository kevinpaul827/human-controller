import { expect, test } from "@playwright/test";

test("navigates between the main frontend pages", async ({ page }) => {
  await page.goto("/#/profiles");

  await expect(
    page.getByRole("heading", { name: "Patient profiles", exact: true }),
  ).toBeVisible();

  await page.getByRole("link", { name: /Settings/i }).click();
  await expect(
    page.getByRole("heading", { name: "Tracking preferences" }),
  ).toBeVisible();

  await page.getByRole("link", { name: /Library/i }).click();
  await expect(
    page.getByRole("heading", { name: "Movement library" }),
  ).toBeVisible();

  await page.goto("/#/");
  await expect(page.getByText("Human Controller")).toBeVisible();
});
