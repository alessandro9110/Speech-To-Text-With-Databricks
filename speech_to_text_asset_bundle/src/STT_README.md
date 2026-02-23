# Speech-To-Text with Databricks — Pipeline Source Code

This folder contains the source code for the two Spark Declarative Pipelines (SDP) that make up
the Speech-To-Text solution:

| Pipeline | Layer | Purpose |
| --- | --- | --- |
| `stt_audio_ingestion` | Bronze → Silver | Ingest audio files from a Unity Catalog Volume and transcribe them via Whisper |
| `stt_nlp_analysis` | Gold | Enrich transcriptions with NLP using Databricks AI SQL functions |

The pipelines are **intentionally decoupled**: each can be deployed, scaled, and scheduled
independently without affecting the other.

## Naming convention

The naming convention applied across this project separates **what** from **how**:

- **Pipeline folder / resource key** (`stt_audio_ingestion`, `stt_nlp_analysis`) — describes the **business capability** of the pipeline, independent of the technology used to implement it.
- **Transformation file name** (`bronze_audio_files.py`, `silver_audio_files.py`, `gold_audio_ai_func_nlp.py`) — describes **how** the transformation is implemented. The `ai_func` segment in `gold_audio_ai_func_nlp.py` signals that the Gold layer is built on Databricks AI SQL functions. The `ai_query` segment in the experimental counterpart signals an external model endpoint. If the implementation were swapped, only the file name and content change — the pipeline name stays the same.
- **`_experimental/` folder** — scripts here are **not picked up** by the pipeline library glob (which covers `transformations/**` only). They serve as ready-to-activate alternative implementations. To activate one, move it into `transformations/` and remove or rename the current active file.

---

## Full medallion architecture

```text
/Volumes/{catalog}/{schema}/files/      (audio files dropped here)
        │
        │  Auto Loader — cloudFiles, binaryFile format
        ▼
bronze_audio_files_raw                  (raw binary content + metadata)
        │
        │  filter extensions + size
        │  ai_query(stt_model, content) ← Whisper endpoint
        ▼
silver_audio_transcription              (transcription text)
        │
        │  filter NULL/empty text
        │  ai_analyze_sentiment()
        │  ai_summarize()
        │  ai_extract()
        │  ai_classify()
        ▼
stt_nlp_analysis                (NLP-enriched Gold table)
```

---

## How the configuration flows from `databricks.yml`

All pipeline parameters originate from the bundle variables declared once in `databricks.yml`
and propagate to the pipelines via the `configuration` block of each pipeline YAML.

### Bundle variables

```yaml
variables:
  catalog:
    default: speech_to_text          # Unity Catalog catalog name
  schema:
    default: audio                   # Schema that holds all pipeline tables
  service_principal_id:              # SP used by run_as in both targets
  stt_model:
    default: stt-whisper-large-v3    # Whisper endpoint name (ingestion pipeline only)
```

`stt_model` is the key variable that links three resources simultaneously:

- the **Model Serving endpoint** (its `name` is `${var.stt_model}`)
- the **`stt_audio_ingestion` pipeline configuration** (passed as `stt_model` spark conf)
- the **AI Gateway inference table** (prefix is `inference_${var.stt_model}`)

Changing it in one place propagates everywhere automatically.

### Target overrides summary

| Setting | dev | prod |
| --- | --- | --- |
| `catalog` | `speech_to_text` | `speech_to_text` |
| `schema` | `audio` | `prod` |
| `stt_model` | `stt-whisper-large-v3` (default) | `stt-whisper-large-v3` (default) |
| `pipelines_development` preset | `true` | `false` |
| Unity Catalog schema | created by bundle | created by bundle |
| Unity Catalog volume | created by bundle | not managed |

In development mode (`pipelines_development: true`) Databricks adds a user-specific prefix to
all table names so that developers do not interfere with each other.

---

## Pipeline 1 — `stt_audio_ingestion`

**Pipeline YAML:** `resources/stt_audio_ingestion.pipeline.yml`

```yaml
configuration:
  catalog: ${var.catalog}
  schema: ${var.schema}
  schema_location_base: /Volumes/${var.catalog}/${var.schema}/files/_schema_metadata
  stt_model: ${var.stt_model}    # injected via spark.conf.get("stt_model")
```

