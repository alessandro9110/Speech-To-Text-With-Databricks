# stt_audio_ingestion — Audio Ingestion Pipeline

This folder contains the source code for the `stt_audio_ingestion` Spark Declarative Pipeline (SDP).
The pipeline reads raw audio files from a Unity Catalog Volume, transcribes them using the Whisper
Large V3 model served via Databricks Model Serving, and persists the results as Delta tables following
a Bronze → Silver medallion architecture.

---

## How the configuration flows from `databricks.yml`

The entire solution is driven by a single source of truth: the bundle variables declared in
`databricks.yml`. Understanding this file is the starting point for understanding how each
component is wired together.

### 1. Bundle variables (`databricks.yml` › `variables`)

```yaml
variables:
  catalog:
    default: speech_to_text          # Unity Catalog catalog name
  schema:
    default: audio                   # Schema inside the catalog
  service_principal_id:              # SP used by run_as in both targets
  stt_model:
    default: stt-whisper-large-v3    # Name of the Whisper Model Serving endpoint
```

`stt_model` is the key variable that connects three separate resources:

- the **Model Serving endpoint** (its name is `${var.stt_model}`)
- the **pipeline configuration** (passed as `stt_model` spark conf)
- the **AI Gateway inference table** (prefix is `inference_${var.stt_model}`)

Changing `stt_model` in one place automatically propagates to all three.

### 2. Model Serving endpoint (`databricks.yml` › top-level `resources`)

```yaml
resources:
  model_serving_endpoints:
    stt_whisper_endpoint:
      name: "${var.stt_model}"          # endpoint name = stt-whisper-large-v3
      config:
        served_entities:
          - entity_name: system.ai.whisper_large_v3
            entity_version: "3"
            workload_type: GPU_SMALL
            scale_to_zero_enabled: true
      ai_gateway:
        inference_table_config:
          enabled: true
          table_name_prefix: inference_${var.stt_model}
```

This endpoint is defined at the top level (outside any target) so it is shared across dev and prod.
It serves Whisper Large V3 from the Databricks-managed `system.ai` catalog — no model registration
is required. The AI Gateway writes every request and response to a Delta table for auditing and
quality monitoring.

### 3. Pipeline definition (`resources/stt_audio_ingestion.pipeline.yml`)

```yaml
resources:
  pipelines:
    stt_audio_ingestion:
      name: stt_audio_ingestion
      serverless: true
      configuration:
        catalog: ${var.catalog}
        schema: ${var.schema}
        schema_location_base: /Volumes/${var.catalog}/${var.schema}/files/_schema_metadata
        stt_model: ${var.stt_model}    # injected into Python via spark.conf.get()
      libraries:
        - glob:
            include: ../src/stt_audio_ingestion/transformations/**
```

The `configuration` block is the bridge between bundle variables and Python code. Every key-value
pair here becomes a Spark conf accessible inside the transformation files via `spark.conf.get()`.

### 4. Target overrides (`databricks.yml` › `targets`)

Each target (dev / prod) can override the pipeline configuration:

| Setting | dev | prod |
| --- | --- | --- |
| `pipelines_development` preset | `true` | `false` |
| `catalog` | `speech_to_text` | `speech_to_text` |
| `schema` | `audio` | `prod` |
| `stt_model` | `stt-whisper-large-v3` (default) | `stt-whisper-large-v3` (default) |
| Unity Catalog schema | created by bundle | created by bundle |
| Unity Catalog volume | created by bundle | not managed (already exists) |

In development mode (`pipelines_development: true`) Databricks adds a user-specific isolation
prefix to table names so that developers do not interfere with each other.

---

## Pipeline steps

The pipeline runs two streaming tables in sequence.

### Step 1 — Bronze: `bronze_audio_files_raw`

**File:** `transformations/bronze_audio_files.py`

```text
/Volumes/{catalog}/{schema}/files/
        │
        │  Auto Loader (cloudFiles, binaryFile format)
        │  pathGlobFilter: *.{wav,mp3,flac,m4a,ogg,mp4}
        ▼
  bronze_audio_files_raw  (streaming Delta table)
```

