import dlt
from pyspark.sql.functions import col, current_timestamp, to_date

# Pipeline-level parameters set in speech_to_text_asset_bundle_etl.pipeline.yml
catalog = spark.conf.get("catalog")
schema = spark.conf.get("schema")
schema_location_base = spark.conf.get("schema_location_base")


@dlt.table(
    name="bronze_audio_files",
    cluster_by=["_ingested_date"],
    comment="Raw audio files ingested as bytes from the Unity Catalog Volume. "
            "The 'content' column holds the raw binary of each audio file "
            "and is passed downstream to the transcription model.",
)
def bronze_audio_files():
    """
    Bronze layer: Auto Loader streaming ingest of audio files as bytes from
    /Volumes/{catalog}/{schema}/files/.

    Each row contains the full binary content of one audio file alongside
    its metadata (path, size, modification time). The transcription job
    reads 'content' and calls the Databricks Model Serving endpoint.
    """
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .option("cloudFiles.schemaLocation", f"{schema_location_base}/bronze_audio_files")
        # Include only supported audio formats
        .option("pathGlobFilter", "*.{wav,mp3,flac,m4a,ogg,mp4}")
        .load(f"/Volumes/{catalog}/{schema}/files/")
        .select(
            col("path"),
            col("content"),                              # raw bytes of the audio file
            col("modificationTime"),
            col("length").alias("file_size_bytes"),
            current_timestamp().alias("_ingested_at"),
        )
        .withColumn("_ingested_date", to_date(col("_ingested_at")))
    )
