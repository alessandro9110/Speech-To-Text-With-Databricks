from pyspark import pipelines as dp
from pyspark.sql.functions import col, regexp_extract, lower

# Supported audio extensions (must match the pathGlobFilter in bronze)
SUPPORTED_EXTENSIONS = ["wav", "mp3", "flac", "m4a", "ogg", "mp4"]

# Pipeline-level parameters set in stt_audio_ingestion.pipeline.yml
# stt_model: name of the Whisper Model Serving endpoint used for transcription
stt_model = spark.conf.get("stt_model")


@dp.table(
    name="silver_audio_transcription",
    cluster_by=["_ingested_date", "file_extension"],
    comment="Validated audio file records enriched with Whisper transcription text. "
            "Reads raw binary content from bronze_audio_files_raw, filters out "
            "unsupported formats and empty files, then calls ai_query() against "
            "the Whisper model serving endpoint (stt_model pipeline parameter) "
            "to produce the transcription_text.",
)
def silver_audio_transcription():
    """
    Silver layer: validate, filter, and transcribe raw audio files.

    Transformations applied:
    - Extract file name and extension from the full path
    - Filter to supported audio formats only
    - Discard empty files before calling the endpoint
    - Call ai_query() with the Whisper serving endpoint (stt_model) to get transcription_text

    Pipeline parameter:
        stt_model  (spark.conf)  Name of the Whisper Model Serving endpoint.
                                 Driven by var.stt_model in databricks.yml,
                                 injected via stt_audio_ingestion.pipeline.yml > configuration.
    """
    return (
        spark.readStream.table("bronze_audio_files_raw")

        # Extract file name and extension for filtering and clustering
        .withColumn("file_name", regexp_extract(col("path"), r"([^/]+)$", 1))
        .withColumn("file_extension", lower(regexp_extract(col("path"), r"\.([^.]+)$", 1)))

        # Keep only supported audio formats (must match pathGlobFilter in bronze)
        .filter(col("file_extension").isin(SUPPORTED_EXTENSIONS))

        # Discard empty files before calling the serving endpoint
        .filter(col("file_size_bytes") > 0)

        # ── Transcription via ai_query ──────────────────────────────────────
        # selectExpr allows calling SQL AI functions from Python.
        # ai_query() sends the raw audio bytes (content column) to the Whisper
        # serving endpoint and returns the transcription as a STRING.
        # Note: if the endpoint expects base64-encoded input, replace 'content'
        #       with 'base64(content)' in the expression below.
        # ───────────────────────────────────────────────────────────────────
        .selectExpr(
            "path",
            "file_name",
            "file_extension",
            "file_size_bytes",
            "modificationTime",
            f"ai_query('{stt_model}', content) AS transcription_text",
            "current_timestamp() AS _transcribed_at",
            "_ingested_at",
            "_ingested_date",
        )
    )
