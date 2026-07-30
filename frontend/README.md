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
│   ├── pages/
│   ├── services/
│   ├── state/
│   ├── styles/
│   ├── types/
│   └── utils/
├── package.json
└── vite.config.ts
```

Plain English:

- `pages/` contains route-level screens such as Profiles, Library, Calibrate,
  Session, and Settings.
- `components/` contains reusable UI pieces, including session controls and
  gesture mapping.
- `services/` talks to the desktop bridge objects exposed over Qt WebChannel.
- `state/` coordinates profiles, movements, bindings, presets, and settings.
- `styles/` contains the global theme and Tailwind CSS configuration.

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

## Scripts

```bash
npm ci
npm run dev
npm run build
npm run lint
npm run prettier
npm run typecheck
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
npm run typecheck
```
