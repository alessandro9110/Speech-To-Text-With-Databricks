# Development Workflow

This guide explains how to develop and test changes locally before deploying.

## Prerequisites

Before starting development:

1. ✅ Repository cloned locally
2. ✅ Python 3.10, 3.11, or 3.12 installed
3. ✅ Databricks CLI installed
4. ✅ Authenticated to Databricks workspace

See [Local Development Setup](05-local-development.md) for details.

## Quick Start

```bash
# Clone and navigate to project
cd speech_to_text_asset_bundle

# Install dependencies
uv sync --dev
# or: pip install -e ".[dev]"

# Run tests
pytest

# Lint code
ruff check .

# Format code
ruff format .

# Build wheel
uv build --wheel

# Validate bundle
databricks bundle validate --target dev
```

## Development Loop

### 1. Make Code Changes

Edit files in `speech_to_text_asset_bundle/`:
- `src/` - Source code
- `resources/` - Job/pipeline definitions
- `tests/` - Test code

### 2. Run Linter

Check code quality with ruff:

```bash
cd speech_to_text_asset_bundle

# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

**Ruff Configuration** (from pyproject.toml):
```toml
[tool.ruff]
line-length = 120
```

### 3. Run Tests Locally

```bash
cd speech_to_text_asset_bundle

# Run all tests
pytest

# Run specific test file
pytest tests/sample_taxis_test.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src
```

**Test Framework**:
- pytest - Test runner
- databricks-connect - Local Databricks testing

### 4. Build Package

Build the Python wheel:

```bash
cd speech_to_text_asset_bundle

# Build wheel using uv (fast)
uv build --wheel

# Or using hatchling (slower)
python -m build --wheel
```

**Output**: `dist/speech_to_text_asset_bundle-0.0.1-py3-none-any.whl`

### 5. Validate Bundle

Validate DAB configuration:

```bash
cd speech_to_text_asset_bundle

# Validate dev target
databricks bundle validate --target dev

# Validate prod target (requires variables)
databricks bundle validate --target prod \
  --var="databricks_host=https://..." \
  --var="admin_user_email=admin@example.com"
```

### 6. Deploy to Dev

Deploy to development workspace:

```bash
cd speech_to_text_asset_bundle

# Deploy to dev (creates databricks.yml.local first if needed)
databricks bundle deploy --target dev
```

**What happens**:
1. Code is uploaded to your user folder
2. Resources are created/updated with your name prefix
3. Jobs and pipelines are configured

### 7. Test in Databricks

After deployment:

1. **Open Databricks workspace**
2. **Navigate to your bundle**:
   - Path: `/Workspace/Users/<your-email>/.bundle/speech_to_text_asset_bundle/dev/`
3. **Test resources**:
   - Run notebook: `src/sample_notebook.ipynb`
   - Run job: `<your-name>_sample_job`
   - Run pipeline: `<your-name>_speech_to_text_asset_bundle_etl`

### 8. Iterate

Repeat steps 1-7 as needed.

## Git Workflow

### Branch Strategy

```
main (production)
  ↑
  └── PR for production deployment
       ↑
      dev (development)
       ↑
       └── feature branches
```

### Creating a Feature Branch

```bash
# Start from dev
git checkout dev
git pull origin dev

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, commit
git add .
git commit -m "Add your feature"

# Push to remote
git push origin feature/your-feature-name
```

### Testing Before Committing

```bash
# Run checks
cd speech_to_text_asset_bundle
ruff check .
pytest
databricks bundle validate --target dev

# If all pass, commit
git add .
git commit -m "Your commit message"
```

### Pull Request Process

1. **Create PR** from feature branch to `dev`
2. **Review changes** - Currently no automated checks (PR workflows not yet implemented)
3. **Merge to dev** - Triggers `sync_git_folder_dev.yml` workflow
4. **Test in dev environment**
5. **Create PR** from `dev` to `main` when ready for production
6. **Merge to main** - Triggers `deploy_asset_bundle_prod.yml` workflow

### Commit Message Guidelines

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add speech-to-text transformation for audio files"
git commit -m "Fix job parameter passing in sample_job.yml"
git commit -m "Update README with deployment instructions"

# Less good
git commit -m "update"
git commit -m "fix bug"
git commit -m "changes"
```

## Working with Specific Components

### Python Package (src/speech_to_text_asset_bundle/)

**Structure**:
```
src/speech_to_text_asset_bundle/
├── __init__.py
├── main.py      # Entry point
└── taxis.py     # Example module
```

**Entry Point** (main.py):
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--schema", required=True)
    args = parser.parse_args()
    # Your code here
```

**Testing Locally**:
```bash
# Install in editable mode
pip install -e .

# Run entry point
main --catalog=speech_to_text --schema=dev
```

### DLT Pipeline (src/speech_to_text_asset_bundle_etl/)

**Structure**:
```
src/speech_to_text_asset_bundle_etl/
├── README.md
└── transformations/
    ├── sample_trips_*.py
    └── sample_zones_*.py
```

**Creating Transformations**:
```python
import dlt

@dlt.table(
    name="my_table",
    comment="My table description"
)
def my_transformation():
    return spark.read.table("source_table")
```

**Testing DLT Locally**:
```bash
# Requires databricks-connect
pip install databricks-connect>=15.4,<15.5

