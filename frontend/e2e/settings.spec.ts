import { expect, test } from "@playwright/test";
import { createAppState, openWithAppState, waitForAppState } from "./helpers";

test("selects every manual tracking mode", async ({ page }) => {
  await openWithAppState(page, "/#/settings", createAppState());

  await page.getByText(/^Choose manually/).click();

  const modes = [
    { name: /^Balanced/, value: "full", currentLabel: "Balanced" },
    {
      name: /^High accuracy/,
      value: "heavy",
      currentLabel: "High accuracy",
    },
    { name: /^Fast/, value: "lite", currentLabel: "Fast" },
  ] as const;

  for (const mode of modes) {
    const radio = page.getByRole("radio", { name: mode.name });
    await radio.check();

    await expect(radio).toBeChecked();
    await expect(
      page.getByText(`Choose manually · Current: ${mode.currentLabel}`, {
        exact: true,
      }),
    ).toBeVisible();
    await waitForAppState(
      page,
      (state) => state.settings.poseModel === mode.value,
    );
  }
});

test("persists all tracking settings across a reload", async ({ page }) => {
  await openWithAppState(page, "/#/settings", createAppState());

  await page.getByText(/^Choose manually/).click();
  await page.getByRole("radio", { name: /^High accuracy/ }).check();

  const threshold = page.getByRole("slider", {
    name: "Default match threshold",
  });
  const cooldown = page.getByRole("slider", { name: "Cooldown" });
  const steadiness = page.getByRole("slider", { name: "Steadiness" });

  await threshold.press("End");
  await cooldown.press("End");
  await steadiness.press("End");

  await expect(threshold).toHaveValue("100");
  await expect(cooldown).toHaveValue("2");
  await expect(steadiness).toHaveValue("4");
  await expect(page.getByText("100%", { exact: true })).toBeVisible();
  await expect(page.getByText("2.0s", { exact: true })).toBeVisible();
  await expect(page.getByText("Strict", { exact: true })).toBeVisible();

  await waitForAppState(
    page,
    (state) =>
      state.settings.poseModel === "heavy" &&
      state.settings.matchThreshold === 100 &&
      state.settings.cooldown === 2 &&
      state.settings.smoothing === 4,
  );

  await page.reload();

  await expect(
    page.getByRole("heading", { name: "Tracking preferences" }),
  ).toBeVisible();
  await expect(
    page.getByText("Choose manually · Current: High accuracy", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(threshold).toHaveValue("100");
  await expect(cooldown).toHaveValue("2");
  await expect(steadiness).toHaveValue("4");
  await expect(page.getByText("100%", { exact: true })).toBeVisible();
  await expect(page.getByText("2.0s", { exact: true })).toBeVisible();
  await expect(page.getByText("Strict", { exact: true })).toBeVisible();

  await page.getByText(/^Choose manually/).click();
  await expect(
    page.getByRole("radio", { name: /^High accuracy/ }),
  ).toBeChecked();
});

test("uses deterministic browser hardware for automatic recommendation", async ({
  page,
}) => {
  await page.addInitScript(() => {
    Object.defineProperty(window.navigator, "hardwareConcurrency", {
      configurable: true,
      get: () => 12,
    });
    Object.defineProperty(window.navigator, "deviceMemory", {
      configurable: true,
      get: () => 16,
    });
  });
  await openWithAppState(page, "/#/settings", createAppState());

  await page.getByRole("button", { name: "Calibrate tracking" }).click();

  await expect(page.getByRole("status")).toHaveText(
    "High accuracy selected · 16 GB RAM · 12 logical CPU cores",
  );
  await expect(
    page.getByText("Choose manually · Current: High accuracy", {
      exact: true,
    }),
  ).toBeVisible();
  await waitForAppState(page, (state) => state.settings.poseModel === "heavy");
});
