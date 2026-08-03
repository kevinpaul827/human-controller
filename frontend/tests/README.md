Frontend tests should live in this directory.

CI is already set up to look here for real test files. Once the team adds a frontend
test runner and a `test:coverage` script in `frontend/package.json`, the workflow will
run coverage automatically and upload the `frontend/coverage` artifact.
