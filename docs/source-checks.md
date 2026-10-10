# Source checks

The release was checked locally with Ruff lint/format, Python compilation, JavaScript syntax validation, Prettier and Python package build. These checks do not evaluate retrieval accuracy or replace behavioral tests.

```sh
uvx ruff@0.17.0 check src examples
uvx ruff@0.17.0 format --check src examples
uv run python -m compileall -q src examples
node --check src/scenescout/static/app.js
npx --yes prettier@3.9.10 --check "src/scenescout/static/*.{js,css,html}"
uv build
```

`docs/ci-workflow.yml` is a ready-to-use GitHub Actions template. **It is not active** in this repository: the publishing connection did not have workflow-write permission, and the GitHub integration also rejected creation. Local checks succeeded; no hosted CI run is claimed.

To activate it using an account connection that can write workflows, place it at `.github/workflows/checks.yml`. It runs source checks only, with read-only repository permissions. It does not download the model, process media or run an automated behavioral suite.
