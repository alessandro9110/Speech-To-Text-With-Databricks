# Speech-to-Text Databricks Asset Bundle

## Overview

This Databricks Asset Bundle implements an end-to-end speech-to-text processing solution using the Databricks Lakehouse platform. The solution processes audio files from contact center recordings and converts them into structured text data that can be analyzed and queried.

### Data Source

The audio files used in this solution are sourced from:
- **Dataset**: [AxonData English Contact Center Audio Dataset](https://huggingface.co/datasets/AxonData/english-contact-center-audio-dataset/tree/main)
- **Storage**: Files have been downloaded from HuggingFace and uploaded to the Databricks **`files` volume** in the catalog

This dataset contains English language audio recordings from contact center scenarios, providing realistic use cases for speech-to-text analysis.

---

## Solution Architecture

The solution follows a structured workflow for processing audio files through multiple stages:

### Step-by-Step Processing Flow

1. **Data Ingestion** (Planned/TODO)
   - Audio files are stored in the `files` volume within the `speech_to_text` catalog
   - Files are organized in a structured format for efficient processing
   - Metadata about audio files is captured for tracking

2. **Speech-to-Text Conversion** (Planned/TODO)
   - Audio files are processed using speech recognition models
   - Transcription results are generated with timestamps and confidence scores
   - Processed results are stored as structured data in Delta tables

3. **Data Transformation** (Planned/TODO)
   - Raw transcriptions are cleaned and normalized
   - Text analytics and NLP processing applied
   - Structured outputs created for downstream analysis

4. **Data Quality & Monitoring** (Planned/TODO)
   - Quality checks on transcription accuracy
   - Monitoring of processing times and success rates
   - Alerting for failed or low-quality transcriptions

---

## Project Structure

The asset bundle is organized into logical folders, each serving a specific purpose:

### `/` (Root Directory)
- **`databricks.yml`**: Main configuration file defining the bundle, variables, and deployment targets (dev/prod)
- **`pyproject.toml`**: Python project configuration including dependencies, build settings, and development tools

### `/resources/`
Contains YAML definitions for all Databricks resources (jobs, pipelines, etc.):
- **Pipeline definitions**: Delta Live Tables (DLT) pipelines for ETL processing
- **Job definitions**: Orchestration jobs that combine notebooks, Python tasks, and pipeline refreshes
- **Resource configuration**: Each resource is defined in its own `.yml` file for clarity

Current resources:
- `speech_to_text_asset_bundle_etl.pipeline.yml`: Main DLT pipeline for data transformations
- `sample_job.job.yml`: Orchestration job demonstrating notebook, Python wheel, and pipeline tasks

### `/src/`
Source code for all data processing logic:

#### `/src/speech_to_text_asset_bundle/`
Python package that gets built into a wheel (`.whl`) for job tasks:
- Contains entry points for Python-based job tasks
- Modules for data processing and business logic
- Packaged and deployed as a distributable wheel file

#### `/src/speech_to_text_asset_bundle_etl/`
Delta Live Tables (DLT) pipeline code:
- **`/transformations/`**: DLT dataset definitions and transformation logic
  - Each dataset is typically defined in its own Python file
  - Uses DLT decorators (`@dlt.table`, `@dlt.view`) for declarative transformations
- Follows DLT best practices for incremental processing and data quality

#### `/src/sample_notebook.ipynb`
Sample Databricks notebook demonstrating:
- Interactive data exploration
- Integration with the bundle's Python packages
- Notebook-based tasks in job workflows

### `/tests/`
Testing infrastructure for the solution:
- **Unit tests**: Test individual functions and transformations
- **Integration tests**: Validate end-to-end workflows
- Uses pytest framework with Databricks Connect for local testing
- `conftest.py`: Shared test fixtures and configuration

### `/fixtures/`
Test data and fixture files used by the test suite (currently empty, can be populated with sample data).

---

## Configuration & Deployment

### Prerequisites

Before deploying, ensure you have:
1. Databricks workspace access with appropriate permissions
2. Databricks CLI installed (`pip install databricks-cli`)
3. Required catalog created: `speech_to_text` (must be created manually in Databricks)
4. Service principal configured (for production deployments via GitHub Actions)

### Environment Targets

The bundle supports two deployment targets:

#### **Dev Target** (Default)
- **Purpose**: Development and testing
- **Catalog**: `speech_to_text`
- **Schema**: `default`
- **Mode**: Development mode (pipelines run in development mode)
- **Deployment path**: `~/Shared/.bundle/speech_to_text_asset_bundle/dev`
- **Resources**: Includes dev schema and files volume

#### **Prod Target**
- **Purpose**: Production workloads
- **Catalog**: `speech_to_text`
- **Schema**: `prod`
- **Mode**: Production mode (full pipeline deployment)
- **Deployment path**: `~/Shared/.bundle/speech_to_text_asset_bundle/prod`
- **Resources**: Includes prod schema

### Variables

The bundle uses variables for environment-specific configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `catalog` | Catalog name for Unity Catalog | `speech_to_text` |
| `schema` | Schema name within the catalog | `default` (dev) / `prod` (prod) |
| `service_principal_id` | Application ID of the service principal | (Required for deployments) |

### Deployment Methods

#### Method 1: Command Line with Variables

Deploy directly with inline variables:

```bash
# Deploy to dev environment
databricks bundle deploy --target dev

# Deploy to prod environment
databricks bundle deploy --target prod
```

#### Method 2: Using Local Configuration File

Create a `databricks.yml.local` file (git-ignored) with your environment-specific values:

```yaml
targets:
  dev:
    variables:
      service_principal_id: "your-service-principal-uuid"
  
  prod:
    variables:
      service_principal_id: "your-service-principal-uuid"
```

Then deploy without passing variables:
```bash
databricks bundle deploy --target dev
databricks bundle deploy --target prod
```

See `.databricks.yml.example` for a complete configuration example.

#### Method 3: GitHub Actions (Recommended for Production)

The solution includes automated CI/CD workflows:
- **Dev**: Automatically syncs code to Databricks Git folder on push to `dev` branch
- **Prod**: Automatically deploys asset bundle on push to `main` branch

See the root [README.md](../README.md) for GitHub Actions setup instructions.

---

## Development Workflow

### Local Development

1. **Install Dependencies**
   ```bash
   # Install development dependencies
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   # Run all tests
   pytest tests/
   
   # Run specific test file
   pytest tests/sample_taxis_test.py
   ```

3. **Linting & Code Quality**
   ```bash
   # Run ruff linter
   ruff check .
   
   # Auto-fix issues
   ruff check --fix .
   ```

4. **Build the Wheel**
   ```bash
   # Build Python wheel package
   uv build --wheel
   ```

### Working with Delta Live Tables

The DLT pipeline is located in `src/speech_to_text_asset_bundle_etl/transformations/`:

1. **Create New Transformation**
   - Add a new Python file in the `transformations/` directory
   - Use DLT decorators to define datasets:
     ```python
     import dlt
     
     @dlt.table(
         comment="Description of your dataset"
     )
     def my_dataset():
         return spark.read...
     ```

2. **Test Transformation Locally**
   ```bash
   # Deploy pipeline to dev
   databricks bundle deploy --target dev
   
   # Run specific transformation
   databricks bundle run speech_to_text_asset_bundle_etl --select my_dataset
   ```

3. **View Pipeline in Databricks**
   - Navigate to **Workflows** > **Delta Live Tables**
   - Find your pipeline: `speech_to_text_asset_bundle_etl`
   - Use the visual DAG to inspect dependencies and data lineage

### Working with Jobs

Jobs are defined in `resources/*.job.yml`:

1. **Modify Job Configuration**
   - Edit the YAML file for your job
   - Configure tasks, schedules, and dependencies

2. **Deploy and Run**
   ```bash
   # Deploy the job
   databricks bundle deploy --target dev
   
   # Trigger the job manually
   databricks bundle run sample_job
   ```

3. **Monitor Job Runs**
   - Navigate to **Workflows** > **Jobs**
   - View run history, logs, and task outputs

---

## Bundle Resources Explained

### Delta Live Tables Pipeline

The `speech_to_text_asset_bundle_etl.pipeline.yml` defines:
- **Serverless execution**: Automatically scales compute resources
- **Catalog & Schema**: Uses variables for environment-specific targeting
- **Libraries**: Loads all transformation modules from `src/speech_to_text_asset_bundle_etl/transformations/`
- **Dependencies**: Includes project dependencies via editable install

### Sample Job

The `sample_job.job.yml` demonstrates:
- **Multi-task workflow**: Combines different task types in sequence
- **Task dependencies**: Tasks execute in order based on `depends_on` configuration
- **Task types**:
  - `notebook_task`: Runs Databricks notebooks
  - `python_wheel_task`: Executes Python code from the built wheel package
  - `pipeline_task`: Triggers DLT pipeline refresh
- **Scheduling**: Configured to run daily (can be modified)
- **Environment**: Uses Python environment version 4 with the bundle's wheel package

---

## Data Storage & Unity Catalog

### Catalog Structure

```
speech_to_text (catalog)
├── default (schema - dev environment)
│   └── files (volume - managed)
│       └── [audio files from HuggingFace dataset]
└── prod (schema - prod environment)
    └── [production tables]
```

### Volumes

The **`files` volume** stores:
- Raw audio files downloaded from HuggingFace
- Input data for speech-to-text processing
- Volume type: MANAGED (data managed by Databricks)

### Tables (Planned/TODO)

Future tables to be created by the DLT pipeline:
- Bronze: Raw transcription results
- Silver: Cleaned and normalized text data
- Gold: Aggregated analytics and insights

---

## Security & Best Practices

### Authentication

- **Dev**: Uses service principal for automated deployments
- **Prod**: Requires service principal with restricted permissions
- **Local**: Uses Databricks CLI authentication profiles

### Permissions

Ensure the service principal has:
- `USE CATALOG` on `speech_to_text` catalog
- `USE SCHEMA` on target schema (`default` or `prod`)
- `CREATE TABLE` for DLT pipeline outputs
- `READ VOLUME` and `WRITE VOLUME` on the `files` volume

### Security Notes

- Never commit secrets or credentials to the repository
- Use GitHub Environments for managing secrets in CI/CD
- Service principal federation with GitHub OIDC eliminates long-lived tokens
- All workspace URLs should use placeholders in documentation

---

## Troubleshooting

### Bundle Validation Fails

**Issue**: `databricks bundle validate` returns errors

**Solution**:
1. Check YAML syntax in `databricks.yml` and resource files
2. Ensure all required variables are defined
3. Verify catalog and schema exist in the target workspace
4. Run `databricks bundle validate --target <target>` for specific target

### Pipeline Fails to Start

**Issue**: DLT pipeline won't start or fails immediately

**Solution**:
1. Check that the catalog and schema specified exist
2. Verify the service principal has appropriate permissions
3. Review pipeline logs in the Databricks UI for specific errors
4. Ensure transformation files have no syntax errors

### Job Task Fails

**Issue**: Job task returns error during execution

**Solution**:
1. Check the task logs in the Databricks Jobs UI
2. For Python wheel tasks, ensure the wheel was built successfully
3. For notebook tasks, verify the notebook path is correct
4. Check that all required parameters are passed correctly

### Volume Access Issues

**Issue**: Cannot read from or write to the `files` volume

**Solution**:
1. Verify the volume exists in the target catalog/schema
2. Ensure the service principal has `READ VOLUME` permission
3. Check that file paths are correct (format: `/Volumes/catalog/schema/volume/path`)
4. For dev environment, confirm the volume is created during deployment

---

## Additional Resources

- **Root README**: [../README.md](../README.md) - Overall project setup and CI/CD configuration
- **DLT Documentation**: [Databricks DLT](https://docs.databricks.com/workflows/delta-live-tables/index.html)
- **Asset Bundles Guide**: [Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)
- **Unity Catalog**: [Unity Catalog Documentation](https://docs.databricks.com/data-governance/unity-catalog/index.html)

---

## Next Steps

To get started with this solution:

1. ✅ **Ensure Prerequisites**: Verify catalog exists and authentication is configured
2. ✅ **Deploy to Dev**: Run `databricks bundle deploy --target dev`
3. 📋 **Upload Audio Files**: Place HuggingFace dataset files in the `files` volume
4. 📋 **Implement Transformations**: Develop DLT transformations for speech-to-text processing
5. 📋 **Test Pipeline**: Run the pipeline and validate outputs
6. 📋 **Deploy to Prod**: Once validated, deploy to production target

For questions or issues, refer to the troubleshooting section or the root README documentation.
