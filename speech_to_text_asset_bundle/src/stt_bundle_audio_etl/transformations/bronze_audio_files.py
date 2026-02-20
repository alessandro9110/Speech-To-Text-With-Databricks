from pyspark import pipelines as dp
from pyspark.sql.functions import col, current_timestamp, to_date

# Pipeline-level parameters set in speech_to_text_asset_bundle_etl.pipeline.yml
catalog = spark.conf.get("catalog")
schema = spark.conf.get("schema")
schema_location_base = spark.conf.get("schema_location_base")


@dp.table(
    name="bronze_audio_files",
    cluster_by=["_ingested_date"],
    comment="Raw audio file metadata ingested from the Unity Catalog Volume. "
            "Binary content is excluded to keep table size manageable; "
            "use the 'path' column to locate the file for transcription.",
)
def bronze_audio_files():
    """
    Bronze layer: Auto Loader streaming ingest of audio files from
    /Volumes/{catalog}/{schema}/files/.

    Captures file metadata only (path, size, modification time).
    The actual transcription is performed downstream by a separate job
    that reads from this table and calls the model serving endpoint.
    """
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "binaryFile")
        .option("cloudFiles.schemaLocation", f"{schema_location_base}/bronze_audio_files")
        # Include only supported audio formats
        .option("pathGlobFilter", "*.{wav,mp3,flac,m4a,ogg,mp4}")
        # Exclude the binary content column — audio files can be large
        .option("binaryFile.excludeContent", "true")
        .load(f"/Volumes/{catalog}/{schema}/files/")
        .select(
            col("path"),
            col("modificationTime"),
            col("length").alias("file_size_bytes"),
            current_timestamp().alias("_ingested_at"),
        )
        .withColumn("_ingested_date", to_date(col("_ingested_at")))
    )
