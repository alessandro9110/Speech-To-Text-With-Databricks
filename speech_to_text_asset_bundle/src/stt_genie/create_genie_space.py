# Databricks notebook source
# This notebook creates or updates the Speech-to-Text Genie Space via the
# Databricks REST API (w.api_client). It is designed to be executed as a task
# inside the stt_genie_setup bundle job after the gold layer tables are ready.
#
# Run it once after the initial deployment, and re-run it whenever you want to
# update the description, sample questions, or table list.
#
# The Genie REST API uses the field 'title' (not 'display_name') and requires
# a 'serialized_space' JSON string containing sample_questions and data_sources.

# COMMAND ----------

dbutils.widgets.text("catalog",      "speech_to_text",       "Catalog")
dbutils.widgets.text("schema",       "audio",                "Schema")
dbutils.widgets.text("warehouse_id", "",                     "SQL Warehouse ID")
dbutils.widgets.text("display_name", "Speech to Text Analytics", "Genie Space Name")

# COMMAND ----------

catalog      = dbutils.widgets.get("catalog")
schema       = dbutils.widgets.get("schema")
warehouse_id = dbutils.widgets.get("warehouse_id")
display_name = dbutils.widgets.get("display_name")

assert warehouse_id, "warehouse_id parameter is required — pass the SQL warehouse ID"

table_identifiers = [
    f"{catalog}.{schema}.gold_audio_sentiment_analysis",
    f"{catalog}.{schema}.gold_audio_daily_stats",
    f"{catalog}.{schema}.gold_audio_sentiment_by_topic",
]

print(f"Catalog:      {catalog}")
print(f"Schema:       {schema}")
print(f"Warehouse ID: {warehouse_id}")
print(f"Display Name: {display_name}")
print(f"Tables:       {table_identifiers}")

# COMMAND ----------

import json
import uuid
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

description = f"""Explore Speech-to-Text analysis results from contact center audio recordings.

Three gold-layer tables are available:

• {catalog}.{schema}.gold_audio_sentiment_analysis
  One row per transcription. Contains file metadata, full transcription text,
  word count, character length, sentiment (positive / negative / neutral / mixed),
  summary, topic, Italian translation, and named entities (person, organization,
  location, date, amount). Clustered by _ingested_date, topic, sentiment.

• {catalog}.{schema}.gold_audio_daily_stats
  Daily aggregations grouped by _ingested_date × topic × sentiment. Contains
  transcription counts, unique file counts, average transcription length (chars),
  and average word count. Use this table for trend analysis.

• {catalog}.{schema}.gold_audio_sentiment_by_topic
  Pivot table — one row per topic, with separate columns for each sentiment label
  (positive, negative, neutral, mixed) showing the count of transcriptions.
  Use this table for sentiment distribution comparisons across topics.

All dates are in the _ingested_date column (DATE type).
Sentiment and topic values are lowercase strings.
File sizes are in bytes (file_size_bytes) in the detail table.
"""

sample_questions = [
    "How many transcriptions have been processed in total?",
    "What is the sentiment distribution across all recordings?",
    "Which topics appear most frequently in the transcriptions?",
    "Show me the daily volume of transcriptions over time",
    "What is the average word count per transcription?",
    "Which recordings have a negative sentiment?",
    "Show the average transcription length grouped by topic",
    "How many transcriptions were processed last week?",
    "Which topics have the highest proportion of neutral sentiment?",
    "Show me the 10 most recent transcriptions with their sentiment and topic",
    "What is the total number of unique audio files processed?",
    "Compare the number of positive vs negative transcriptions per topic",
]

# The Genie REST API requires 'serialized_space': a JSON string containing
# sample questions and data source table identifiers.
serialized_space = json.dumps({
    "version": 2,
    "config": {
        "sample_questions": [
            {"id": uuid.uuid4().hex, "question": [q]} for q in sample_questions
        ],
    },
    "data_sources": {
        "tables": [
            {"identifier": t} for t in sorted(table_identifiers)
        ],
    },
})

# The REST API uses 'title' (not 'display_name') for the space name.
space_body = {
    "title":            display_name,
    "description":      description,
    "warehouse_id":     warehouse_id,
    "serialized_space": serialized_space,
}

# COMMAND ----------
# Check whether a space with this title already exists.

existing_space_id = None
try:
    response  = w.api_client.do("GET", "/api/2.0/genie/spaces")
    all_spaces = response.get("spaces", [])
    match = next(
        (s for s in all_spaces if s.get("title") == display_name),
        None,
    )
    if match:
        existing_space_id = match["space_id"]
        print(f"Found existing Genie Space '{display_name}' (space_id: {existing_space_id})")
except Exception as e:
    print(f"Warning: could not list Genie Spaces — will attempt to create: {e}")

# COMMAND ----------
# Create or update the space.

if existing_space_id:
    w.api_client.do(
        "PATCH",
        f"/api/2.0/genie/spaces/{existing_space_id}",
        body=space_body,
    )
    space_id = existing_space_id
    print(f"Updated Genie Space '{display_name}' (space_id: {space_id})")
else:
    result   = w.api_client.do("POST", "/api/2.0/genie/spaces", body=space_body)
    space_id = result["space_id"]
    print(f"Created Genie Space '{display_name}' (space_id: {space_id})")

# COMMAND ----------

dbutils.notebook.exit(space_id)
