Frontend tests live in this directory and run with Vitest.

- `appStateModel.test.ts` covers browser-state parsing and pure state helpers.
- `AppStateProvider.test.tsx` covers saving, profiles, gestures, bindings,
  thresholds, presets, unsaved changes, and undo.
- The bridge suites mock Qt WebChannel and cover callback, Promise, synchronous,
  missing, failing, delayed, and signal-based behavior.

Run `npm test` for the suite or `npm run test:coverage` for the HTML and LCOV
coverage reports.
