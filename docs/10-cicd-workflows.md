# CI/CD Workflows

This document describes the GitHub Actions workflows in this repository.

## Overview

The repository uses GitHub Actions for continuous integration and deployment. Currently, there are **2 deployment workflows** but **no PR validation workflows yet**.

## Workflow Files

All workflows are located in `.github/workflows/`:

```
.github/workflows/
├── deploy_asset_bundle_prod.yml  # Production deployment
└── sync_git_folder_dev.yml       # Development sync
```

## Path Filters

**Important**: Both workflows include path filters to avoid unnecessary runs:

```yaml
on:
  push:
    paths:
      - 'speech_to_text_asset_bundle/**'
      - '.github/workflows/**'
```

This means workflows **only run when**:
- Files in `speech_to_text_asset_bundle/` change
- Workflow files themselves change

**Benefits**:
- Saves GitHub Actions minutes
- Faster feedback (no waiting for unrelated changes)
- Cleaner Actions history

## Development Workflow: sync_git_folder_dev.yml

### Purpose
Synchronizes code to the Dev Git folder in Databricks for rapid iterative development.

### Trigger
```yaml
on:
  push:
    branches:
      - dev
    paths:
      - 'speech_to_text_asset_bundle/**'
      - '.github/workflows/**'
```

### Configuration

**Environment**: `Dev` (GitHub environment)

**Required Variables**:
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Databricks workspace URL | `https://<workspace>.cloud.databricks.com` |

**Required Secrets**:
| Secret | Description |
|--------|-------------|
| `DATABRICKS_CLIENT_ID` | Service principal UUID for OIDC |

**Permissions**:
```yaml
permissions:
  id-token: write  # Required for OIDC
  contents: read   # Required to checkout code
```

### Authentication Method
Uses **GitHub OIDC** to obtain a short-lived token:
```yaml
env:
  DATABRICKS_AUTH_TYPE: github-oidc
  DATABRICKS_HOST: ${{ vars.DATABRICKS_HOST }}
  DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
```

### Actions
1. Checkout code (`actions/checkout@v3`)
2. Setup Databricks CLI (`databricks/setup-cli@main`)
3. Update Git folder:
   ```bash
   databricks repos update /Workspace/Shared/Speech-To-Text-With-Databricks --branch dev
   ```

### Target Location
Updates repository at:
```
/Workspace/Shared/Speech-To-Text-With-Databricks
```

### When to Use
- Active development on the `dev` branch
- Want immediate code updates in Databricks
- Testing notebooks interactively
- Rapid iteration without full deployment

### Concurrency
```yaml
concurrency: dev_environment
```
Prevents multiple simultaneous deployments to dev.

## Production Workflow: deploy_asset_bundle_prod.yml

### Purpose
Deploys the complete Databricks Asset Bundle to production with proper governance.

### Trigger
```yaml
on:
  push:
    branches:
      - main
    paths:
      - 'speech_to_text_asset_bundle/**'
      - '.github/workflows/**'
```

### Configuration

**Environment**: `Prod` (GitHub environment)

**Required Variables**:
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Databricks workspace URL | `https://<workspace>.cloud.databricks.com` |

**Required Secrets**:
| Secret | Description |
|--------|-------------|
| `DATABRICKS_CLIENT_ID` | Service principal UUID for OIDC |

**Permissions**:
```yaml
permissions:
  id-token: write  # Required for OIDC
  contents: read   # Required to checkout code
```

### Authentication Method
Uses **GitHub OIDC** to obtain a short-lived token:
```yaml
env:
  DATABRICKS_AUTH_TYPE: github-oidc
  DATABRICKS_HOST: ${{ vars.DATABRICKS_HOST }}
  DATABRICKS_CLIENT_ID: ${{ secrets.DATABRICKS_CLIENT_ID }}
```

### Actions
1. Checkout code (`actions/checkout@v3`)
2. Setup Databricks CLI (`databricks/setup-cli@main`)
3. Deploy asset bundle:
   ```bash
   cd speech_to_text_asset_bundle
   databricks bundle deploy --target prod
   ```

### Target Configuration
From `databricks.yml`:
```yaml
prod:
  mode: production
  workspace:
    host: ${var.databricks_host}
    root_path: /Workspace/Shared/.bundle/${bundle.name}/${bundle.target}
  variables:
    catalog: speech_to_text
    schema: prod
```

### Deployment Location
```
/Workspace/Shared/.bundle/speech_to_text_asset_bundle/prod/
```

### When to Use
- Deploying stable, tested code to production
- After PR approval and merge to main
- For production-grade deployments with governance

