# Solution Architecture

**Purpose**: Technical deep-dive into the Speech-to-Text solution architecture, data flow, and implementation details.

**Scope**: Medallion architecture, pipeline design, Unity Catalog integration, and planned extensions.

---

## Architecture Overview

This solution implements a **medallion architecture** (Bronze → Silver → Gold) for processing audio files and extracting text transcriptions using Databricks Lakehouse capabilities.

### Key Components

1. **Unity Catalog Volume** — Stores raw audio files
2. **Spark Declarative Pipeline (SDP)** — Serverless streaming pipeline for data transformations
3. **Auto Loader** — Incremental file ingestion with schema inference
4. **Delta Live Tables** — Bronze and Silver streaming tables
5. **Model Serving** (planned) — Transcription inference endpoint
6. **AI/BI Dashboard** (planned) — Monitoring and analytics
7. **Genie Space** (planned) — Natural language query interface

---

## Data Flow

### 1. Audio Ingestion (Bronze Layer)

**Source**: `/Volumes/speech_to_text/audio/files/`  
**Output**: `bronze_audio_files` (streaming table)

**Implementation**: `src/stt_bundle_audio_etl/transformations/bronze_audio_files.py`

```python
@dp.table(name="bronze_audio_files", cluster_by=["_ingested_date"])
def bronze_audio_files():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .option("pathGlobFilter", "*.{wav,mp3,flac,m4a,ogg,mp4}")
        .load(f"/Volumes/{catalog}/{schema}/files/")
    )
```

**What it does**:
- Auto Loader monitors the Volume for new audio files
- Supported formats: WAV, MP3, FLAC, M4A, OGG, MP4
- Captures file metadata: path, size, modification time, binary content
- Streams records incrementally to the Bronze table

**Schema inference metadata**: Stored at `/Volumes/{catalog}/{schema}/files/_schema_metadata/bronze_audio_files`

---

### 2. Validation & Enrichment (Silver Layer)

**Source**: `bronze_audio_files`  
**Output**: `silver_audio_files` (streaming table)

**Implementation**: `src/stt_bundle_audio_etl/transformations/silver_audio_files.py`

```python
@dp.table(name="silver_audio_files", cluster_by=["_ingested_date", "file_extension"])
def silver_audio_files():
    return (
        spark.readStream.table("bronze_audio_files")
        .withColumn("file_name", regexp_extract(col("path"), r"([^/]+)$", 1))
        .withColumn("file_extension", lower(regexp_extract(col("path"), r"\.([^.]+)$", 1)))
        .filter(col("file_extension").isin(SUPPORTED_EXTENSIONS))
        .filter(col("file_size_bytes") > 0)
        .withColumn("transcription_status", lit("pending"))
    )
```

**What it does**:
- Extracts file name and extension from path
- Filters out unsupported formats
- Removes empty files (size = 0)
- Adds `transcription_status = 'pending'` for downstream processing
- Enriches with audit timestamp `_processed_at`

---

### 3. Transcription (Gold Layer) — TODO

**Planned Architecture**:

1. **Scheduled Job** reads from `silver_audio_files` where `transcription_status = 'pending'`
2. For each record:
   - Loads binary content from Bronze table (via join on `path`)
   - Calls Databricks Model Serving endpoint for speech-to-text inference
   - Receives transcription results (text, timestamps, confidence)
3. Writes results to **`gold_transcriptions`** table
4. Updates `transcription_status = 'completed'` in Silver table

**Model Serving Options**:
- Pre-trained model from Model Marketplace (e.g., Whisper, Wav2Vec2)
- Custom fine-tuned model registered in MLflow Model Registry
- External API endpoint (e.g., Azure Cognitive Services, AWS Transcribe)

---

### 4. Analytics Layer — TODO

**Planned Features**:

#### AI/BI Dashboard
- Transcription volume over time
- Processing latency metrics
- File format distribution
- Error rate monitoring
- Average audio duration vs. transcription time

#### Genie Space
- Natural language queries: "Show me all transcriptions from last week"
- Semantic search: "Find calls mentioning billing issues"
- Aggregations: "What's the average call duration by language?"

---

## Unity Catalog Structure

```
speech_to_text (catalog)
├── audio (schema — dev environment)
│   ├── files (volume — MANAGED)
│   │   ├── [audio files: .wav, .mp3, .flac, .m4a, .ogg, .mp4]
│   │   └── _schema_metadata/
│   │       └── bronze_audio_files/
│   ├── bronze_audio_files (streaming table)
│   ├── silver_audio_files (streaming table)
│   └── gold_transcriptions (table — planned)
│
└── prod (schema — prod environment)
    ├── bronze_audio_files (streaming table)
    ├── silver_audio_files (streaming table)
    └── gold_transcriptions (table — planned)
```

**Note**: The `files` volume is created automatically in the dev environment by the DAB deployment. In prod, volumes must be created manually or added to the bundle configuration.

---

## Pipeline Configuration

### Serverless Compute

The pipeline uses **serverless compute** for automatic scaling:
- No cluster management required
- Scales automatically based on data volume
- Cost-efficient for variable workloads

### Pipeline Parameters

