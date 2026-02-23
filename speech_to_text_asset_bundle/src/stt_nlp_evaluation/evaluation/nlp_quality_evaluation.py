# Databricks notebook source

# MAGIC %md
# MAGIC # NLP Quality Evaluation
# MAGIC
# MAGIC Evaluates the quality of NLP enrichment produced by the speech-to-text pipeline,
# MAGIC comparing the two NLP implementations head-to-head:
# MAGIC
# MAGIC | Implementation | Table | How AI is called |
# MAGIC |---|---|---|
# MAGIC | **ai_func** | `silver_audio_nlp_ai_func` | Databricks built-in AI SQL functions |
# MAGIC | **ai_query** | `silver_audio_nlp_ai_query` | External LLM endpoint (`nlp_model`) |
# MAGIC
# MAGIC Both tables share the same output schema:
# MAGIC `sentiment · summary · entities · topic · translation_it`
# MAGIC
# MAGIC Results are logged to an MLflow experiment so you can compare runs over time
# MAGIC in the MLflow UI.

# COMMAND ----------

# DBTITLE 1,Install / verify MLflow version
# Requires mlflow[databricks] >= 3.1.0
# Run this cell once if the cluster doesn't have the right version installed.
# %pip install --upgrade "mlflow[databricks]>=3.1.0" --quiet

# COMMAND ----------

# DBTITLE 1,Imports
import mlflow
from mlflow.genai.scorers import scorer
from mlflow.genai.judges import meets_guidelines
from mlflow.entities import Feedback

# COMMAND ----------

# DBTITLE 1,MLflow Setup
mlflow.set_tracking_uri("databricks")
mlflow.set_experiment("/Shared/speech-to-text/nlp-quality-evaluation")

# COMMAND ----------

# DBTITLE 1,Configuration
# ── Adjust to match your deployment environment ───────────────────────────────
CATALOG = "speech_to_text"
SCHEMA = "audio"      # "audio" for dev; "prod" for production
SAMPLE_SIZE = 50      # Number of rows to evaluate per NLP implementation
# ─────────────────────────────────────────────────────────────────────────────

# Valid label sets — must stay in sync with the pipeline prompt definitions
VALID_SENTIMENTS = {"positive", "negative", "neutral", "mixed"}
VALID_TOPICS = {"financial", "legal", "medical", "operational", "general"}

# COMMAND ----------

# DBTITLE 1,Load Evaluation Data from Silver Tables


def load_eval_data(table_name, sample_size):
    """
    Reads a sample from a silver NLP table and converts rows into the
    MLflow evaluation data format: [{"inputs": {...}, "outputs": {...}}, ...]

    The outputs are pre-computed by the pipeline, so no predict_fn is needed
    during evaluation — mlflow.genai.evaluate() scores them directly.
    """
    df = (
        spark.read.table(f"{CATALOG}.{SCHEMA}.{table_name}")
        .select(
            "transcription_text",
            "sentiment",
            "summary",
            "entities",
            "topic",
            "translation_it",
            "_nlp_model",
        )
        .filter("transcription_text IS NOT NULL AND LENGTH(TRIM(transcription_text)) > 0")
        .limit(sample_size)
    )

    records = []
    for row in df.collect():
        entities = row["entities"] or {}
        records.append(
            {
                "inputs": {
                    "transcription_text": row["transcription_text"],
                },
                "outputs": {
                    "sentiment": row["sentiment"] or "",
                    "summary": row["summary"] or "",
                    "entities": {
                        "person":       (entities.get("person") or []),
                        "organization": (entities.get("organization") or []),
                        "location":     (entities.get("location") or []),
                        "date":         (entities.get("date") or []),
                        "amount":       (entities.get("amount") or []),
                    },
                    "topic": row["topic"] or "",
                    "translation_it": row["translation_it"] or "",
                    "_nlp_model": row["_nlp_model"] or "",
                },
            }
        )
    return records


ai_func_data = load_eval_data("silver_audio_nlp_ai_func", SAMPLE_SIZE)
ai_query_data = load_eval_data("silver_audio_nlp_ai_query", SAMPLE_SIZE)

