# Copilot Custom Agents

This repository defines custom GitHub Copilot agents to support development, CI/CD, and documentation.
Agents are stored under `.github/agents/`.

## Quick guide: which agent to use

### 1) Databricks Platform Engineer (DE/AI/ML + Lakeflow)
**When to use:** end-to-end Databricks development (pipelines, notebooks, PySpark modules, data engineering + AI/ML patterns).  
**Focus:** implements and improves the Databricks solution under `speech_to_text_asset_bundle/`, including Lakeflow pipeline design that will be deployed via DAB.  
**Typical tasks:** create/modify notebooks and PySpark code, define pipelines/jobs/resources, enforce DE best practices and scalable Spark patterns.

---

### 2) DAB Specialist (Secure Public Repo)
**When to use:** changes to the Databricks Asset Bundle configuration and resources.  
**Focus:** `speech_to_text_asset_bundle/databricks.yml` + `speech_to_text_asset_bundle/resources/**` using DAB best practices. Fixes misconfigured paths/targets and enforces public-repo hygiene.  
**Key rules:** no real workspace host URLs, no secrets, dev/prod via targets/variables, deploy under `/Workspace/Shared/...`.

---

### 3) DAB + Workflows Engineer
**When to use:** GitHub Actions CI/CD pipeline design and maintenance.  
**Focus:** `.github/workflows/**` — orchestrates `databricks bundle validate/deploy` using targets/variables defined in `databricks.yml` (does not invent variable names).  
**Typical tasks:** PR checks (ruff/pytest + bundle validate), path-based triggers, dev deploy automation, prod deploy with approvals (GitHub Environments).

---

### 4) Docs & Architecture Writer
**When to use:** writing/updating documentation in a structured and accurate way.  
**Focus:** root `README.md` as the main entrypoint (solution overview + configuration/setup for DAB and GitHub Actions) and `/docs/*.md` as deep-dives.  
**Key rule:** documentation must reflect what actually exists in `speech_to_text_asset_bundle/` and workflows; if missing, mark as Planned/TODO.

---

## Repository documentation structure

- `README.md` (root): main documentation entrypoint  
  - solution overview  
  - configuration and setup (DAB + GitHub Actions)  
  - references to `/docs`

- `docs/`: additional markdown documents  
  - deep dives, runbooks, troubleshooting, conventions

- `speech_to_text_asset_bundle/`: the Databricks solution (DAB)  
  - jobs/pipelines definitions (`resources/**`)  
  - bundle configuration (`databricks.yml`)  
  - notebooks/scripts and PySpark modules (`src/**`)

