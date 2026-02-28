# Speech-to-Text Databricks Asset Bundle

## Overview

This Databricks Asset Bundle implements an end-to-end speech-to-text processing solution using the Databricks Lakehouse platform. The solution ingests audio files from contact center recordings, tracks them through a Bronze → Silver medallion pipeline, and prepares the data for downstream transcription and analysis.

### Data Source

The audio files used in this solution are sourced from:

- **Dataset**: [AxonData English Contact Center Audio Dataset](https://huggingface.co/datasets/AxonData/english-contact-center-audio-dataset/tree/main)
- **Storage**: Files have been downloaded from HuggingFace and uploaded to the Databricks **`files` volume** in the catalog

This dataset contains English language audio recordings from contact center scenarios, providing realistic use cases for speech-to-text analysis.

---

## Solution Architecture

The solution follows a medallion architecture to process audio files through multiple stages:

### Processing Flow

1. **Data Ingestion — Bronze** ✅
   - Audio files stored in `/Volumes/{catalog}/{schema}/files/` are continuously tracked via Auto Loader
   - File metadata (path, size, modification time) is captured as a streaming Delta table: `bronze_audio_files_raw`
   - Supported formats: `wav`, `mp3`, `flac`, `m4a`, `ogg`, `mp4`

2. **Transcription — Silver** ✅
   - Bronze records are transcribed via the Whisper Large V3 Model Serving endpoint using `ai_query()`
   - Output: `silver_audio_transcription` with `transcription_text` per file

3. **NLP Enrichment — Silver** ✅
   - Each transcription is enriched with sentiment, summary, named entities, topic classification, and Italian translation
   - Two parallel implementations are produced for quality comparison:
     - `silver_audio_nlp_ai_func` — Databricks built-in AI SQL functions
     - `silver_audio_nlp_ai_query` — Foundation Model API via `ai_query()`

4. **Gold Layer — Analysis-Ready Tables** ✅
   - Joins NLP enrichment with transcription metadata, flattens entity structs, adds derived metrics
   - Three output tables for dashboards and ad-hoc analysis:
     - `gold_audio_sentiment_analysis` — full detail table (one row per transcription)
     - `gold_audio_daily_stats` — daily aggregation by date × topic × sentiment
     - `gold_audio_sentiment_by_topic` — sentiment distribution cross-tab per business domain

5. **NLP Quality Evaluation** ✅
   - MLflow GenAI evaluation notebook compares both silver NLP implementations with deterministic validators and LLM judges
   - Results logged to `/Shared/nlp-quality-evaluation` experiment

---

## Project Structure

```text
speech_to_text_asset_bundle/
├── databricks.yml                                  # Bundle config: variables, targets (dev/prod)
├── pyproject.toml                                  # Python project config and dev dependencies
├── resources/
│   ├── stt_audio_transcription.pipeline.yml        # Bronze + Silver transcription pipeline
│   ├── stt_nlp_enrichment.pipeline.yml             # Silver NLP enrichment pipeline
│   ├── stt_gold_layer.pipeline.yml                 # Gold aggregation pipeline
│   └── stt_main.job.yml                            # Orchestration job
└── src/
    ├── stt_audio_transcription/transformations/
    │   ├── bronze_audio_files.py                   # Auto Loader → bronze_audio_files_raw
    │   └── silver_audio_files.py                   # Whisper → silver_audio_transcription
    ├── stt_nlp_enrichment/transformations/
    │   ├── silver_audio_nlp_ai_func.py             # NLP via AI SQL functions
    │   └── silver_audio_nlp_ai_query.py            # NLP via Foundation Model (ai_query)
    ├── stt_gold_layer/transformations/
    │   ├── gold_audio_sentiment_analysis.py        # Gold detail table (flattened entities, metrics)
    │   └── gold_aggregates.py                      # gold_audio_daily_stats + gold_audio_sentiment_by_topic
    └── stt_nlp_evaluation/evaluation/
        └── nlp_quality_evaluation.ipynb            # MLflow GenAI evaluation notebook
```

### `/resources/`

Contains YAML definitions for all Databricks resources:

- **`stt_audio_transcription.pipeline.yml`** — Serverless SDP pipeline: Bronze (Auto Loader) → Silver (Whisper transcription via `ai_query()`).
- **`stt_nlp_enrichment.pipeline.yml`** — Serverless SDP pipeline: enriches `silver_audio_transcription` with sentiment, summary, entities, topic, and translation. Produces two implementations for quality comparison.
- **`stt_gold_layer.pipeline.yml`** — Serverless SDP pipeline: builds analysis-ready gold tables from the NLP-enriched silver data. Flattens entity structs, adds derived metrics, and produces daily and topic/sentiment aggregations.
- **`stt_main.job.yml`** — Orchestration job that chains all three pipelines in sequence, then runs the MLflow evaluation notebook in parallel with the gold layer update.

### `/src/stt_gold_layer/transformations/`

- **`gold_audio_sentiment_analysis.py`** — Gold detail table. Joins `silver_audio_nlp_ai_query` (selected for its richer, more contextual summaries) with `silver_audio_transcription`, normalises `sentiment` and `topic` to lowercase, flattens the `entities` STRUCT into individual columns (`entities_person`, `entities_organization`, `entities_location`, `entities_date`, `entities_amount`), and derives `transcription_length` and `transcription_word_count`. Clustered by `_ingested_date`, `topic`, `sentiment`.
- **`gold_aggregates.py`** — Two aggregate tables:
  - `gold_audio_daily_stats` — counts, unique files, avg length/word count grouped by `_ingested_date × topic × sentiment`
  - `gold_audio_sentiment_by_topic` — pivot table with topics as rows and sentiment labels as columns (counts per cell)

#### Auto Loader Schema Metadata

Schema inference metadata for Auto Loader is stored at:

```text
/Volumes/{catalog}/{schema}/files/_schema_metadata/bronze_audio_files
```

This path is configured via the `schema_location_base` pipeline parameter and is kept separate from the source audio files to avoid permission conflicts.

---

## Configuration & Deployment

### Prerequisites

Before deploying, ensure you have:

1. Databricks workspace access with appropriate permissions
2. Databricks CLI installed and configured
3. Required catalog created: `speech_to_text` (must be created manually in Databricks)
4. Service principal configured (for production deployments via GitHub Actions)

### Environment Targets

The bundle supports two deployment targets:

#### **Dev Target** (Default)

- **Catalog**: `speech_to_text`
- **Schema**: `default`
- **Mode**: Development (pipeline runs in development mode)
- **Deployment path**: `~/Shared/.bundle/speech_to_text_asset_bundle/dev`
- **Resources created**: dev schema + `files` managed volume

#### **Prod Target**

- **Catalog**: `speech_to_text`
- **Schema**: `prod`
- **Mode**: Production
- **Deployment path**: `~/Shared/.bundle/speech_to_text_asset_bundle/prod`
- **Resources created**: prod schema

### Variables

| Variable                | Description                                                                              | Default                                  |
|-------------------------|------------------------------------------------------------------------------------------|------------------------------------------|
| `catalog`               | Unity Catalog name                                                                       | `speech_to_text`                         |
| `schema`                | Schema within the catalog                                                                | `audio` (dev) / `prod` (prod)            |
| `service_principal_id`  | Application ID of the service principal                                                  | (required for deployments)               |
| `stt_model`             | Whisper Model Serving endpoint used for audio transcription via `ai_query()`             | `stt-whisper-large-v3`                   |
| `nlp_model`             | Foundation Model API endpoint used for NLP tasks via `ai_query()`                        | `databricks-meta-llama-3-3-70b-instruct` |
| `gold_nlp_source_table` | Silver NLP table used as gold layer source (`silver_audio_nlp_ai_query` or `_ai_func`)   | `silver_audio_nlp_ai_query`              |

### Deployment

```bash
# Validate the bundle configuration
databricks bundle validate

# Deploy to dev (default)
databricks bundle deploy --var="service_principal_id=<SP_APP_ID>"

# Run the full pipeline (transcription → NLP enrichment → gold layer + evaluation)
databricks bundle run stt_main

# Deploy to production
databricks bundle deploy --target prod --var="service_principal_id=<SP_APP_ID>"
```

#### Using a Local Configuration File

Create a `databricks.yml.local` file (git-ignored) with environment-specific values:

```yaml
targets:
  dev:
    variables:
      service_principal_id: "your-service-principal-uuid"
  prod:
    variables:
      service_principal_id: "your-service-principal-uuid"
```

See `.databricks.yml.example` for a complete example.

#### GitHub Actions (Recommended for Production)

- **Dev**: Automatically syncs code to Databricks Git folder on push to `dev` branch
- **Prod**: Automatically deploys the asset bundle on push to `main` branch

See the root [README.md](../README.md) for GitHub Actions setup instructions.

---

## Development Workflow

### Local Development

1. **Install Dependencies**

   ```bash
   pip install -e ".[dev]"
   ```

2. **Run Tests**

   ```bash
   pytest tests/
   ```

3. **Linting & Code Quality**

   ```bash
   ruff check .
   ruff check --fix .
   ```

### Working with the Pipeline

Transformation files are in `src/stt_audio_ingestion/transformations/`. Each file uses the modern Spark Declarative Pipelines (SDP) API:

```python
from pyspark import pipelines as dp

@dp.table(name="my_table", cluster_by=["date_column"])
def my_table():
    return spark.readStream.table("upstream_table")
```

**Add a new transformation:**

1. Create a new `.py` file in `transformations/`
2. Use `@dp.table()` or `@dp.materialized_view()` decorators
3. Access pipeline parameters with `spark.conf.get("catalog")` etc.
4. Deploy and run:

   ```bash
   databricks bundle deploy
   databricks bundle run stt_audio_ingestion
   ```

**View the pipeline in Databricks:**

- Navigate to **Workflows** > **Delta Live Tables**
- Find the pipeline: `stt_audio_ingestion` (with dev prefix in development mode)

---

## Data Storage & Unity Catalog

### Catalog Structure

```text
speech_to_text (catalog)
├── audio (schema — dev environment)
│   ├── files (volume — managed)
│   │   ├── [audio files: .wav, .mp3, .flac, .m4a, .ogg, .mp4]
│   │   └── _schema_metadata/              <- Auto Loader schema inference metadata
│   ├── bronze_audio_files_raw             <- stt_audio_transcription pipeline
│   ├── silver_audio_transcription         <- stt_audio_transcription pipeline
│   ├── silver_audio_nlp_ai_func           <- stt_nlp_enrichment pipeline
│   ├── silver_audio_nlp_ai_query          <- stt_nlp_enrichment pipeline
│   ├── gold_audio_sentiment_analysis      <- stt_gold_layer pipeline
│   ├── gold_audio_daily_stats             <- stt_gold_layer pipeline
│   └── gold_audio_sentiment_by_topic      <- stt_gold_layer pipeline
└── prod (schema — prod environment)
    └── [same tables, prod data]
```

### Volumes

The **`files` volume** stores:

- Raw audio files downloaded from HuggingFace
- Auto Loader schema metadata (under `_schema_metadata/`)
- Volume type: MANAGED

### Pipeline Tables

| Table                            | Layer  | Pipeline                  | Description                                                       |
|----------------------------------|--------|---------------------------|-------------------------------------------------------------------|
| `bronze_audio_files_raw`         | Bronze | stt_audio_transcription   | Raw audio file metadata from Auto Loader, append-only             |
| `silver_audio_transcription`     | Silver | stt_audio_transcription   | Transcription text produced by Whisper via `ai_query()`           |
| `silver_audio_nlp_ai_func`       | Silver | stt_nlp_enrichment        | NLP enrichment via Databricks AI SQL functions                    |
| `silver_audio_nlp_ai_query`      | Silver | stt_nlp_enrichment        | NLP enrichment via Foundation Model API (`ai_query()`)            |
| `gold_audio_sentiment_analysis`  | Gold   | stt_gold_layer            | Full detail: joined NLP + metadata, flattened entities, metrics   |
| `gold_audio_daily_stats`         | Gold   | stt_gold_layer            | Daily aggregation by date × topic × sentiment                     |
| `gold_audio_sentiment_by_topic`  | Gold   | stt_gold_layer            | Sentiment cross-tab per business domain (pivot table)             |

---

## Security & Best Practices

### Authentication

- **Dev**: Uses service principal for automated deployments
- **Prod**: Requires service principal with restricted permissions
- **Local**: Uses Databricks CLI authentication profiles

### Permissions

Ensure the service principal has:

- `USE CATALOG` on `speech_to_text` catalog
- `USE SCHEMA` on target schema (`default` or `prod`)
- `CREATE TABLE` for pipeline table outputs
- `READ VOLUME` and `WRITE VOLUME` on the `files` volume

### Security Notes

- Never commit secrets or credentials to the repository
- Use GitHub Environments for managing secrets in CI/CD
- Service principal federation with GitHub OIDC eliminates long-lived tokens

---

## Troubleshooting

### Bundle Validation Fails

**Solution:**

1. Check YAML syntax in `databricks.yml` and resource files
2. Ensure all required variables are defined
3. Verify catalog and schema exist in the target workspace
4. Run `databricks bundle validate --target <target>` for a specific target

### Pipeline Fails to Start

**Solution:**

1. Verify the catalog and schema exist and the service principal has permissions
2. Check that the `files` volume exists and audio files are present
3. Review pipeline logs in **Workflows > Delta Live Tables**
4. Confirm transformation files have no syntax errors

### Auto Loader: Schema Location Errors

**Solution:**

1. Ensure the `_schema_metadata` folder is not inside the audio file source path
2. Verify `schema_location_base` is set correctly in `stt_audio_ingestion.pipeline.yml`
3. The service principal needs `WRITE VOLUME` permission on the `files` volume

### Volume Access Issues

**Solution:**

1. Verify the volume exists: `/Volumes/{catalog}/{schema}/files/`
2. Ensure the service principal has `READ VOLUME` permission
3. For dev environment, confirm the volume is created during `databricks bundle deploy`

---

## Additional Resources

- **Root README**: [../README.md](../README.md) — Overall project setup and CI/CD configuration
- **Spark Declarative Pipelines**: [Databricks SDP Documentation](https://docs.databricks.com/aws/en/ldp/)
- **Asset Bundles Guide**: [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- **Unity Catalog**: [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)

---

## Next Steps

1. ✅ **Bronze & Silver Transcription** — Auto Loader ingests audio, Whisper transcribes via Model Serving
2. ✅ **NLP Enrichment** — Sentiment, summary, entities, topic, and translation (two parallel implementations)
3. ✅ **Gold Layer** — Analysis-ready detail and aggregate tables built from the enriched silver data
4. ✅ **NLP Quality Evaluation** — MLflow GenAI evaluation comparing both NLP implementations
5. 📋 **Dashboard** — Build an AI/BI dashboard on top of the gold layer tables
6. 📋 **Genie Space** — Natural language interface for querying `gold_audio_sentiment_analysis`
