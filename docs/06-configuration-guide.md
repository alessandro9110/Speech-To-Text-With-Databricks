# Configuration Guide

This document provides a comprehensive guide to all configuration options in the project.

## Configuration Overview

The project uses **variables** instead of hardcoded values for security and flexibility. Configuration can be provided via:

1. Command-line arguments (`--var`)
2. Local configuration file (`databricks.yml.local`)
3. GitHub environment variables (for CI/CD)

## Configuration Variables

### Databricks Asset Bundle Variables

Defined in `speech_to_text_asset_bundle/databricks.yml`:

```yaml
variables:
  catalog:
    description: The catalog to use for Speech To Text With Databrikcs solution.
  schema:
    description: The schema to use for Speech To Text With Databrikcs solution.
  databricks_host:
    description: The Databricks workspace URL (e.g., https://your-workspace.cloud.databricks.com)
  admin_user_email:
    description: The email address of the admin user for production deployment permissions
```

### Variable Details

#### `databricks_host`
**Required for**: Both dev and prod  
**Purpose**: Specifies the Databricks workspace URL  
**Format**: `https://<workspace-id>.cloud.databricks.com`  
**Example**: `https://dbc-12345678-9abc.cloud.databricks.com`

**Security Note**: Never hardcode this in the repository. Use variables or local config files.

#### `admin_user_email`
**Required for**: Prod only  
**Purpose**: Grants CAN_MANAGE permission to an admin user in production  
**Format**: Valid email address  
**Example**: `admin@example.com`

**Security Note**: Never commit personal email addresses to the repository.

#### `catalog`
**Required for**: Both dev and prod  
**Purpose**: Unity Catalog name for the solution  
**Default values**:
- Dev: `speech_to_text` (defined in target)
- Prod: `speech_to_text` (defined in target)

**Note**: Values are pre-configured in targets, no need to override unless needed.

#### `schema`
**Required for**: Both dev and prod  
**Purpose**: Schema name within the catalog  
**Default values**:
- Dev: `dev` (defined in target)
- Prod: `prod` (defined in target)

**Note**: Values are pre-configured in targets, no need to override unless needed.

## Configuration Methods

### Method 1: Command Line Variables

Pass variables directly when running Databricks CLI commands:

```bash
# Dev deployment
databricks bundle deploy --target dev \
  --var="databricks_host=https://your-workspace.cloud.databricks.com"

# Prod deployment
databricks bundle deploy --target prod \
  --var="databricks_host=https://your-workspace.cloud.databricks.com" \
  --var="admin_user_email=admin@example.com"
```

**Pros**:
- ✅ No files to manage
- ✅ Explicit and visible
- ✅ Good for CI/CD scripts

**Cons**:
- ❌ Verbose for repeated use
- ❌ Easy to forget required variables

### Method 2: Local Configuration File

Create `speech_to_text_asset_bundle/databricks.yml.local`:

```yaml
targets:
  dev:
    variables:
      databricks_host: https://your-workspace.cloud.databricks.com
  
  prod:
    variables:
      databricks_host: https://your-workspace.cloud.databricks.com
      admin_user_email: admin@example.com
```

Then deploy without explicit variables:
```bash
cd speech_to_text_asset_bundle
databricks bundle deploy --target dev
databricks bundle deploy --target prod
```

**Pros**:
- ✅ Simple deployment commands
- ✅ Easy to maintain
- ✅ Good for local development

**Cons**:
- ❌ Must create file
- ❌ Must not commit (in .gitignore)

**Example file**: See `.databricks.yml.example` for a template.

### Method 3: GitHub Environment Variables

For CI/CD workflows, configure in GitHub:

**Location**: Settings → Environments → [Dev/Prod] → Variables

**Dev Environment**:
| Variable | Value |
|----------|-------|
| `DATABRICKS_HOST` | Your workspace URL |

**Prod Environment**:
| Variable | Value |
|----------|-------|
| `DATABRICKS_HOST` | Your workspace URL |

**Note**: The workflows don't pass these as bundle variables. Instead, they set them as environment variables for authentication. The `admin_user_email` variable still needs to be provided via databricks.yml.local or the workflow needs to be updated to pass it.

## Target-Specific Configuration

### Dev Target

```yaml
dev:
  presets:
    name_prefix: ${workspace.current_user.short_name}_
    pipelines_development: true
    trigger_pause_status: PAUSED
    jobs_max_concurrent_runs: 10
    tags:
      department: finance
  mode: development
  default: true
  workspace:
    host: ${var.databricks_host}
    root_path: /Workspace/Users/${workspace.current_user.user_name}/.bundle/${bundle.name}/${bundle.target}
  variables:
    catalog: speech_to_text
    schema: dev
  resources:
    schemas:
      dev:
        name: dev
        catalog_name: speech_to_text
        comment: 'Schema for development'
```

**Key Settings**:
- **mode**: `development` - enables development features
- **name_prefix**: User's short name - prevents conflicts
- **root_path**: User-specific folder
- **pipelines_development**: `true` - faster pipeline iterations
- **trigger_pause_status**: `PAUSED` - jobs don't run automatically
- **default**: `true` - used when no target specified

### Prod Target

```yaml
prod:
  presets:
    name_prefix: 'prod_'
    pipelines_development: false
    trigger_pause_status: PAUSED
    jobs_max_concurrent_runs: 10
    tags:
      department: finance
  mode: production
  workspace:
    host: ${var.databricks_host}
    root_path: /Workspace/Shared/.bundle/${bundle.name}/${bundle.target}
  variables:
    catalog: speech_to_text
    schema: prod
  resources:
    schemas:
      prod:
        name: prod
        catalog_name: speech_to_text
        comment: 'Schema for production'
  permissions:
    - user_name: ${var.admin_user_email}
      level: CAN_MANAGE
```

