# Speech-To-Text with Databricks — Solution Overview

## What does this solution do?

This solution takes raw audio files — meetings, calls, recordings — and turns them into structured,
enriched data you can query and analyse directly in Databricks.

The process happens in three stages:

1. **Transcription.** Audio files dropped into a Unity Catalog Volume are picked up automatically
   and transcribed to text using the Whisper Large V3 model served via a Databricks Model Serving
   endpoint.

2. **NLP enrichment.** Each transcription is enriched with sentiment, a summary, named entities,
   a topic classification, and an Italian translation. This step runs two parallel implementations
   side by side — one using Databricks built-in AI SQL functions, the other using the Foundation
   Model API — so you can compare them.

3. **Quality evaluation.** An MLflow evaluation notebook reads a sample from both enriched tables,
   scores them against a set of validators and LLM judges, and logs the results to an MLflow
   experiment so you can compare the two implementations visually.

---

## Architecture A — Triggered mode (current)

In the default setup, a single Databricks job called `stt_main` orchestrates the whole flow.
You trigger it manually or on a schedule, and it runs the three stages in sequence:

```text
  stt_main job  (manual trigger or cron schedule)
        │
        ├─ Step 1: run_ingestion_pipeline
        │          Picks up new audio files from the Volume and writes silver_audio_transcription
        │
        ├─ Step 2: run_nlp_pipeline          [waits for Step 1]
        │          Enriches new transcriptions and writes silver_audio_nlp_ai_func
        │          and silver_audio_nlp_ai_query in parallel
        │
        └─ Step 3: evaluate_nlp_quality      [waits for Step 2]
                   Runs the MLflow evaluation notebook and logs results
```

Each pipeline step runs a **triggered update**: it processes everything that arrived since the
last run, then shuts down. No compute stays on between runs, so you only pay when the job runs.

The three Databricks resources that back this job are:

| Resource | Type | What it does |
| --- | --- | --- |
| `stt_audio_transcription` | Spark Declarative Pipeline | Bronze → Silver transcription |
| `stt_nlp_enrichment` | Spark Declarative Pipeline | Silver NLP enrichment (two implementations) |
| `stt_nlp_evaluation` | Spark Declarative Pipeline | MLflow GenAI evaluation of both NLP implementations |
| `stt_main` | Job | Orchestrates the three pipelines in sequence |

Configuration — catalog name, schema, model endpoint names — is driven by the bundle variables
in `databricks.yml` and flows automatically into each resource at deploy time.

---

## Architecture B — Continuous mode (alternative)

> **Disclaimer — when and how to switch**
>
> If you need audio transcribed within seconds of upload rather than waiting for the next job run,
> you can switch both pipelines to **continuous mode**. In continuous mode each pipeline runs
> permanently, processing new files the moment they appear, without needing a job to trigger them.
>
> To make the switch:
>
> 1. Add `continuous: enabled: true` to `stt_audio_transcription.pipeline.yml` and
>    `stt_nlp_enrichment.pipeline.yml`.
> 2. Remove (or delete entirely) the `run_ingestion_pipeline` and `run_nlp_pipeline` tasks from
>    `stt_main`. The evaluation notebook can be run on its own schedule or manually.
>
> Keep in mind the trade-offs:

| | Architecture A (triggered) | Architecture B (continuous) |
| --- | --- | --- |
| Latency | Depends on job schedule | Near real-time (seconds) |
| Cost | Pay per run | Always-on compute |
| Evaluation | Runs automatically after each update | Decoupled, run separately |
| Orchestration | Single job controls everything | Pipelines run independently |

---

## Deploying and running

Deploy to dev (default) or prod, then trigger the job:

```bash
# Deploy to dev
databricks bundle deploy --var="service_principal_id=<SP_APP_ID>"

# Deploy to prod
databricks bundle deploy --target prod --var="service_principal_id=<SP_APP_ID>"

# Run the full pipeline
databricks bundle run stt_main
```

---

## Source files

```text
src/
├── stt_audio_transcription/transformations/
│   ├── bronze_audio_files.py        # Auto Loader → bronze_audio_files_raw
│   └── silver_audio_files.py        # Whisper → silver_audio_transcription
├── stt_nlp_enrichment/transformations/
│   ├── silver_audio_nlp_ai_func.py  # NLP via AI SQL functions
│   └── silver_audio_nlp_ai_query.py # NLP via Foundation Model (ai_query)
└── stt_nlp_evaluation/evaluation/
    └── nlp_quality_evaluation.py    # MLflow GenAI evaluation notebook
```
