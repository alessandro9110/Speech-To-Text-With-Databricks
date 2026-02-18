## README structure (MUST keep this order)
The README must always follow this section order and headings (you may add small sub-sections, but do not reorder):

1. Overview
2. Configuration (FIRST)
   2.1 Prerequisites
   2.2 Authentication & Secrets
   2.3 Environments (dev/prod) and variables
3. Repository / Code structure (SECOND)
   3.1 Databricks Asset Bundle layout
   3.2 Notebooks
   3.3 Pipelines / Jobs (resources)
   3.4 Python package (`src/`)
   3.5 Tests
4. How to run
   4.1 Local checks (lint/tests) (only if configured)
   4.2 DAB commands (validate/deploy) (only if bundle exists)
5. CI/CD
6. Security notes (public repo hygiene)
7. Planned / TODO (optional, only if needed)

## Formatting rules
- Keep headings stable. Avoid renaming them unless explicitly requested.
- Configuration section must explain how to set values WITHOUT exposing real hosts/tokens.
- Code structure section must describe notebooks/pipelines based on what exists in `speech_to_text_asset_bundle/`.
- If a section has no current implementation, keep the heading and write “Not implemented yet” + a short TODO.