# Run transformation
python -m speech_to_text_asset_bundle_etl.transformations.sample_trips_*
```

### Notebooks (src/)

**Location**: `src/sample_notebook.ipynb`

**Development**:
1. Edit locally in VS Code or Jupyter
2. Test in Databricks workspace after deployment
3. Sync changes back to repo

**Best Practices**:
- Keep notebooks simple
- Extract complex logic to Python modules
- Add comments and markdown cells
- Test before committing

### Jobs (resources/)

**Location**: `resources/sample_job.job.yml`

**Editing**:
```yaml
resources:
  jobs:
    sample_job:
      name: sample_job
      # Edit trigger, tasks, etc.
```

**Testing**:
1. Validate: `databricks bundle validate`
2. Deploy: `databricks bundle deploy`
3. Run manually in Databricks UI

### Pipelines (resources/)

**Location**: `resources/speech_to_text_asset_bundle_etl.pipeline.yml`

**Editing**:
```yaml
resources:
  pipelines:
    speech_to_text_asset_bundle_etl:
      catalog: ${var.catalog}
      # Edit configuration
```

**Testing**:
1. Validate: `databricks bundle validate`
2. Deploy: `databricks bundle deploy`
3. Start pipeline in Databricks UI

## Development Tools

### VS Code Setup

Recommended extensions:
- Python
- Jupyter
- YAML
- Ruff

Workspace settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff"
}
```

### Command Line Tools

```bash
# Databricks CLI
databricks --version
databricks auth login
databricks repos list
databricks bundle deploy

# Python tools
python --version
pip --version
uv --version

# Testing
pytest --version
ruff --version
```

## Debugging

### Debug Tests

```bash
# Run with debugging
pytest -v --pdb

# Run specific test with prints
pytest -v -s tests/sample_taxis_test.py::test_function
```

### Debug Jobs

1. Deploy to dev
2. Add print/logging statements
3. Run job manually
4. Check job run logs in Databricks UI

### Debug Pipelines

1. Deploy to dev
2. Start pipeline
3. Check pipeline logs in Databricks UI
4. Use `expectation` clauses for data quality checks

## Performance Tips

### Faster Testing

```bash
# Run only fast tests
pytest -m "not slow"

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

### Faster Building

```bash
# Use uv instead of pip (much faster)
uv sync --dev
uv build --wheel
```

### Faster Deployment

```bash
# Deploy only changed resources
databricks bundle deploy --force-lock

# Skip validation (use with caution)
databricks bundle deploy --force
```

## Best Practices

### Code Quality
- ✅ Run ruff before committing
- ✅ Write tests for new code
- ✅ Keep functions small and focused
- ✅ Add docstrings to public functions
- ✅ Follow PEP 8 (ruff enforces this)

### Testing
- ✅ Test locally before deploying
- ✅ Write unit tests for business logic
- ✅ Test in dev before promoting to prod
- ✅ Use fixtures for common test data

### Documentation
- ✅ Update README when changing functionality
- ✅ Add comments for complex logic
- ✅ Document configuration changes
- ✅ Keep docstrings up to date

### Git
- ✅ Commit frequently with clear messages
- ✅ Use feature branches
- ✅ Pull before pushing
- ✅ Review changes before committing

## Common Tasks

### Add a New Python Module

1. Create file: `src/speech_to_text_asset_bundle/my_module.py`
2. Write code and docstrings
3. Create test: `tests/test_my_module.py`
4. Run tests: `pytest tests/test_my_module.py`
5. Commit changes

### Add a New DLT Transformation

1. Create file: `src/speech_to_text_asset_bundle_etl/transformations/my_transformation.py`
2. Define DLT tables
3. Update pipeline.yml if needed
4. Deploy and test in dev
5. Commit changes

### Modify a Job

1. Edit `resources/sample_job.job.yml`
2. Validate: `databricks bundle validate`
3. Deploy to dev: `databricks bundle deploy`
4. Test job in Databricks UI
5. Commit changes

### Update Dependencies

1. Edit `pyproject.toml`
2. Update lock file: `uv sync`
3. Test: `pytest`
4. Commit `pyproject.toml` (not lock file if using pip)

## Troubleshooting

### Import Errors
**Issue**: Module not found

**Solution**:
```bash
pip install -e .
# or
uv sync --dev
```

### Test Failures
**Issue**: Tests fail locally

**Solution**:
1. Check if dependencies installed
2. Check if databricks-connect configured
3. Run with verbose: `pytest -v`

### Deployment Errors
**Issue**: Bundle deployment fails

**Solution**:
1. Validate first: `databricks bundle validate`
2. Check authentication: `databricks auth login`
3. Check variables in databricks.yml.local
4. Check logs for specific error

### Path Filter Not Triggering Workflow
**Issue**: Push doesn't trigger workflow

**Solution**:
1. Check if files are in filtered paths:
   - `speech_to_text_asset_bundle/**`
   - `.github/workflows/**`
2. Check correct branch (dev or main)
3. Check workflow run history in Actions tab

## Next Steps

- [Testing Guide](09-testing-guide.md) - Learn about testing in detail
- [Deployment Guide](11-deployment-guide.md) - Deploy your changes
- [CI/CD Workflows](10-cicd-workflows.md) - Understand automated workflows
