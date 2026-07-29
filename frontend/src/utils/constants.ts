export const ROUTES = {
  session: "/",
  profiles: "/profiles",
  library: "/library",
  calibrate: "/calibrate",
  settings: "/settings",
} as const;

export const NAV_ITEMS = [
  { label: "Session", path: ROUTES.session },
  { label: "Profiles", path: ROUTES.profiles },
  { label: "Library", path: ROUTES.library },
  { label: "Settings", path: ROUTES.settings },
];

export const CALIBRATION_STEPS = [
  "Choose movement",
  "Align camera",
  "Record gesture",
  "Save mapping",
];
