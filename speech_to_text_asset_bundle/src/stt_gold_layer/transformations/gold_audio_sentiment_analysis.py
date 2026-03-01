from pyspark import pipelines as dp
from pyspark.sql.functions import col, length, lower, size, split, trim

# Pipeline-level parameters set in resources/stt_gold_layer.pipeline.yml
catalog           = spark.conf.get("catalog")
schema            = spark.conf.get("schema")
nlp_source_table  = spark.conf.get("nlp_source_table")


@dp.table(
    name="gold_audio_sentiment_analysis",
    cluster_by=["_ingested_date", "topic", "sentiment"],
    comment="Gold layer: full detail view of every transcription with its NLP enrichment. "
            "Source NLP table is configurable via the nlp_source_table pipeline parameter "
            "(default: silver_audio_nlp_ai_query). "
            "Joined with silver_audio_transcription for file-level metadata. "
            "Flattens the entity STRUCT and adds derived text metrics. "
            "Primary source for dashboards and sentiment analysis across topics, dates, and file attributes.",
)
def gold_audio_sentiment_analysis():
    """
    Gold layer: per-transcription NLP detail table with sentiment as the primary dimension.

    Source selection:
        Driven by the nlp_source_table pipeline parameter (var.gold_nlp_source_table in
        databricks.yml). Default: silver_audio_nlp_ai_query (Foundation Model API — richer,
        more contextual summaries). Can be switched to silver_audio_nlp_ai_func (AI SQL
        functions) without code changes via the bundle variable or pipeline configuration.
        Sentiment and topic values are normalised to lowercase to ensure consistent grouping
        in downstream aggregations regardless of which source is selected.

    Sources:
        {catalog}.{schema}.{nlp_source_table}          — NLP enrichment (configurable)
        {catalog}.{schema}.silver_audio_transcription  — raw metadata (file size, mod time)

    Transformations applied:
        - Left-join silver_audio_transcription to bring in file_size_bytes, modificationTime
        - Normalise sentiment and topic to lowercase
        - Flatten entities STRUCT into individual columns (entities_person, …, entities_amount)
        - Derive transcription_length (character count) and transcription_word_count

    Pipeline parameters:
        catalog           (spark.conf)  Unity Catalog catalog name.
        schema            (spark.conf)  Schema that holds the silver tables.
        nlp_source_table  (spark.conf)  Silver NLP table to read from (see databricks.yml).
    """
    nlp = spark.read.table(f"{catalog}.{schema}.{nlp_source_table}")

    # Bring in file-level metadata not carried forward by the NLP pipeline
    txn = (
        spark.read.table(f"{catalog}.{schema}.silver_audio_transcription")
        .select("path", "file_size_bytes", "modificationTime")
    )

    return (
        nlp.join(txn, on="path", how="left")
        .select(
            # ── File identity ──────────────────────────────────────────────
            col("path"),
            col("file_name"),
            col("file_extension"),
            col("file_size_bytes"),
            col("modificationTime"),

            # ── Transcription text and derived metrics ─────────────────────
            col("transcription_text"),
            length(col("transcription_text")).alias("transcription_length"),
            size(split(trim(col("transcription_text")), r"\s+")).alias("transcription_word_count"),

            # ── NLP outputs ────────────────────────────────────────────────
            # Normalise to lowercase: source values are Title Case (e.g. "Neutral", "Financial")
            lower(col("sentiment")).alias("sentiment"),
            col("summary"),
            lower(col("topic")).alias("topic"),
            col("translation_it"),

            # ── Flattened entity struct ────────────────────────────────────
            # ai_extract() returns STRUCT<person, organization, location, date, amount>
            # each field is ARRAY<STRING>. Exposed as top-level array columns here.
            col("entities.person").alias("entities_person"),
            col("entities.organization").alias("entities_organization"),
            col("entities.location").alias("entities_location"),
            col("entities.date").alias("entities_date"),
            col("entities.amount").alias("entities_amount"),

            # ── Audit metadata ─────────────────────────────────────────────
            col("_ingested_date"),
            col("_ingested_at"),
            col("_transcribed_at"),
            col("_analyzed_at"),
            col("_nlp_model"),
        )
    )