Defined in `resources/stt_bundle_audio_etl.pipeline.yml` and accessed via `spark.conf.get()`:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `catalog` | Unity Catalog name | `speech_to_text` |
| `schema` | Schema within catalog | `audio` (dev), `prod` (prod) |
| `schema_location_base` | Auto Loader metadata location | `/Volumes/speech_to_text/audio/files/_schema_metadata` |

---

## Deployment Modes

### Dev Target

- **Mode**: Development
- **Pipeline Development**: `true` (enables faster iterations, relaxed SLA)
- **Triggers**: Paused (manual start)
- **Deployment Path**: `/Workspace/Shared/.bundle/speech_to_text_asset_bundle/dev`
- **Git Sync**: Enabled (Git folder updated on push to `dev` branch)

### Prod Target

- **Mode**: Production
- **Pipeline Development**: `false` (enforces SLA, optimized performance)
- **Triggers**: Paused (manual start or scheduled)
- **Deployment Path**: `/Workspace/Shared/.bundle/speech_to_text_asset_bundle/prod`
- **Git Sync**: Disabled (uses direct bundle deployment)

---

## Security Considerations

### Authentication

- **GitHub Actions → Databricks**: Uses OIDC federation (no long-lived tokens)
- **Pipeline Execution**: Runs as service principal (`run_as` configuration)
- **Local Development**: Uses Databricks CLI profile authentication

### Permissions Model

The service principal requires:

```sql
-- Catalog level
GRANT USE CATALOG ON CATALOG speech_to_text TO `<service_principal_uuid>`;

-- Schema level
GRANT USE SCHEMA, CREATE TABLE ON SCHEMA speech_to_text.audio TO `<service_principal_uuid>`;
GRANT USE SCHEMA, CREATE TABLE ON SCHEMA speech_to_text.prod TO `<service_principal_uuid>`;

-- Volume level
GRANT READ VOLUME, WRITE VOLUME ON VOLUME speech_to_text.audio.files TO `<service_principal_uuid>`;
```

### Best Practices

- Never commit real workspace URLs or secrets to the repository
- Use GitHub Environments to isolate Dev and Prod configurations
- Require manual approval for production deployments
- Service principal should have minimal required permissions (principle of least privilege)

---

## Performance Considerations

### Auto Loader

- **Schema inference**: Metadata stored separately from source files to avoid permission conflicts
- **File format**: `binaryFile` format reads entire file content into a single column
- **Filtering**: Applied at ingestion time using `pathGlobFilter` to reduce unnecessary processing

### Delta Tables

- **Clustering**: Both Bronze and Silver tables are clustered by `_ingested_date` for efficient time-based queries
- **Partitioning**: Not used (clustering is sufficient for this use case)
- **Streaming**: Append-only writes for continuous ingestion

### Serverless Pipelines

- Automatically scales based on data volume
- No idle cluster costs
- Sub-minute startup time

---

## Monitoring & Observability

### Current Monitoring

- **Pipeline Execution**: Databricks UI → Workflows → Delta Live Tables
- **Table Lineage**: Databricks UI → Data → Catalog → Table → Lineage tab
- **Data Quality**: Built-in expectations (can be added to transformations)

### Planned Monitoring (TODO)

- **Dashboard Metrics**:
  - Files ingested per hour/day
  - Transcription success rate
  - Average processing time
  - Error breakdown by type
- **Alerts**:
  - Pipeline failures
  - Transcription endpoint downtime
  - Data quality violations

---

## Extensibility

### Adding New Transformations

1. Create a new Python file in `src/stt_bundle_audio_etl/transformations/`
2. Define table using `@dp.table` or `@dp.materialized_view`
3. Deploy: `databricks bundle deploy --target dev`
4. Run: `databricks bundle run stt_bundle_audio_etl`

### Integrating with Model Serving

**Example** (planned implementation):

```python
import requests
from pyspark.sql.functions import udf, col

# Define UDF to call model serving endpoint
@udf("string")
def transcribe_audio(audio_bytes):
    # Replace 'your_secret_scope' and 'model_serving_token' with your actual
    # Databricks secret scope and key names configured in your workspace
    token = dbutils.secrets.get(scope="your_secret_scope", key="model_serving_token")
    
    # Replace <workspace> with your actual Databricks workspace hostname
    # (same as DATABRICKS_HOST environment variable)
    response = requests.post(
        "https://<workspace>.cloud.databricks.com/serving-endpoints/whisper-model/invocations",
        headers={"Authorization": f"Bearer {token}"},
        json={"inputs": audio_bytes}
    )
    return response.json()["predictions"][0]

# Apply to Silver records
gold_transcriptions = (
    spark.read.table("silver_audio_files")
    .filter(col("transcription_status") == "pending")
    .withColumn("transcription", transcribe_audio(col("content")))
)
```

---

## References

- [Databricks Spark Declarative Pipelines](https://docs.databricks.com/aws/en/ldp/)
- [Unity Catalog Volumes](https://docs.databricks.com/data-governance/unity-catalog/volumes.html)
- [Auto Loader](https://docs.databricks.com/ingestion/auto-loader/index.html)
- [Databricks Model Serving](https://docs.databricks.com/machine-learning/model-serving/index.html)
- [Back to README](../README.md)
