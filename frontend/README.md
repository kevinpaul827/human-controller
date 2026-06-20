# Frontend

This directory contains the stubbed React + TypeScript frontend for the project.

## Stack

- React
- TypeScript
- Vite
- Material UI
- React Router

## Structure

```text
src/
  components/
  pages/
  routes/
  styles/
  utils/
```

## Pages

- Home
- Profiles
- Calibrate
- Session
- Settings

## Scripts

```bash
npm install
npm run dev
npm run lint
npm run prettier
npm run typecheck
```

## Before Opening a PR

Please run the following checks locally before creating a pull request:

```bash
npm run lint
npm run prettier
npm run typecheck
```

## Notes

- Shared styling is handled with CSS modules.
- Routing is defined in `src/routes/AppRoutes.tsx`.
- The app shell currently uses a top header and a left sidebar.