print(f"Rows loaded — ai_func : {len(ai_func_data)}")
print(f"Rows loaded — ai_query: {len(ai_query_data)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Scorers
# MAGIC
# MAGIC Two scorer categories:
# MAGIC
# MAGIC 1. **Format validators** – deterministic checks (no LLM cost).
# MAGIC    Ensure each output field contains a valid, non-empty value.
# MAGIC 2. **Quality judges** – LLM-based checks using `meets_guidelines()`.
# MAGIC    Assess whether the NLP output is semantically correct for the transcription.

# COMMAND ----------

# DBTITLE 1,Format Validation Scorers


@scorer
def sentiment_format(outputs):
    """Checks that sentiment is one of the four expected labels."""
    value = (outputs.get("sentiment") or "").strip().lower()
    is_valid = value in VALID_SENTIMENTS
    return Feedback(
        name="sentiment_format",
        value=is_valid,
        rationale=f"Got '{value}'; expected one of {sorted(VALID_SENTIMENTS)}",
    )


@scorer
def topic_format(outputs):
    """Checks that topic is one of the five expected labels."""
    value = (outputs.get("topic") or "").strip().lower()
    is_valid = value in VALID_TOPICS
    return Feedback(
        name="topic_format",
        value=is_valid,
        rationale=f"Got '{value}'; expected one of {sorted(VALID_TOPICS)}",
    )


@scorer
def entities_completeness(outputs):
    """Checks that all five entity keys are present in the entities struct."""
    entities = outputs.get("entities") or {}
    required_keys = {"person", "organization", "location", "date", "amount"}
    missing = required_keys - set(entities.keys())
    is_valid = len(missing) == 0
    return Feedback(
        name="entities_completeness",
        value=is_valid,
        rationale=(
            f"Missing entity keys: {sorted(missing)}"
            if missing
            else "All entity keys present"
        ),
    )


@scorer
def outputs_non_empty(outputs):
    """
    Checks that the four main output fields are non-empty strings.
    Returns one Feedback per field so each metric is tracked independently.
    """
    checks = {
        "summary_non_empty":     (outputs.get("summary") or "").strip(),
        "translation_non_empty": (outputs.get("translation_it") or "").strip(),
        "sentiment_non_empty":   (outputs.get("sentiment") or "").strip(),
        "topic_non_empty":       (outputs.get("topic") or "").strip(),
    }
    return [
        Feedback(
            name=name,
            value=bool(value),
            rationale="Non-empty" if value else "Empty or whitespace-only",
        )
        for name, value in checks.items()
    ]


# COMMAND ----------

# DBTITLE 1,Quality Scorers (LLM Judges via meets_guidelines)


@scorer
def summary_quality(inputs, outputs):
    """
    LLM judge: checks that the summary captures the key content of the transcription.

    Uses meets_guidelines() with explicit context so this scorer works correctly
    even when there is no predict_fn (pre-computed outputs path).
    """
    transcription = inputs.get("transcription_text") or ""
    summary = outputs.get("summary") or ""
    return meets_guidelines(
        name="summary_quality",
        guidelines=[
            "The response must be a concise, single-sentence summary",
            "The response must reflect the main topic or key information present in the request",
            "The response must not be empty or a generic placeholder",
        ],
        context={"request": transcription, "response": summary},
    )


@scorer
def sentiment_consistency(inputs, outputs):
    """
    LLM judge: checks that the sentiment label is consistent
    with the emotional tone of the transcription.
    """
    transcription = inputs.get("transcription_text") or ""
    sentiment = outputs.get("sentiment") or ""
    return meets_guidelines(
        name="sentiment_consistency",
        guidelines=[
            "The response must be a single sentiment label: positive, negative, neutral, or mixed",
            "The response must match the overall emotional tone expressed in the request",
        ],
        context={"request": transcription, "response": sentiment},
    )


@scorer
def topic_accuracy(inputs, outputs):
    """
    LLM judge: checks that the topic label correctly describes
    the primary domain of the transcription.
    """
    transcription = inputs.get("transcription_text") or ""
    topic = outputs.get("topic") or ""
    return meets_guidelines(
        name="topic_accuracy",
        guidelines=[
            "The response must be a single label: financial, legal, medical, operational, or general",
            "The response must correctly describe the primary subject domain of the request",
        ],
        context={"request": transcription, "response": topic},
    )


# COMMAND ----------

# DBTITLE 1,Assemble Scorer List

ALL_SCORERS = [
    # ── Format validators (deterministic, no LLM cost) ────────────────────────
    sentiment_format,
    topic_format,
    entities_completeness,
    outputs_non_empty,
    # ── Quality judges (LLM-based) ────────────────────────────────────────────
    summary_quality,
    sentiment_consistency,
    topic_accuracy,
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Evaluation Runs
# MAGIC
# MAGIC Each `mlflow.genai.evaluate()` call creates a named MLflow run under the
# MAGIC experiment `/Shared/speech-to-text/nlp-quality-evaluation`.
# MAGIC Open the experiment in the MLflow UI to compare runs side-by-side.

# COMMAND ----------

# DBTITLE 1,Evaluate — ai_func Implementation

print("Evaluating silver_audio_nlp_ai_func ...")

with mlflow.start_run(run_name="silver_audio_nlp_ai_func"):
    ai_func_results = mlflow.genai.evaluate(
        data=ai_func_data,
        scorers=ALL_SCORERS,
        # predict_fn is omitted: outputs are pre-computed from the pipeline table
    )

print(f"  Run ID : {ai_func_results.run_id}")
print(f"  Metrics: {ai_func_results.metrics}")

# COMMAND ----------

# DBTITLE 1,Evaluate — ai_query Implementation

print("Evaluating silver_audio_nlp_ai_query ...")

with mlflow.start_run(run_name="silver_audio_nlp_ai_query"):
    ai_query_results = mlflow.genai.evaluate(
        data=ai_query_data,
        scorers=ALL_SCORERS,
        # predict_fn is omitted: outputs are pre-computed from the pipeline table
    )

print(f"  Run ID : {ai_query_results.run_id}")
print(f"  Metrics: {ai_query_results.metrics}")

# COMMAND ----------

# DBTITLE 1,Compare Results

all_metrics = sorted(
    set(ai_func_results.metrics) | set(ai_query_results.metrics)
)

print("\n=== NLP Quality Comparison ===")
print(f"  Catalog : {CATALOG}")
print(f"  Schema  : {SCHEMA}")
print(f"  Sample  : {SAMPLE_SIZE} rows per implementation\n")

col_w = 48
print(f"{'Metric':<{col_w}} {'ai_func':>10} {'ai_query':>10}")
print("-" * (col_w + 22))

for metric in all_metrics:
    func_val  = ai_func_results.metrics.get(metric)
    query_val = ai_query_results.metrics.get(metric)
    func_str  = f"{func_val:.3f}"  if isinstance(func_val,  float) else str(func_val)
    query_str = f"{query_val:.3f}" if isinstance(query_val, float) else str(query_val)
    print(f"{metric:<{col_w}} {func_str:>10} {query_str:>10}")

print(f"\nView full trace-level results in the MLflow UI:")
print(f"  ai_func  → run {ai_func_results.run_id}")
print(f"  ai_query → run {ai_query_results.run_id}")
