# Copilot Instructions

## Code review focus
When reviewing PRs, enforce documentation quality.

### Documentation rules (required)
- Every new public function/method/class must have a docstring.
- Non-trivial logic must have comments explaining the "why", not the "what".
- Spark transformations: add a short comment for complex joins, window specs, and non-obvious filters.
- If a code block is hard to understand in <10 seconds, request a comment or refactor.

### What to do in review
- If a rule is violated, request changes and point to the exact file/line.
- Suggest an example docstring/comment that matches the code.
- Prefer concise English comments.