export const ROUTES = {
  home: "/",
  profiles: "/profiles",
  calibrate: "/calibrate",
  session: "/session",
  settings: "/settings",
} as const;

export const NAV_ITEMS = [
  { label: "Home", path: ROUTES.home },
  { label: "Profiles", path: ROUTES.profiles },
  { label: "Calibrate", path: ROUTES.calibrate },
  { label: "Session", path: ROUTES.session },
  { label: "Settings", path: ROUTES.settings },
];

export const CALIBRATION_STEPS = [
  "Choose movement",
  "Align camera",
  "Record gesture",
  "Save mapping",
];
