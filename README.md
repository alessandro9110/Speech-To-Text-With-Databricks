# Speech-To-Text-With-Databricks

A speech-to-text processing solution using **Databricks Asset Bundles** for infrastructure-as-code and **GitHub Actions** for automated CI/CD deployment.

---

## Overview

This repository implements an end-to-end speech-to-text (STT) pipeline on Databricks:

- Audio files are ingested from Unity Catalog Volumes using Auto Loader
- Data flows through a Bronze → Silver medallion architecture (Spark Declarative Pipelines)
- Deployment is automated via GitHub Actions with OIDC authentication
- Infrastructure is managed via Databricks Asset Bundles (DAB)

### What's Implemented

✅ **Audio Ingestion Pipeline** — Bronze and Silver layers track audio file metadata  
✅ **Automated CI/CD** — GitHub Actions deploy to Dev and Prod environments  
✅ **Infrastructure as Code** — Databricks Asset Bundle with dev/prod targets

### TODO

- [ ] **Text Extraction** — Transcription job calling model serving endpoint
- [ ] **Dashboard Creation** — Databricks AI/BI dashboards for monitoring and analysis
- [ ] **Genie Space** — Natural language interface for querying transcription results

---

## Quick Start

### Prerequisites

- Databricks workspace with Unity Catalog enabled
- GitHub repository with administrative access
- Databricks CLI installed (optional, for local deployment)

### Setup

1. **Configure Databricks** — Create catalog, service principal, and federation policies  
   → See [docs/DATABRICKS_SETUP.md](docs/DATABRICKS_SETUP.md)

2. **Configure GitHub Actions** — Set up environments, variables, and secrets  
   → See [docs/GITHUB_ACTIONS_SETUP.md](docs/GITHUB_ACTIONS_SETUP.md)

3. **Deploy** — Push to `dev` or `main` branch to trigger automated deployment

---

## Project Structure

```
Speech-To-Text-With-Databricks/
├── speech_to_text_asset_bundle/     # Databricks Asset Bundle (DAB)
│   ├── databricks.yml               # Bundle config: variables, targets (dev/prod)
│   ├── resources/                   # Jobs, pipelines, schemas, volumes
│   ├── src/                         # Python code: notebooks, transformations
│   ├── tests/                       # Unit and integration tests
│   └── pyproject.toml               # Python dependencies and tooling
├── .github/workflows/               # CI/CD automation
│   ├── sync_git_folder_and_deploy_adb_dev.yml   # Deploy to Dev on push to 'dev'
│   └── sync_git_folder_and_deploy_adb_prod.yml  # Deploy to Prod on push to 'main'
├── docs/                            # Additional documentation
└── README.md                        # This file
```

### `/speech_to_text_asset_bundle`

The core Databricks solution. Contains:

- **`databricks.yml`** — Bundle configuration with `dev` and `prod` targets
- **`resources/`** — YAML definitions for pipelines, schemas, volumes
- **`src/stt_bundle_audio_etl/transformations/`** — Python files for Bronze/Silver tables using Spark Declarative Pipelines
- **`tests/`** — Unit tests for transformations
- **`pyproject.toml`** — Dependencies (PySpark, pytest, ruff)

**For detailed documentation**, see [speech_to_text_asset_bundle/README.md](speech_to_text_asset_bundle/README.md)

### `/.github/workflows`

GitHub Actions workflows for CI/CD:

- **`sync_git_folder_and_deploy_adb_dev.yml`** — Syncs Git folder and deploys to Dev when code is pushed to `dev` branch
- **`sync_git_folder_and_deploy_adb_prod.yml`** — Deploys asset bundle to Prod when code is pushed to `main` branch

Both workflows use GitHub OIDC for secure, token-less authentication with Databricks.

---

## Solution Details

### Data Flow

1. **Audio files** are uploaded to `/Volumes/speech_to_text/audio/files/` (Unity Catalog Volume)
2. **Bronze layer** ingests files using Auto Loader (streaming)
   - Tracks metadata: path, size, modification time
   - Stores raw binary content for downstream transcription
3. **Silver layer** validates and enriches records
   - Extracts file name and extension
   - Filters unsupported formats
   - Marks files as `pending` for transcription
4. **Transcription** (TODO) — Downstream job processes silver records and calls model serving endpoint
5. **Gold layer** (TODO) — Stores transcription results (text, timestamps, confidence scores)
6. **Analytics** (TODO) — Dashboards and Genie for querying transcription data

### Technologies

- **Spark Declarative Pipelines (SDP)** — Serverless streaming pipelines with `@dp.table` decorators
- **Auto Loader** — Incremental ingestion from Unity Catalog Volumes
- **Unity Catalog** — Centralized data governance and metadata management
- **Databricks Asset Bundles** — Infrastructure-as-code for multi-environment deployment
- **GitHub Actions + OIDC** — Secure CI/CD without long-lived tokens

---

## Deployment

### Automated (Recommended)

Push to `dev` or `main` branch to trigger GitHub Actions workflows:

```bash
git push origin dev      # Deploys to Dev environment
git push origin main     # Deploys to Prod environment
```

### Manual (Databricks CLI)

```bash
cd speech_to_text_asset_bundle

# Validate configuration
databricks bundle validate --target dev

# Deploy to dev
databricks bundle deploy --target dev --var="service_principal_id=<uuid>"

# Deploy to prod
databricks bundle deploy --target prod --var="service_principal_id=<uuid>"
```

---

## Additional Documentation

- **[Databricks Setup](docs/DATABRICKS_SETUP.md)** — Service principal, catalog, and federation policy configuration
- **[GitHub Actions Setup](docs/GITHUB_ACTIONS_SETUP.md)** — GitHub environments, variables, and secrets
- **[Solution Architecture](docs/SOLUTION_ARCHITECTURE.md)** — Technical deep-dive into pipeline design and data flow
- **[Environment Setup Overview](docs/ENVIRONMENT_SETUP.md)** — Quick setup checklist and documentation index
- **[Asset Bundle Details](speech_to_text_asset_bundle/README.md)** — Development workflow, pipeline architecture, troubleshooting
- **[Copilot Agents](docs/copilot-agents.md)** — Custom AI agents available in this repository

### External References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [GitHub OIDC in Databricks](https://docs.databricks.com/dev-tools/auth/provider-github.html)
- [Spark Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/)

---

## License

See [LICENSE](LICENSE) for details.
