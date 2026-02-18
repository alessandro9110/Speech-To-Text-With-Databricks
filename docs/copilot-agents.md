# Copilot Custom Agents

Custom GitHub Copilot agents are stored under `.github/agents/`.

## Agents overview

| Agent (file) | Purpose | Primary scope | Use it when… |
|---|---|---|---|
| **Databricks Platform Engineer (DE/AI/ML + Lakeflow)** (`databricks-platform-engineer.agent.md`) | End-to-end Databricks expert for Data Engineering + AI/ML. Designs Lakeflow pipelines and implements notebooks + PySpark code following best practices. | `speech_to_text_asset_bundle/` (DAB solution: notebooks/scripts, `src/`, `resources/`, `tests/`) | You need to build or evolve the Databricks solution (pipelines/jobs/notebooks, PySpark modules, data flows, AI/ML-oriented DE patterns). |
| **DAB Specialist (Secure Public Repo)** (`dab-specialist.agent.md`) | Maintains and improves the Databricks Asset Bundle configuration using DAB best practices; fixes targets/paths and enforces public-repo hygiene. | `speech_to_text_asset_bundle/databricks.yml` + `speech_to_text_asset_bundle/resources/**` | You need to update/fix the bundle config, resources wiring, variables/targets, deployment paths (Shared), or sanitize config for a public repo (no hosts/secrets/PII). |
| **DAB + Workflows Engineer** (`dab-workflows-engineer.agent.md`) | Owns GitHub Actions CI/CD for DAB: PR checks, validation, and safe deploy orchestration using DAB targets/variables and GitHub Environments. | `.github/workflows/**` (reads `speech_to_text_asset_bundle/databricks.yml` as source of truth) | You need to change CI/CD (triggers, ruff/pytest, bundle validate, deploy dev/prod, approvals) without hardcoding secrets or inventing bundle variables. |
| **Docs & Architecture Writer** (`docs-writer.agent.md`) | Writes clear and precise documentation: README as main entry (solution + setup) and `/docs/*.md` as deep dives. | `README.md` + `docs/*.md` (validated against `speech_to_text_asset_bundle/` and workflows) | You need to update docs to match the real implementation, describe project structure first, then solution details, and keep setup instructions accurate (DAB + GitHub Actions). |

## Repository documentation structure

| Area | Location | What it contains |
|---|---|---|
| Main documentation | `README.md` (root) | Solution overview + configuration/setup for Databricks Asset Bundles and GitHub Actions; links to `/docs`. |
| Additional docs | `docs/` | Extra markdown documents (deep dives, runbooks, troubleshooting, conventions). |
| Databricks solution (DAB) | `speech_to_text_asset_bundle/` | Bundle config (`databricks.yml`), jobs/pipelines/resources (`resources/**`), PySpark/Python code (`src/**`), tests (`tests/**`). |
