# Contributing

Open an issue with the use case before expanding the feature set. Keep the visual-search workflow focused and avoid adding cloud dependencies to the default path.

```sh
uv sync --frozen
uv run scenescout
uvx ruff check src examples
uvx ruff format --check src examples
npx --yes prettier@3.9.10 --check "src/scenescout/static/*.{js,css,html}"
```

For a behavioral change, describe how you reproduced it, the final behavior, relevant model/runtime versions, and any checks you performed. Do not claim model quality from a single successful query. Do not commit `.data`, model weights, personal videos or secrets.

The UI lives in `src/scenescout/static/` and has no frontend build step. Keep visible text in both translation dictionaries, provide keyboard access, and respect reduced motion. Use DOM text nodes for user-supplied names and queries.