### Step 1 — Bronze: `bronze_audio_files_raw`

**File:** `stt_audio_ingestion/transformations/bronze_audio_files.py`

```text
/Volumes/{catalog}/{schema}/files/
        │
        │  Auto Loader (cloudFiles, binaryFile)
        │  pathGlobFilter: *.{wav,mp3,flac,m4a,ogg,mp4}
        ▼
  bronze_audio_files_raw  (streaming Delta table)
```

Auto Loader watches the Unity Catalog Volume for new audio files and picks them up
incrementally — files already ingested are never reprocessed. Each row holds the full
binary content of one audio file alongside its metadata.

| Column | Type | Description |
| --- | --- | --- |
| `path` | STRING | Full path of the file inside the volume |
| `content` | BINARY | Raw bytes of the entire audio file |
| `modificationTime` | TIMESTAMP | Last-modified timestamp from the volume |
| `file_size_bytes` | LONG | Size of the file in bytes |
| `_ingested_at` | TIMESTAMP | Timestamp when Auto Loader picked up the file |
| `_ingested_date` | DATE | Date partition derived from `_ingested_at` |

Clustered on `_ingested_date`. Schema inference metadata is stored at
`schema_location_base/bronze_audio_files_raw`.

### Step 2 — Silver: `silver_audio_transcription`

**File:** `stt_audio_ingestion/transformations/silver_audio_files.py`

```text
  bronze_audio_files_raw
        │
        │  filter: supported extensions only (wav, mp3, flac, m4a, ogg, mp4)
        │  filter: file_size_bytes > 0
        │
        │  ai_query(stt_model, content)   ← calls Whisper Model Serving endpoint
        ▼
  silver_audio_transcription  (streaming Delta table)
```

Reads `bronze_audio_files_raw` as a streaming source and applies:

1. **Metadata extraction** — derives `file_name` and `file_extension` from `path` via regex.
2. **Filtering** — drops unsupported formats and empty files before calling the endpoint.
3. **Transcription** — calls Whisper via `ai_query()` inside `selectExpr()`:

   ```python
   stt_model = spark.conf.get("stt_model")
   .selectExpr(f"ai_query('{stt_model}', content) AS transcription_text", ...)
   ```

| Column | Type | Description |
| --- | --- | --- |
| `path` | STRING | Full path of the source audio file |
| `file_name` | STRING | File name extracted from path |
| `file_extension` | STRING | Lowercase extension (wav, mp3, …) |
| `file_size_bytes` | LONG | Size of the audio file |
| `modificationTime` | TIMESTAMP | Last-modified timestamp from the volume |
| `transcription_text` | STRING | Text returned by the Whisper endpoint |
| `_transcribed_at` | TIMESTAMP | Timestamp when transcription was produced |
| `_ingested_at` | TIMESTAMP | Ingestion timestamp from the bronze layer |
| `_ingested_date` | DATE | Date partition from the bronze layer |

Clustered on `(_ingested_date, file_extension)`.

---

## Pipeline 2 — `stt_nlp_analysis`

**Pipeline YAML:** `resources/stt_nlp_analysis.pipeline.yml`

```yaml
configuration:
  catalog: ${var.catalog}    # injected via spark.conf.get("catalog")
  schema: ${var.schema}      # injected via spark.conf.get("schema")
```

`catalog` and `schema` are used to build the fully-qualified cross-pipeline source reference:
`{catalog}.{schema}.silver_audio_transcription`.

### Gold: `stt_nlp_analysis_ai_func`

**File:** `stt_nlp_analysis/transformations/gold_audio_ai_func_nlp.py`

```text
  {catalog}.{schema}.silver_audio_transcription
        │
        │  filter: transcription_text IS NOT NULL AND != ""
        │
        │  ai_analyze_sentiment(transcription_text)   → sentiment
        │  ai_summarize(transcription_text)            → summary
        │  ai_extract(transcription_text, labels)      → entities (STRUCT)
        │  ai_classify(transcription_text, labels)     → topic
        │  ai_translate(transcription_text, 'Italian') → translation_it
        ▼
  stt_nlp_analysis_ai_func  (streaming Delta table — Gold layer)
```

