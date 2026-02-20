from pyspark import pipelines as dp
from pyspark.sql.functions import (
    col,
    current_timestamp,
    lit,
    regexp_extract,
    lower,
)

# Supported audio extensions (must match the pathGlobFilter in bronze)
SUPPORTED_EXTENSIONS = ["wav", "mp3", "flac", "m4a", "ogg", "mp4"]


@dp.table(
    name="silver_audio_files",
    cluster_by=["_ingested_date", "file_extension"],
    comment="Validated and enriched audio file records ready for transcription. "
            "Each row represents one audio file with its extracted metadata. "
            "'transcription_status' starts as 'pending' and is updated by the "
            "transcription job once the file has been processed.",
)
def silver_audio_files():
    """
    Silver layer: clean, validate, and enrich bronze_audio_files.

    Transformations applied:
    - Extract file name and extension from the full path
    - Filter to supported audio formats only
    - Add 'transcription_status' column (default: 'pending')
    - Add '_processed_at' audit timestamp
    """
    # Reads from the bronze table defined in bronze_audio_files.py.
    # Unqualified name resolves to the pipeline's configured catalog/schema.
    return (
        spark.readStream.table("bronze_audio_files")
        # Extract the file name (last segment after the final '/')
        .withColumn(
            "file_name",
            regexp_extract(col("path"), r"([^/]+)$", 1),
        )
        # Extract the file extension (lowercased)
        .withColumn(
            "file_extension",
            lower(regexp_extract(col("path"), r"\.([^.]+)$", 1)),
        )
        # Keep only rows whose extension is in the supported list
        .filter(col("file_extension").isin(SUPPORTED_EXTENSIONS))
        # Ensure the file is not empty
        .filter(col("file_size_bytes") > 0)
        # Default transcription status; updated externally after model inference
        .withColumn("transcription_status", lit("pending"))
        .withColumn("_processed_at", current_timestamp())
        # Forward the clustering column from bronze
        .withColumn("_ingested_date", col("_ingested_date"))
        .select(
            col("path"),
            col("file_name"),
            col("file_extension"),
            col("file_size_bytes"),
            col("modificationTime"),
            col("transcription_status"),
            col("_ingested_at"),
            col("_ingested_date"),
            col("_processed_at"),
        )
    )
