# Speech To Text With Databricks

[![Databricks](https://img.shields.io/badge/Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white)](https://databricks.com)
[![Whisper Large V3](https://img.shields.io/badge/Whisper_Large_V3-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/research/whisper)
[![LLaMA 3.3 70B](https://img.shields.io/badge/LLaMA_3.3_70B-0467DF?style=for-the-badge&logo=meta&logoColor=white)](https://ai.meta.com/blog/llama-3-3/)
[![MLflow](https://img.shields.io/badge/MLflow-0194E2?style=for-the-badge&logo=mlflow&logoColor=white)](https://mlflow.org)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org)

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
- ✅ **Dashboard** — Databricks AI/BI dashboard for monitoring transcription and NLP results
- ✅ **Genie Space** — Natural language interface for querying the gold layer tables

---

## Quick Start

### Prerequisites

- **Databricks workspace(s) with Unity Catalog enabled**
  - **Two workspaces** (recommended for full CI/CD): one for `dev`, one for `prod` — each target in `databricks.yml` points to a separate workspace, ensuring complete environment isolation
  - **One workspace** (simplified setup): both `dev` and `prod` targets deploy to the same workspace, differentiated only by schema name — suitable for personal projects or demos
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
│   ├── resources/                        # Jobs, pipelines, schemas, volumes, dashboard
│   │   ├── stt_audio_transcription.pipeline.yml  # Bronze + Silver transcription pipeline
│   │   ├── stt_nlp_enrichment.pipeline.yml       # Silver NLP enrichment pipeline
│   │   ├── stt_gold_layer.pipeline.yml           # Gold aggregation pipeline
│   │   ├── stt_dashboard.dashboard.yml           # AI/BI dashboard resource
│   │   ├── stt_genie.job.yml                     # Genie Space setup job
│   │   └── stt_main.job.yml                      # Orchestration job
│   ├── src/                              # Python source code and assets
│   │   ├── stt_audio_transcription/      # Bronze + Silver transcription tables
│   │   ├── stt_nlp_enrichment/           # Silver NLP enrichment tables
│   │   ├── stt_gold_layer/               # Gold detail and aggregate tables
│   │   ├── dashboards/                   # AI/BI dashboard definition (Lakeview JSON)
│   │   ├── stt_genie/                    # Genie Space setup notebook
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

- **`databricks.yml`** — Bundle configuration with `dev` and `prod` targets and all bundle variables
- **`resources/`** — YAML definitions for all pipelines, the AI/BI dashboard, the Genie Space setup job, the orchestration job, schemas, and volumes
- **`src/stt_audio_transcription/`** — Bronze and Silver transcription pipeline tables
- **`src/stt_nlp_enrichment/`** — Silver NLP enrichment tables (two parallel implementations)
- **`src/stt_gold_layer/`** — Gold detail and aggregate tables
- **`src/dashboards/`** — AI/BI Lakeview dashboard definition
- **`src/stt_genie/`** — Notebook that creates/updates the Genie Space via the Databricks SDK
- **`src/stt_nlp_evaluation/`** — MLflow GenAI evaluation notebook
- **`tests/`** — Unit tests for transformations

**For detailed documentation**, see [speech_to_text_asset_bundle/README.md](speech_to_text_asset_bundle/README.md)
**For detailed documentation**, see [speech_to_text_asset_bundle/README.md](speech_to_text_asset_bundle/README.md)

### `/.github/workflows`

GitHub Actions workflows for CI/CD:

- **`sync_git_folder_and_deploy_adb_dev.yml`** — Syncs Git folder and deploys to Dev when code is pushed to `dev` branch
- **`sync_git_folder_and_deploy_adb_prod.yml`** — Deploys asset bundle to Prod when code is pushed to `main` branch

Both workflows use GitHub OIDC for secure, token-less authentication with Databricks.

---

## Solution Details

### Data Flow

```text
/Volumes/speech_to_text/audio/files/     ← audio files (wav, mp3, flac, …)
        │
        │  Auto Loader
        ▼
bronze_audio_files_raw                   ← raw file metadata (Bronze)
        │
        │  ai_query(Whisper Large V3)
        ▼
silver_audio_transcription               ← transcription text (Silver)
        │
        ├────────────────────────────────────────────┐
        │  AI SQL functions                          │  Foundation Model API (ai_query)
        ▼                                            ▼
silver_audio_nlp_ai_func        silver_audio_nlp_ai_query   ← Gold source
        │                                            │
        ├──────────────────┬─────────────────────────┘
                           │
              ┌────────────┴──────────────────────────┐
              ▼                                        ▼
 nlp_quality_evaluation.ipynb          gold_audio_sentiment_analysis  ┐
 (MLflow GenAI evaluation)             gold_audio_daily_stats         ├ (Gold)
                                       gold_audio_sentiment_by_topic  ┘
                                                       │
                                        ┌──────────────┴──────────────┐
                                        ▼                             ▼
                                 AI/BI Dashboard               Genie Space
                             (Speech to Text Analytics)   (natural language queries)
```

All four stages are orchestrated by the `stt_main` job: transcription → NLP enrichment → gold layer update and MLflow evaluation in parallel.

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

# Run the full pipeline (transcription → NLP enrichment → gold layer + evaluation)
databricks bundle run stt_main
```

---

## Additional Documentation

- **[Databricks Setup](docs/DATABRICKS_SETUP.md)** — Service principal, catalog, and federation policy configuration
- **[GitHub Actions Setup](docs/GITHUB_ACTIONS_SETUP.md)** — GitHub environments, variables, and secrets
- **[Solution Architecture](docs/SOLUTION_ARCHITECTURE.md)** — Technical deep-dive into pipeline design and data flow
- **[Environment Setup Overview](docs/ENVIRONMENT_SETUP.md)** — Quick setup checklist and documentation index
- **[Bundle README](speech_to_text_asset_bundle/README.md)** — Pipeline architecture, data schemas, and configuration reference
- **[Copilot Agents](docs/copilot-agents.md)** — Custom AI agents available in this repository

### External References

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [GitHub OIDC in Databricks](https://docs.databricks.com/dev-tools/auth/provider-github.html)
- [Spark Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/)

---

## License

See [LICENSE](LICENSE) for details.
