# Configuration Guide for Databricks Asset Bundle

## Overview

This document explains how to configure the required variables after the security improvements that removed hardcoded secrets.

## What Changed

Previously, the following sensitive information was hardcoded in the repository:
- Databricks workspace URL
- Personal email addresses

Now, these values are configurable through variables.

## Required Configuration

### For GitHub Actions Workflows

The workflows already use environment variables. Ensure these are set in your GitHub repository:

**Settings → Environments → Dev/Prod → Variables:**
- `DATABRICKS_HOST`: Your Databricks workspace URL

**Settings → Environments → Dev/Prod → Secrets:**
- `DATABRICKS_CLIENT_ID`: Service principal client ID for OIDC authentication

### For Local Development

You have two options:

#### Option 1: Command Line Variables

```bash
# Dev deployment
databricks bundle deploy --target dev \
  --var="databricks_host=https://your-workspace.cloud.databricks.com"

# Prod deployment
databricks bundle deploy --target prod \
  --var="databricks_host=https://your-workspace.cloud.databricks.com" \
  --var="admin_user_email=admin@example.com"
```

#### Option 2: Local Configuration File

Create `speech_to_text_asset_bundle/databricks.yml.local` (this file is git-ignored):

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

Then simply run:
```bash
databricks bundle deploy --target dev
# or
databricks bundle deploy --target prod
```

## Variables Reference

| Variable | Required For | Description | Example |
|----------|-------------|-------------|---------|
| `databricks_host` | dev, prod | Your Databricks workspace URL | `https://your-workspace.cloud.databricks.com` |
| `admin_user_email` | prod only | Admin email for production permissions | `admin@example.com` |

## Security Notes

- Never commit `databricks.yml.local` - it's in `.gitignore`
- Never hardcode workspace URLs or emails in the repository
- Use GitHub Secrets for CI/CD authentication
- The workflows use OIDC authentication (no long-lived tokens needed)

## Verification

After configuration, test your setup:

```bash
# Validate the configuration
databricks bundle validate --target dev

# Deploy to dev
databricks bundle deploy --target dev
```

## Troubleshooting

### Error: "variable 'databricks_host' has not been set"

**Solution:** Provide the variable using one of the methods above.

### Error: "variable 'admin_user_email' has not been set"

**Solution:** This variable is only required for prod deployments. Add it to your configuration.

For more help, see:
- [README.md](../README.md)
- [.github/ENVIRONMENT_SETUP.md](../.github/ENVIRONMENT_SETUP.md)