Records with NULL or empty `transcription_text` are filtered out before any AI function is
invoked. The five Databricks AI SQL functions are called via PySpark `selectExpr()` — no
external model endpoint or custom inference code is required.

#### `ai_analyze_sentiment(transcription_text)`

Detects the emotional tone of the transcription.

- Return type: `STRING` — `positive` | `negative` | `neutral` | `mixed`
- Use case: flag negative conversations for review, aggregate sentiment trends over time.

#### `ai_summarize(transcription_text)`

Generates a concise summary of the full transcription.

- Return type: `STRING`
- Use case: dashboard digests, search index content, notification emails.

#### `ai_extract(transcription_text, array(...))`

Extracts structured named entities. Labels are controlled by `ENTITY_LABELS_SQL` in
`gold_audio_ai_func_nlp.py`:

```python
ENTITY_LABELS_SQL = "array('person', 'organization', 'location', 'date', 'amount')"
```

- Return type: `STRUCT<person ARRAY<STRING>, organization ARRAY<STRING>, location ARRAY<STRING>, date ARRAY<STRING>, amount ARRAY<STRING>>`
- Use case: knowledge graphs, compliance audits, CRM enrichment.

#### `ai_classify(transcription_text, array(...))`

Classifies the transcription into a single business topic. Labels are controlled by
`TOPIC_LABELS_SQL` in `gold_audio_ai_func_nlp.py`:

```python
TOPIC_LABELS_SQL = "array('financial', 'legal', 'medical', 'operational', 'general')"
```

- Return type: `STRING` (one of the labels above)
- Use case: route records to domain-specific consumers, filter dashboards by department.

#### `ai_translate(transcription_text, 'Italian')`

Translates the full transcription text into Italian.

- Return type: `STRING`
- Use case: make transcriptions accessible to Italian-speaking teams, localise dashboards and reports, enable cross-language search.

#### Output schema

| Column | Type | Description |
| --- | --- | --- |
| `path` | STRING | Full path of the source audio file |
| `file_name` | STRING | File name extracted from path |
| `file_extension` | STRING | Lowercase audio format |
| `transcription_text` | STRING | Full transcription from the silver layer |
| `sentiment` | STRING | Emotional tone: positive / negative / neutral / mixed |
| `summary` | STRING | Concise summary of the transcription |
| `entities` | STRUCT | Named entities grouped by type |
| `topic` | STRING | Business topic classification |
| `translation_it` | STRING | Italian translation of the transcription |
| `_ingested_date` | DATE | Date partition from the bronze layer |
| `_ingested_at` | TIMESTAMP | Ingestion timestamp from the bronze layer |
| `_transcribed_at` | TIMESTAMP | Transcription timestamp from the silver layer |
| `_analyzed_at` | TIMESTAMP | Timestamp when NLP enrichment was applied |

Clustered on `_ingested_date`.

#### Customizing labels

To change classification categories or add entity types, edit only the two constants at the
top of `gold_audio_ai_func_nlp.py` — no changes to the pipeline YAML or `databricks.yml` are needed.

---

## Directory structure

```text
src/
├── STT_README.md                                  # this file
├── stt_audio_ingestion/
│   └── transformations/
│       ├── bronze_audio_files.py                  # Bronze: Auto Loader → bronze_audio_files_raw
│       └── silver_audio_files.py                  # Silver: Whisper transcription → silver_audio_transcription
└── stt_nlp_analysis/
    ├── _experimental/                             # NOT included in pipeline glob (transformations/**)
    │   └── gold_audio_ai_query_nlp.py             # Draft: same NLP tasks via ai_query() + external model
    └── transformations/
        └── gold_audio_ai_func_nlp.py              # ACTIVE — Gold: AI SQL functions → stt_nlp_analysis_ai_func
```

---

## Deploying and running

```bash
# Deploy both pipelines to dev (default target)
databricks bundle deploy --var="service_principal_id=<SP_APP_ID>"

# Deploy both pipelines to prod
databricks bundle deploy --target prod --var="service_principal_id=<SP_APP_ID>"

# Run the ingestion pipeline (Bronze + Silver)
databricks bundle run stt_audio_ingestion

# Run the NLP pipeline (Gold)
databricks bundle run stt_nlp_analysis
```
