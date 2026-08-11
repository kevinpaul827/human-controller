# Frontend

This directory contains the React + TypeScript frontend that the desktop app
loads inside `QWebEngineView`.

## Stack

- React
- TypeScript
- Vite
- Radix UI
- Tailwind CSS
- React Router

## Structure

```text
frontend/
├── src/
│   ├── components/
│   ├── context/
│   ├── hooks/
│   ├── lib/
│   ├── pages/
│   ├── services/
│   ├── state/
│   ├── styles/
│   ├── types/
│   └── utils/
├── package.json
└── vite.config.ts
```

Frontend Structure:

- `pages/` contains route-level screens such as Profiles, Library, Calibrate,
  Session, and Settings.
- `components/` contains reusable UI pieces, including session controls and
  gesture mapping.
- `lib/` contains small shared helpers such as class name merging and keyboard
  display helpers.
- `utils/` contains app-level constants and helper functions shared across
  features.
- `services/` talks to the desktop bridge objects exposed over Qt WebChannel.
- `state/` coordinates profiles, movements, bindings, presets, and settings.
- `context/` stores React context used across pages, such as the selected
  profile.
- `styles/` contains the global stylesheet and theme tokens used by the app.

## Desktop Integration

The frontend is not just a standalone web app. In the desktop flow it also:

- loads inside the Qt desktop shell
- reads and saves profile, gesture, binding, preset, and settings state
- reacts to desktop calibration and session state changes
- controls the separate always-on-top session picture-in-picture overlay
- reports calibration preview bounds to the native Qt camera widget

The Session page does not render camera pixels in the browser. Starting a
session opens a separate native picture-in-picture window. Calibration still
reserves and measures a viewport that the desktop app overlays with the native
Qt preview widget.

## Browser vs Desktop Mode

When running with Vite in the browser, the frontend uses browser-friendly
fallbacks where possible so pages can still be developed without the desktop
shell.

When running inside the desktop app, the frontend uses Qt WebChannel bridge
objects to:

- load and save persistent state
- control calibration and live session flows
- open native settings screens
- report preview bounds for native camera overlays

If something works in the browser preview but breaks in the packaged app, the
problem is often in the bridge integration rather than the React UI itself.

## Scripts

```bash
npm ci
npm run dev
npm run build
npm run lint
npm run prettier
npm run test
npm run typecheck
npm run test:e2e
```

Script guide:

- `npm run dev` starts the browser-only Vite frontend.
- `npm run build` runs TypeScript build checks and creates the production
  frontend bundle.
- `npm run test` runs the Vitest unit tests in `jsdom`.
- `npm run test:e2e` runs the Playwright browser E2E suite.

## Playwright E2E

Playwright in this project is set up for the browser version of the frontend
only. It tests the React shell loaded by Vite and does not cover the native Qt
window, camera preview, or OS-level key injection.

The tests live in `frontend/e2e/` and use the app's existing browser fallback
storage instead of the desktop bridge.

Install the bundled Chromium browser once after installing the frontend
dependencies:

```bash
npx playwright install chromium
```

Useful commands:

```bash
npm run test:e2e
npm run test:e2e:headed
npm run test:e2e:ui
```

## Typical Workflows

Use the frontend by itself when you only need browser-side work:

```bash
npm run dev
```

Use the full desktop-integrated workflow from the repository root when you need
the real camera, Qt bridges, key injection, and picture-in-picture overlay:

```bash
make preview-local
```

If you changed frontend code that must be tested inside the packaged macOS app,
rebuild the desktop bundle from the repository root:

```bash
make macos-app
```

## Before Opening a PR

Please run the following checks locally before creating a pull request:

```bash
npm run lint
npm run prettier
npm run test
npm run typecheck
```
