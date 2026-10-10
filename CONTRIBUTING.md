# Contributing

Open an issue with the use case before expanding the feature set. Keep the visual-search workflow focused and avoid adding cloud dependencies to the default path.

```sh
uv sync --frozen --extra cpu --group dev
uv run --no-sync scenescout
uv run --no-sync pytest --cov=scenescout --cov-fail-under=80
uv run --no-sync ruff check src examples scripts evaluation tests
uv run --no-sync ruff format --check src examples scripts evaluation tests
npx --yes prettier@3.9.10 --check "src/scenescout/static/*.{js,css,html}"
```

For a behavioral change, describe how you reproduced it, the final behavior, relevant model/runtime versions, and any checks you performed. Do not claim model quality from a single successful query. Do not commit `.data`, model weights, personal videos or secrets.

The UI lives in `src/scenescout/static/` and has no frontend build step. Keep visible text in both translation dictionaries, provide keyboard access, and respect reduced motion. Use DOM text nodes for user-supplied names and queries.