**Key Settings**:
- **mode**: `production` - strict validation
- **name_prefix**: `prod_` - clear production indicator
- **root_path**: Shared folder - single deployment
- **pipelines_development**: `false` - production-optimized
- **permissions**: Admin user gets CAN_MANAGE access

## Authentication Configuration

### For GitHub Actions (OIDC)

Already configured in workflows:

```yaml
env:
  DATABRICKS_AUTH_TYPE: github-oidc
  DATABRICKS_HOST: ${{ vars.DATABRICKS_HOST }}
  DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
```

**Required GitHub Configuration**:

**Environment Variables**:
- `DATABRICKS_HOST`: Workspace URL

**Environment Secrets**:
- `DATABRICKS_CLIENT_ID`: Service principal UUID

### For Local Development

Use Databricks CLI authentication. Configure with:

```bash
databricks auth login --host https://your-workspace.cloud.databricks.com
```

Or use environment variables:
```bash
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=your-token
```

**Security Note**: Never commit tokens or use them in public repositories.

## Python Package Configuration

### pyproject.toml

```toml
[project]
name = "speech_to_text_asset_bundle"
version = "0.0.1"
requires-python = ">=3.10,<3.13"
dependencies = []

[dependency-groups]
dev = [
    "pytest",
    "ruff",
    "databricks-dlt",
    "databricks-connect>=15.4,<15.5",
    "ipykernel",
]

[project.scripts]
main = "speech_to_text_asset_bundle.main:main"

[tool.ruff]
line-length = 120
```

**Key Settings**:
- **Python version**: 3.10, 3.11, or 3.12
- **Entry point**: `main` command runs `speech_to_text_asset_bundle.main:main`
- **Ruff line length**: 120 characters

### Installing Dependencies

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or using uv (faster)
uv sync --dev
```

## Resource Configuration

### Jobs

Configured in `resources/sample_job.job.yml`:

```yaml
resources:
  jobs:
    sample_job:
      name: sample_job
      trigger:
        periodic:
          interval: 1
          unit: DAYS
      parameters:
        - name: catalog
          default: ${var.catalog}
        - name: schema
          default: ${var.schema}
      # ... tasks ...
```

**Configurable**:
- Trigger schedule (interval, unit)
- Parameters (uses bundle variables)
- Email notifications (commented out)

### Pipelines

Configured in `resources/speech_to_text_asset_bundle_etl.pipeline.yml`:

```yaml
resources:
  pipelines:
    speech_to_text_asset_bundle_etl:
      name: speech_to_text_asset_bundle_etl
      catalog: ${var.catalog}
      schema: ${var.schema}
      serverless: true
      root_path: "../src/speech_to_text_asset_bundle_etl"
      # ... libraries ...
```

**Configurable**:
- Catalog and schema (uses bundle variables)
- Serverless vs cluster-based
- Library paths
- Dependencies

## Validation

### Validate Configuration

Before deploying, validate your configuration:

```bash
cd speech_to_text_asset_bundle

# Validate dev configuration
databricks bundle validate --target dev

# Validate prod configuration
databricks bundle validate --target prod \
  --var="databricks_host=https://..." \
  --var="admin_user_email=admin@example.com"
```

### Common Validation Errors

#### "variable 'X' has not been set"
**Solution**: Provide the variable via command line or databricks.yml.local

#### "invalid workspace host"
**Solution**: Ensure databricks_host is a valid URL format

#### "permission denied"
**Solution**: Ensure service principal or user has necessary permissions

## Configuration Best Practices

### Security
- ❌ Never commit `databricks.yml.local`
- ❌ Never hardcode workspace URLs
- ❌ Never commit personal email addresses
- ✅ Use variables for all environment-specific values
- ✅ Use GitHub Secrets for CI/CD
- ✅ Use OIDC instead of tokens

### Organization
- ✅ Keep `databricks.yml.local` template in `.databricks.yml.example`
- ✅ Document all variables in databricks.yml
- ✅ Use consistent naming across environments
- ✅ Separate dev and prod configurations

### Maintenance
- ✅ Review variables when adding new resources
- ✅ Update documentation when changing configuration
- ✅ Validate configuration before merging PRs
- ✅ Test configuration in dev before prod

## Environment Variables Reference

### For Databricks CLI

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABRICKS_HOST` | Workspace URL | `https://...` |
| `DATABRICKS_TOKEN` | Personal access token | `dapi...` |
| `DATABRICKS_AUTH_TYPE` | Authentication method | `github-oidc` |
| `DATABRICKS_CLIENT_ID` | Service principal ID | `UUID` |

### For Python Code

Job and pipeline tasks can access parameters:

```python
# In job task
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--catalog")
parser.add_argument("--schema")
args = parser.parse_args()
```

## Troubleshooting

### Configuration Not Applied
- Check file name: must be `databricks.yml.local`
- Check location: must be in `speech_to_text_asset_bundle/`
- Check YAML syntax: validate with `yamllint`

### Variable Not Found
- Ensure variable is defined in `variables:` section
- Check spelling and case sensitivity
- Verify variable is set in target or passed via CLI

### Authentication Issues
- For local: run `databricks auth login`
- For CI/CD: check GitHub environment configuration
- Verify service principal has correct permissions

## Next Steps

- [Local Development Setup](05-local-development.md) - Set up your local environment
- [Deployment Guide](11-deployment-guide.md) - Deploy with your configuration
- [Troubleshooting](13-troubleshooting.md) - Solve configuration issues
