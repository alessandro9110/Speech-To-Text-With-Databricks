# Speech To Text With Databricks

A speech-to-text processing solution using **Databricks Asset Bundles** for infrastructure-as-code and **GitHub Actions** for automated CI/CD deployment.

---

## Overview

This repository implements an end-to-end speech-to-text (STT) pipeline on Databricks:

- Audio files are ingested from Unity Catalog Volumes using Auto Loader
- Data flows through a Bronze → Silver medallion architecture (Spark Declarative Pipelines)
- Transcription is handled by Whisper Large V3 via a Databricks Model Serving endpoint
- NLP enrichment (sentiment, summary, entities, topic, translation) is applied to every transcription
- Both NLP implementations (AI SQL functions and Foundation Model API) are evaluated with MLflow
- Deployment is automated via GitHub Actions with OIDC authentication
- Infrastructure is managed via Databricks Asset Bundles (DAB)

### What's Implemented

- ✅ **Audio Ingestion & Transcription** — Auto Loader picks up audio files and Whisper transcribes them
- ✅ **NLP Enrichment** — Sentiment, summary, entities, topic, and translation via two parallel implementations
- ✅ **MLflow Evaluation** — Side-by-side quality comparison of AI SQL functions vs Foundation Model API
- ✅ **Automated CI/CD** — GitHub Actions deploy to Dev and Prod environments
- ✅ **Infrastructure as Code** — Databricks Asset Bundle with dev/prod targets

### TODO

- [ ] **Dashboard** — Databricks AI/BI dashboard for monitoring transcription and NLP results
- [ ] **Genie Space** — Natural language interface for querying transcription and enrichment data

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

```text
Speech-To-Text-With-Databricks/
├── speech_to_text_asset_bundle/          # Databricks Asset Bundle (DAB)
│   ├── databricks.yml                    # Bundle config: variables, targets (dev/prod)
│   ├── resources/                        # Jobs, pipelines, schemas, volumes
│   │   ├── stt_audio_transcription.pipeline.yml
│   │   ├── stt_nlp_enrichment.pipeline.yml
│   │   └── stt_main.job.yml
│   ├── src/                              # Python source code
│   │   ├── stt_audio_transcription/      # Bronze + Silver transcription tables
│   │   ├── stt_nlp_enrichment/           # Silver NLP enrichment tables
│   │   └── stt_nlp_evaluation/           # MLflow quality evaluation notebook
│   ├── tests/                            # Unit and integration tests
│   └── pyproject.toml                    # Python dependencies and tooling
├── .github/workflows/                    # CI/CD automation
│   ├── sync_git_folder_and_deploy_adb_dev.yml   # Deploy to Dev on push to 'dev'
│   └── sync_git_folder_and_deploy_adb_prod.yml  # Deploy to Prod on push to 'main'
├── docs/                                 # Additional documentation
└── README.md                             # This file
```

### `/speech_to_text_asset_bundle`

The core Databricks solution. Contains:

- **`databricks.yml`** — Bundle configuration with `dev` and `prod` targets, bundle variables (catalog, schema, stt_model, nlp_model)
- **`resources/`** — YAML definitions for the two pipelines (`stt_audio_transcription`, `stt_nlp_enrichment`), the orchestration job (`stt_main`), schemas, and volumes
- **`src/stt_audio_transcription/transformations/`** — Bronze (Auto Loader) and Silver (Whisper transcription) pipeline tables
- **`src/stt_nlp_enrichment/transformations/`** — Two parallel Silver NLP implementations: AI SQL functions and Foundation Model API
- **`src/stt_nlp_evaluation/evaluation/`** — MLflow GenAI evaluation notebook comparing both NLP implementations
- **`tests/`** — Unit tests for transformations

**For detailed documentation**, see [speech_to_text_asset_bundle/src/STT_README.md](speech_to_text_asset_bundle/src/STT_README.md)

### `/.github/workflows`

GitHub Actions workflows for CI/CD:

- **`sync_git_folder_and_deploy_adb_dev.yml`** — Syncs Git folder and deploys to Dev when code is pushed to `dev` branch
- **`sync_git_folder_and_deploy_adb_prod.yml`** — Deploys asset bundle to Prod when code is pushed to `main` branch

Both workflows use GitHub OIDC for secure, token-less authentication with Databricks.

---

## Solution Details

### Data Flow

```text
/Volumes/speech_to_text/audio/files/     ← audio files uploaded here
        │
        │  Auto Loader (bronze_audio_files_raw)
        ▼
bronze_audio_files_raw                   ← raw binary + metadata
        │
        │  ai_query(Whisper endpoint)
        ▼
silver_audio_transcription               ← transcription text
        │
        ├────────────────────────────────────────────┐
        │  AI SQL functions                          │  Foundation Model (ai_query)
        ▼                                            ▼
silver_audio_nlp_ai_func            silver_audio_nlp_ai_query
        │                                            │
        └──────────────────┬─────────────────────────┘
                           ▼
              nlp_quality_evaluation.ipynb
              (MLflow GenAI evaluation)
```

All three stages are orchestrated by the `stt_main` job, which runs them in sequence on a triggered (on-demand or scheduled) basis.

### Technologies

- **Spark Declarative Pipelines (SDP)** — Serverless streaming pipelines with `@dlt.table` decorators
- **Auto Loader** — Incremental ingestion from Unity Catalog Volumes
- **Whisper Large V3** — Foundation Model for audio transcription via Model Serving endpoint
- **Databricks AI SQL functions** — Built-in `ai_analyze_sentiment`, `ai_summarize`, `ai_extract`, `ai_classify`, `ai_translate`
- **Foundation Model API** — `databricks-meta-llama-3-3-70b-instruct` via `ai_query()` for NLP tasks
- **MLflow GenAI evaluation** — Side-by-side quality scoring with deterministic validators and LLM judges
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

# Run the full pipeline (transcription → NLP enrichment → evaluation)
databricks bundle run stt_main
```

---

## Additional Documentation

- **[Databricks Setup](docs/DATABRICKS_SETUP.md)** — Service principal, catalog, and federation policy configuration
- **[GitHub Actions Setup](docs/GITHUB_ACTIONS_SETUP.md)** — GitHub environments, variables, and secrets
- **[Solution Architecture](docs/SOLUTION_ARCHITECTURE.md)** — Technical deep-dive into pipeline design and data flow
- **[Environment Setup Overview](docs/ENVIRONMENT_SETUP.md)** — Quick setup checklist and documentation index
- **[Source Code & Architecture](speech_to_text_asset_bundle/src/STT_README.md)** — Pipeline architecture, data schemas, and configuration reference
- **[Copilot Agents](docs/copilot-agents.md)** — Custom AI agents available in this repository

### External References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [GitHub OIDC in Databricks](https://docs.databricks.com/dev-tools/auth/provider-github.html)
- [Spark Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/)

---

## License

See [LICENSE](LICENSE) for details.
