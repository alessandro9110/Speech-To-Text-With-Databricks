from pyspark import pipelines as dp
from pyspark.sql.functions import col

# Pipeline-level parameters set in stt_nlp_analysis.pipeline.yml
catalog = spark.conf.get("catalog")
schema = spark.conf.get("schema")

# ── Topic classification labels ───────────────────────────────────────────────
# Passed to ai_classify() to bucket each transcription into a business category.
# Extend this list to add domain-specific topics without changing the pipeline logic.
TOPIC_LABELS_SQL = "array('financial', 'legal', 'medical', 'operational', 'general')"

# ── Entity extraction labels ──────────────────────────────────────────────────
# Passed to ai_extract() to pull structured entities out of the transcription text.
# Each label becomes a field in the returned STRUCT column (ARRAY<STRING> per label).
ENTITY_LABELS_SQL = "array('person', 'organization', 'location', 'date', 'amount')"


@dp.table(
    name="stt_nlp_analysis",
    cluster_by=["_ingested_date"],
    comment="Gold layer: NLP enrichment of transcribed audio. "
            "Reads silver_audio_transcription from the stt_audio_ingestion pipeline "
            "and applies Databricks AI SQL functions to produce: "
            "sentiment (ai_analyze_sentiment), summary (ai_summarize), "
            "named entities (ai_extract) and topic classification (ai_classify).",
)
def stt_nlp_analysis():
    """
    Gold layer: NLP enrichment of transcription text via Databricks AI functions.

    Source:
        {catalog}.{schema}.silver_audio_transcription
        (cross-pipeline reference — full 3-part name required)

    Transformations applied:
        - Filter out NULL or empty transcriptions before calling AI endpoints
        - ai_analyze_sentiment()  → sentiment:  STRING ('positive' | 'negative' |
                                                          'neutral' | 'mixed')
        - ai_summarize()          → summary:    STRING (concise summary of the text)
        - ai_extract()            → entities:   STRUCT<person, organization,
                                                       location, date, amount>
                                                each field is ARRAY<STRING>
        - ai_classify()           → topic:      STRING (one of TOPIC_LABELS)

    Pipeline parameters:
        catalog  (spark.conf)  Unity Catalog catalog name.
        schema   (spark.conf)  Schema that holds silver_audio_transcription.
    """
    return (
        spark.readStream.table(f"{catalog}.{schema}.silver_audio_transcription")

        # Skip records where transcription is absent or empty before calling AI endpoints
        .filter(col("transcription_text").isNotNull())
        .filter(col("transcription_text") != "")

        # ── NLP enrichment via Databricks AI SQL functions ────────────────────
        # selectExpr bridges PySpark streaming with SQL AI functions.
        # All four functions call Databricks-managed foundation models under the hood
        # — no endpoint configuration is required.
        # ─────────────────────────────────────────────────────────────────────
        .selectExpr(
            "path",
            "file_name",
            "file_extension",
            "transcription_text",
            "_ingested_date",
            "_ingested_at",
            "_transcribed_at",

            # Detect the overall emotional tone of the transcription
            "ai_analyze_sentiment(transcription_text) AS sentiment",

            # Generate a concise summary of the transcription content
            "ai_summarize(transcription_text) AS summary",

            # Extract structured named entities: people, orgs, locations, dates, amounts
            f"ai_extract(transcription_text, {ENTITY_LABELS_SQL}) AS entities",

            # Classify the transcription into a single business topic
            f"ai_classify(transcription_text, {TOPIC_LABELS_SQL}) AS topic",

            "current_timestamp() AS _analyzed_at",
        )
    )