### Concurrency
```yaml
concurrency: prod_environment
```
Prevents multiple simultaneous deployments to prod.

## Missing Workflows (Planned)

According to `.github/instructions/workflow.instructions.md`, the following workflows should be added:

### PR Validation Workflow (Not Yet Implemented)
**Should include**:
- Linting (ruff)
- Unit tests (pytest)
- Asset bundle validation (`databricks bundle validate -t dev`)
- Asset bundle validation (`databricks bundle validate -t prod`)

**Path filters**:
- Must use the same path filters as deployment workflows

**No secrets**:
- Should not echo secrets
- Should not include real workspace URLs in committed files

## OIDC Setup Requirements

### Service Principal Federation Policies

For workflows to authenticate, the service principal must have federation policies configured:

#### Dev Environment Policy
```
Issuer: https://token.actions.githubusercontent.com
Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev
Audiences: <service-principal-uuid>
```

#### Prod Environment Policy
```
Issuer: https://token.actions.githubusercontent.com
Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Prod
Audiences: <service-principal-uuid>
```

### Security Benefits
- ✅ No long-lived tokens
- ✅ Short-lived credentials (expires quickly)
- ✅ Scoped to specific repository and environment
- ✅ Auditable in both GitHub and Databricks
- ✅ Can't be stolen and reused elsewhere

## Workflow Comparison

| Feature | Dev Workflow | Prod Workflow |
|---------|--------------|---------------|
| **Branch** | dev | main |
| **Method** | Git sync | Bundle deploy |
| **Target** | Git folder | Bundle deployment |
| **Speed** | Fast | Slower (full validation) |
| **Use Case** | Active development | Production deployment |
| **Validation** | None | Full bundle validation |
| **Resources** | Per-user prefixed | prod_ prefixed |

## Monitoring Workflows

### View Workflow Runs
1. Go to the **Actions** tab in GitHub
2. Select the workflow name
3. View run history and logs

### Manual Trigger
Currently, workflows only trigger on push. Manual triggering not configured.

To add manual triggering, add to workflow:
```yaml
on:
  workflow_dispatch:
```

## Troubleshooting

### Workflow Doesn't Trigger
**Check**:
1. Are changes in filtered paths?
   - Changes to `docs/` won't trigger workflows
   - Only `speech_to_text_asset_bundle/**` and `.github/workflows/**` trigger
2. Correct branch?
   - `dev` → sync_git_folder_dev.yml
   - `main` → deploy_asset_bundle_prod.yml

### Authentication Fails
**Check**:
1. Environment variables set correctly in GitHub?
2. Service principal has federation policy for this environment?
3. Subject in policy matches: `repo:owner/repo:environment:EnvName`
4. Service principal has necessary permissions in workspace?

### Deployment Fails
**Check**:
1. Asset bundle valid locally?
   ```bash
   databricks bundle validate --target prod
   ```
2. All required variables set in databricks.yml?
3. Service principal has deployment permissions?
4. Check workflow logs for specific errors

### Path Filter Issues
**To test if path affects workflow**:
```bash
# These WILL trigger workflows
git add speech_to_text_asset_bundle/src/example.py
git commit -m "Update code"
git push

# These WILL NOT trigger workflows
git add docs/new-doc.md
git commit -m "Update docs"
git push
```

## Best Practices

### Security
- ✅ Use OIDC (already configured)
- ✅ Use GitHub environments (already configured)
- ✅ Use path filters (already configured)
- ❌ Never echo secrets in logs
- ❌ Never commit workspace URLs

### Development
- Use `dev` branch for active development
- Test locally before pushing to `dev`
- Only merge to `main` after thorough testing
- Add PR validation workflow (not yet implemented)

### Deployment
- Monitor workflow runs in Actions tab
- Check Databricks workspace after deployment
- Verify resources created correctly
- Test deployed jobs/pipelines

## Next Steps

### Add PR Validation Workflow
According to workflow.instructions.md, create:
```yaml
# .github/workflows/pr_validation.yml
name: PR Validation
on:
  pull_request:
    paths:
      - 'speech_to_text_asset_bundle/**'
      - '.github/workflows/**'

jobs:
  lint:
    # Run ruff
  test:
    # Run pytest
  validate:
    # Run databricks bundle validate
```

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Databricks CLI Documentation](https://docs.databricks.com/dev-tools/cli/index.html)
- [GitHub OIDC in Databricks](https://docs.databricks.com/dev-tools/auth/provider-github.html)
- [Workflow Instructions](.github/instructions/workflow.instructions.md)
