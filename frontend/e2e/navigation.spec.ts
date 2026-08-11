import { expect, test } from "@playwright/test";

const routes = [
  { path: "/#/", navigationName: "Session", heading: "Session" },
  {
    path: "/#/profiles",
    navigationName: "Profiles",
    heading: "Patient profiles",
  },
  {
    path: "/#/library",
    navigationName: "Library",
    heading: "Movement library",
  },
  {
    path: "/#/calibrate",
    navigationName: "Calibration",
    heading: "Record a movement",
  },
  {
    path: "/#/settings",
    navigationName: "Settings",
    heading: "Tracking preferences",
  },
] as const;

test("renders each main application route", async ({ page }) => {
  for (const route of routes) {
    await page.goto(route.path);

    await expect(
      page.getByRole("heading", {
        name: route.heading,
        exact: true,
      }),
    ).toBeVisible();
  }
});

test("marks only the current navigation link as active", async ({ page }) => {
  for (const route of routes) {
    await page.goto(route.path);

    const navigation = page.getByRole("navigation", {
      name: "Main",
    });
    const activeLink = navigation.getByRole("link", {
      name: route.navigationName,
      exact: true,
    });

    await expect(activeLink).toHaveAttribute("aria-current", "page");
    await expect(navigation.locator('[aria-current="page"]')).toHaveCount(1);
  }
});

test("redirects an unknown route to Session", async ({ page }) => {
  await page.goto("/#/does-not-exist");

  await expect(page).toHaveURL(/\/#\/$/);
  await expect(
    page.getByRole("heading", {
      name: "Session",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("navigation", { name: "Main" }).getByRole("link", {
      name: "Session",
      exact: true,
    }),
  ).toHaveAttribute("aria-current", "page");
});
