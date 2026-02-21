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
   - File metadata (path, size, modification time) is captured as a streaming Delta table
   - Supported formats: `wav`, `mp3`, `flac`, `m4a`, `ogg`, `mp4`

2. **Data Validation — Silver** ✅
   - Bronze records are validated and enriched
   - File name and extension are extracted from the path
   - Invalid or empty files are filtered out
   - Each record is assigned a `transcription_status = 'pending'` to be updated by the transcription job

3. **Speech-to-Text Conversion** (Planned/TODO)
   - A downstream job reads `silver_audio_files` and calls the model serving endpoint
   - Transcription results (text, timestamps, confidence scores) are written back to a Gold table

4. **Data Quality & Monitoring** (Planned/TODO)
   - Quality checks on transcription accuracy
   - Monitoring of processing times and success rates

---

## Project Structure

```text
speech_to_text_asset_bundle/
├── databricks.yml                          # Bundle config: variables, targets (dev/prod)
├── pyproject.toml                          # Python project config and dev dependencies
├── resources/
│   └── stt_bundle_audio_etl.pipeline.yml  # Spark Declarative Pipeline definition
└── src/
    ├── sample_notebook.ipynb               # Interactive exploration notebook
    └── stt_bundle_audio_etl/
        ├── README.md
        └── transformations/
            ├── bronze_audio_files.py       # Bronze: Auto Loader ingest from Volume
            └── silver_audio_files.py       # Silver: validation and enrichment
```

### `/resources/`

Contains YAML definitions for all Databricks resources:

- **`stt_bundle_audio_etl.pipeline.yml`**: Spark Declarative Pipeline (serverless) that runs the Bronze → Silver transformations. Pipeline-level parameters (`catalog`, `schema`, `schema_location_base`) are passed to Python code via `spark.conf.get()`.

### `/src/stt_bundle_audio_etl/transformations/`

Python files that define the pipeline tables using the modern `pyspark.pipelines` API (`@dp.table`):

- **`bronze_audio_files.py`** — Bronze layer. Streams audio file metadata from `/Volumes/{catalog}/{schema}/files/` using Auto Loader. Captures `path`, `file_size_bytes`, `modificationTime`, `_ingested_at`, `_ingested_date`. Binary content is excluded to keep the table size manageable.
- **`silver_audio_files.py`** — Silver layer. Reads from `bronze_audio_files`, extracts `file_name` and `file_extension`, filters unsupported formats and empty files, and adds `transcription_status = 'pending'`.

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

| Variable               | Description                              | Default                          |
|------------------------|------------------------------------------|----------------------------------|
| `catalog`              | Unity Catalog name                       | `speech_to_text`                 |
| `schema`               | Schema within the catalog                | `default` (dev) / `prod` (prod)  |
| `service_principal_id` | Application ID of the service principal  | (required for deployments)       |

### Deployment

```bash
# Validate the bundle configuration
databricks bundle validate

# Deploy to dev (default)
databricks bundle deploy

# Run the pipeline
databricks bundle run stt_bundle_audio_etl

# Deploy to production
databricks bundle deploy --target prod
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

Transformation files are in `src/stt_bundle_audio_etl/transformations/`. Each file uses the modern Spark Declarative Pipelines (SDP) API:

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
   databricks bundle run stt_bundle_audio_etl
   ```

**View the pipeline in Databricks:**

- Navigate to **Workflows** > **Delta Live Tables**
- Find the pipeline: `stt_bundle_audio_etl` (with dev prefix in development mode)

---

## Data Storage & Unity Catalog

### Catalog Structure

```text
speech_to_text (catalog)
├── default (schema — dev environment)
│   └── files (volume — managed)
│       ├── [audio files: .wav, .mp3, .flac, .m4a, .ogg, .mp4]
│       └── _schema_metadata/          <- Auto Loader schema inference metadata
│           └── bronze_audio_files/
├── bronze_audio_files (streaming table)   <- created by pipeline
├── silver_audio_files (streaming table)   <- created by pipeline
└── prod (schema — prod environment)
```

### Volumes

The **`files` volume** stores:

- Raw audio files downloaded from HuggingFace
- Auto Loader schema metadata (under `_schema_metadata/`)
- Volume type: MANAGED

### Pipeline Tables

| Table                  | Layer  | Type            | Description                                        |
|------------------------|--------|-----------------|----------------------------------------------------|
| `bronze_audio_files`   | Bronze | Streaming Table | Raw audio file metadata, append-only               |
| `silver_audio_files`   | Silver | Streaming Table | Validated records, ready for transcription         |

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
2. Verify `schema_location_base` is set correctly in `stt_bundle_audio_etl.pipeline.yml`
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

1. ✅ **Deploy to Dev** — `databricks bundle deploy --target dev`
2. ✅ **Bronze & Silver Pipeline** — Audio file metadata ingested and validated
3. 📋 **Upload Audio Files** — Place HuggingFace dataset files in `/Volumes/speech_to_text/default/files/`
4. 📋 **Run Pipeline** — `databricks bundle run stt_bundle_audio_etl`
5. 📋 **Implement Transcription Job** — Downstream job reads `silver_audio_files`, calls model serving endpoint, writes results to Gold table
6. 📋 **Deploy to Prod** — `databricks bundle deploy --target prod`
