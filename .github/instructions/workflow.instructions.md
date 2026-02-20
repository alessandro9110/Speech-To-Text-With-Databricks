---
applyTo: ".github/workflows/**/*.yml"
---

- Workflows must use paths filters to run only on:
  - speech_to_text_asset_bundle/**
  - .github/workflows/**
- PR workflows must run lint/tests and `databricks bundle validate -t dev/prod`
- Deploy to prod must require approvals and never use dev credentials.
- Never echo secrets or include real workspace URLs in committed files.