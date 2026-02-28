from pyspark import pipelines as dp
from pyspark.sql.functions import (
    col,
    count,
    avg,
    countDistinct,
    round as spark_round,
    sum as spark_sum,
)

# Pipeline-level parameters set in resources/stt_gold_layer.pipeline.yml
catalog = spark.conf.get("catalog")
schema = spark.conf.get("schema")


@dp.table(
    name="gold_audio_daily_stats",
    cluster_by=["_ingested_date"],
    comment="Gold layer: daily aggregated statistics grouped by ingestion date, topic, and "
            "sentiment. Tracks transcription volume, average text length, word count, and unique "
            "file count per day. Feeds time-series charts and KPI tiles in dashboards.",
)
def gold_audio_daily_stats():
    """
    Gold layer: daily aggregation of transcription and NLP metrics.

    Source:
        {catalog}.{schema}.gold_audio_sentiment_analysis   (gold detail table)

    Aggregations:
        - transcription_count      — number of transcriptions per group
        - unique_files             — number of distinct audio files processed
        - avg_transcription_length — average character count of transcription text
        - avg_word_count           — average word count of transcription text
        - total_transcription_length — sum of all character counts (proxy for total volume)

    Dimensions:
        _ingested_date, topic, sentiment

    Pipeline parameters:
        catalog  (spark.conf)  Unity Catalog catalog name.
        schema   (spark.conf)  Schema that holds the gold detail table.
    """
    return (
        spark.read.table(f"{catalog}.{schema}.gold_audio_sentiment_analysis")
        .groupBy("_ingested_date", "topic", "sentiment")
        .agg(
            count("*").alias("transcription_count"),
            countDistinct("file_name").alias("unique_files"),
            spark_round(avg("transcription_length"), 0).cast("long").alias("avg_transcription_length"),
            spark_round(avg("transcription_word_count"), 0).cast("long").alias("avg_word_count"),
            spark_sum("transcription_length").alias("total_transcription_length"),
        )
        .orderBy("_ingested_date", "topic", "sentiment")
    )


@dp.table(
    name="gold_audio_sentiment_by_topic",
    comment="Gold layer: cross-tabulation of topic vs sentiment. "
            "Shows the count of transcriptions for each topic/sentiment combination. "
            "Use for heatmaps and comparative sentiment breakdowns per business domain.",
)
def gold_audio_sentiment_by_topic():
    """
    Gold layer: sentiment distribution cross-tab per business topic.

    Source:
        {catalog}.{schema}.gold_audio_sentiment_analysis   (gold detail table)

    Output columns:
        topic, positive, negative, neutral, mixed

    Each cell contains the count of transcriptions for that topic/sentiment pair.
    Missing combinations are filled with 0.

    Pipeline parameters:
        catalog  (spark.conf)  Unity Catalog catalog name.
        schema   (spark.conf)  Schema that holds the gold detail table.
    """
    return (
        spark.read.table(f"{catalog}.{schema}.gold_audio_sentiment_analysis")
        .groupBy("topic")
        .pivot("sentiment", ["positive", "negative", "neutral", "mixed"])
        .count()
        .fillna(0)
        .orderBy("topic")
    )