**What it does:**

Auto Loader watches the Unity Catalog Volume at `/Volumes/{catalog}/{schema}/files/` for new audio
files. Whenever a file is dropped into the volume, Auto Loader picks it up incrementally without
reprocessing files it has already ingested.

Each row in the output table represents one audio file and contains:

| Column | Type | Description |
| --- | --- | --- |
| `path` | STRING | Full path of the file inside the volume |
| `content` | BINARY | Raw bytes of the entire audio file |
| `modificationTime` | TIMESTAMP | Last-modified timestamp from the volume |
| `file_size_bytes` | LONG | Size of the file in bytes |
| `_ingested_at` | TIMESTAMP | Timestamp when Auto Loader picked up the file |
| `_ingested_date` | DATE | Date partition derived from `_ingested_at` |

The table is clustered on `_ingested_date` to speed up date-range queries.

The `content` (BINARY) column is the raw payload that is forwarded to the Whisper model in the
next step. Auto Loader stores its schema inference metadata under
`schema_location_base/bronze_audio_files_raw` to track which files have already been processed.

### Step 2 — Silver: `silver_audio_transcription`

**File:** `transformations/silver_audio_files.py`

```text
  bronze_audio_files_raw
        │
        │  filter: supported extensions only (wav, mp3, flac, m4a, ogg, mp4)
        │  filter: file_size_bytes > 0
        │
        │  ai_query(stt_model, content)   ← calls Whisper endpoint
        ▼
  silver_audio_transcription  (streaming Delta table)
```

**What it does:**

Reads `bronze_audio_files_raw` as a streaming source and applies three transformations:

1. **Extract metadata** — derives `file_name` and `file_extension` from the `path` column using
   regex, so downstream consumers can filter by format without parsing paths themselves.

2. **Filter** — drops rows with unsupported extensions or empty content (`file_size_bytes = 0`)
   before sending data to the model endpoint, avoiding unnecessary inference calls.

3. **Transcription via `ai_query()`** — calls the Whisper Model Serving endpoint using the SQL
   `ai_query()` function invoked through PySpark `selectExpr()`. The endpoint name is read at
   pipeline startup from `spark.conf.get("stt_model")`, which was injected by the bundle via the
   `configuration` block in `stt_audio_ingestion.pipeline.yml`.

   ```python
   stt_model = spark.conf.get("stt_model")

   .selectExpr(
       ...
       f"ai_query('{stt_model}', content) AS transcription_text",
       ...
   )
   ```

Each row in the output table contains:

| Column | Type | Description |
| --- | --- | --- |
| `path` | STRING | Full path of the source audio file |
| `file_name` | STRING | File name extracted from path |
| `file_extension` | STRING | Lowercase extension (wav, mp3, …) |
| `file_size_bytes` | LONG | Size of the audio file |
| `modificationTime` | TIMESTAMP | Last-modified timestamp from the volume |
| `transcription_text` | STRING | Text returned by the Whisper endpoint |
| `_transcribed_at` | TIMESTAMP | Timestamp when transcription was produced |
| `_ingested_at` | TIMESTAMP | Timestamp from the bronze layer |
| `_ingested_date` | DATE | Date partition from the bronze layer |

The table is clustered on `(_ingested_date, file_extension)`.

---

## Directory structure

```text
stt_audio_ingestion/
├── README.md                          # this file
└── transformations/
    ├── bronze_audio_files.py          # Step 1: Auto Loader ingest → bronze_audio_files_raw
    └── silver_audio_files.py          # Step 2: filter + transcribe → silver_audio_transcription
```

---

## Deploying and running

```bash
# Deploy to dev (default target)
databricks bundle deploy --var="service_principal_id=<SP_APP_ID>"

# Deploy to prod
databricks bundle deploy --target prod --var="service_principal_id=<SP_APP_ID>"

# Run the pipeline manually
databricks bundle run stt_audio_ingestion
```
