# Frontend

This directory contains the React + TypeScript frontend that the desktop app
loads inside `QWebEngineView`.

## Stack

- React
- TypeScript
- Vite
- Material UI
- React Router
- CSS modules

## Structure

```text
frontend/
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── styles/
│   ├── types/
│   └── utils/
├── package.json
└── vite.config.ts
```

Plain English:

- `pages/` contains route-level screens such as Home, Profiles, Calibrate, Session, and Settings.
- `components/` contains reusable UI pieces, including the session camera panel.
- `services/sessionBridge.ts` talks to the desktop `sessionBridge` object exposed over Qt WebChannel.
- `styles/` contains the CSS modules used by the app.

## Desktop Integration

The frontend is not just a standalone web app. In the desktop flow it also:

- loads inside the Qt desktop shell
- reports the session preview viewport bounds to the Python app
- reacts to desktop session state changes from the Qt bridge
- updates the session preview aspect ratio when the native camera feed changes

The session page itself does not render the real camera pixels in the browser.
Instead, it reserves and measures a viewport that the desktop app overlays with
the native Qt preview widget.

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
the real session preview and Qt bridge behavior:

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
