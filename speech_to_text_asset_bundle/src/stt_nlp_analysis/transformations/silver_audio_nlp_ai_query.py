from pyspark import pipelines as dp
from pyspark.sql.functions import col, trim

# Pipeline-level parameters set in stt_nlp_analysis.pipeline.yml
catalog = spark.conf.get("catalog")
schema = spark.conf.get("schema")
# Name of the external model serving endpoint used for NLP inference.
# Driven by var.gpt_model in databricks.yml (default: stt-gpt-5-2).
nlp_model = spark.conf.get("nlp_model")


@dp.table(
    name="stt_nlp_analysis_ai_query",
    cluster_by=["_ingested_date"],
    comment="Gold layer: NLP enrichment via ai_query() against an external model serving "
            "endpoint. Routes each NLP task (sentiment, summary, entities, topic, translation) "
            "through a custom or third-party model rather than using built-in Databricks AI "
            "SQL functions. The endpoint is driven by the nlp_model pipeline parameter.",
)
def stt_nlp_analysis_ai_query():
    """
    Gold layer: NLP enrichment via an external model endpoint.

    Source:
        {catalog}.{schema}.silver_audio_transcription
        (cross-pipeline reference — full 3-part name required)

    Strategy:
        Each NLP task is sent to the external endpoint as a separate ai_query() call
        with a task-specific instruction prompt prepended to the transcription text.
        All calls happen in a single selectExpr pass over the streaming batch.

    Transformations applied:
        - Filter out NULL or empty transcriptions before calling the endpoint
        - ai_query(nlp_model, prompt + text) → sentiment   STRING
        - ai_query(nlp_model, prompt + text) → summary     STRING
        - ai_query(nlp_model, prompt + text) → entities    STRUCT<person, organization, location, date, amount> (parsed via from_json)
        - ai_query(nlp_model, prompt + text) → topic       STRING
        - ai_query(nlp_model, prompt + text) → translation_it STRING

    Pipeline parameters:
        catalog    (spark.conf)  Unity Catalog catalog name.
        schema     (spark.conf)  Schema that holds silver_audio_transcription.
        nlp_model  (spark.conf)  Name of the external Model Serving endpoint.
    """
    return (
        spark.readStream.table(f"{catalog}.{schema}.silver_audio_transcription")

        # Skip records where transcription is absent or empty before calling the endpoint
        .filter(col("transcription_text").isNotNull())
        .filter(trim(col("transcription_text")) != "")

        # ── NLP enrichment via ai_query() against the external model endpoint ─────
        # Each column prepends a task-specific instruction to guide the model.
        # The nlp_model endpoint must support plain-text single-turn prompts.
        # ─────────────────────────────────────────────────────────────────────────
        .selectExpr(
            "path",
            "file_name",
            "file_extension",
            "transcription_text",
            "_ingested_date",
            "_ingested_at",
            "_transcribed_at",

            # Sentiment: return only one of: positive, negative, neutral, mixed
            f"ai_query('{nlp_model}',"
            f"  CONCAT('Classify the sentiment of the following text as one of: "
            f"positive, negative, neutral, mixed. Reply with one word only.\\n\\n',"
            f"  transcription_text)) AS sentiment",

            # Summary: concise single-sentence summary
            f"ai_query('{nlp_model}',"
            f"  CONCAT('Summarize the following text in one concise sentence.\\n\\n',"
            f"  transcription_text)) AS summary",

            # Entities: parse JSON response into STRUCT matching ai_extract() output schema.
            # from_json() converts the model's JSON string into a typed STRUCT so that
            # the column type is identical to the ai_func version of this table.
            f"from_json("
            f"  ai_query('{nlp_model}',"
            f"    CONCAT('Extract named entities from the following text. "
            f"Return ONLY valid JSON with keys: person, organization, location, date, amount. "
            f"Each key maps to an array of extracted strings. "
            f"Return an empty array [] if nothing is found. No extra text.\\n\\n',"
            f"    transcription_text)),"
            f"  'struct<person:array<string>,organization:array<string>,"
            f"location:array<string>,date:array<string>,amount:array<string>>'"
            f") AS entities",

            # Topic: return one of the predefined business topics
            f"ai_query('{nlp_model}',"
            f"  CONCAT('Classify the following text into exactly one of these topics: "
            f"financial, legal, medical, operational, general. Reply with one word only.\\n\\n',"
            f"  transcription_text)) AS topic",

            # Italian translation
            f"ai_query('{nlp_model}',"
            f"  CONCAT('Translate the following text to Italian. "
            f"Return only the translation, no explanations.\\n\\n',"
            f"  transcription_text)) AS translation_it",

            "current_timestamp() AS _analyzed_at",
        )
    )
