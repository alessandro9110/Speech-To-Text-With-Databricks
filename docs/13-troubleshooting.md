# Troubleshooting Guide

Common issues and solutions for Speech-To-Text-With-Databricks.

## Table of Contents

- [GitHub Actions / CI/CD Issues](#github-actions--cicd-issues)
- [Databricks Authentication Issues](#databricks-authentication-issues)
- [Deployment Issues](#deployment-issues)
- [Local Development Issues](#local-development-issues)
- [Configuration Issues](#configuration-issues)
- [Path Filter Issues](#path-filter-issues)

## GitHub Actions / CI/CD Issues

### Workflow Doesn't Trigger

**Symptoms**: Push to branch doesn't trigger workflow

**Possible Causes**:

1. **Changes not in filtered paths**
   ```
   Workflows only run on changes to:
   - speech_to_text_asset_bundle/**
   - .github/workflows/**
   ```

   **Solution**: Ensure changes are in these directories. Changes to `docs/`, `README.md`, etc. won't trigger workflows.

2. **Wrong branch**
   - `sync_git_folder_dev.yml` only runs on `dev` branch
   - `deploy_asset_bundle_prod.yml` only runs on `main` branch

   **Solution**: Push to the correct branch

3. **Workflow disabled**

   **Solution**: 
   - Go to **Actions** tab in GitHub
   - Find the workflow
   - Check if it's enabled

**Verification**:
```bash
# Check which files changed
git diff --name-only HEAD~1

# Verify branch
git branch --show-current
```

### Authentication Fails: "Unable to exchange GitHub token"

**Symptoms**: Workflow fails with OIDC authentication error

**Possible Causes**:

1. **Missing or incorrect DATABRICKS_CLIENT_ID**

   **Solution**:
   - Go to Settings → Environments → [Dev/Prod] → Secrets
   - Verify `DATABRICKS_CLIENT_ID` matches service principal UUID
   - UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

2. **Federation policy not configured or incorrect**

   **Solution**: Verify federation policy in Databricks:
   ```
   Issuer: https://token.actions.githubusercontent.com
   Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev
   Audiences: <service-principal-uuid>
   ```

   - Subject must match repository and environment **exactly**
   - If you forked the repo, update the subject with your GitHub username

3. **Service principal lacks permissions**

   **Solution**:
   - In Databricks workspace settings, add service principal
   - Grant at least **User** role (Admin for full access)

4. **Workflow permissions not set**

   **Solution**: Verify workflow has:
   ```yaml
   permissions:
     id-token: write
     contents: read
   ```

**Verification**:
```bash
# Check workflow file
cat .github/workflows/sync_git_folder_dev.yml | grep -A 5 "permissions:"

# Verify environment in GitHub
# Settings → Environments → Dev → View
```

### Workflow Fails: "databricks repos update failed"

**Symptoms**: Dev workflow fails at Git folder update step

**Possible Causes**:

1. **Git repository not created in Databricks**

   **Solution**:
   - Open Databricks workspace
   - Go to Workspace → Shared
   - Create Git repository:
     - URL: `https://github.com/alessandro9110/Speech-To-Text-With-Databricks`
     - Path: `/Workspace/Shared/Speech-To-Text-With-Databricks`
     - Branch: `dev`

2. **Service principal lacks folder permissions**

   **Solution**:
   - In Databricks, navigate to `/Workspace/Shared/`
   - Right-click → Permissions
   - Add service principal with `CAN_MANAGE` permission

3. **Incorrect path in workflow**

   **Solution**: Verify workflow uses correct path:
   ```yaml
   run: databricks repos update /Workspace/Shared/Speech-To-Text-With-Databricks --branch dev
   ```

### Workflow Fails: "databricks bundle deploy failed"

**Symptoms**: Prod workflow fails at bundle deploy step

**Possible Causes**:

1. **Bundle validation fails**

   **Solution**: Test locally:
   ```bash
   cd speech_to_text_asset_bundle
   databricks bundle validate --target prod \
     --var="databricks_host=https://..." \
     --var="admin_user_email=admin@example.com"
   ```

2. **Missing variables**

   **Solution**: For prod deployment, ensure `admin_user_email` is set. Update workflow or create `databricks.yml.local` in repository (but don't commit it).

3. **Service principal lacks deployment permissions**

   **Solution**: Grant service principal necessary permissions for:
   - Creating jobs
   - Creating pipelines
   - Creating schemas
   - Deploying to `/Workspace/Shared/`

## Databricks Authentication Issues

### Local: "Error: No authentication configured"

**Symptoms**: `databricks` commands fail with authentication error

**Solution**:
```bash
# Configure authentication
databricks auth login --host https://your-workspace.cloud.databricks.com

# Or set environment variables
export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
export DATABRICKS_TOKEN=your-token

# Verify authentication
databricks auth whoami
```

### Local: "Error: invalid host"

**Symptoms**: Authentication fails with invalid host error

**Solution**:
- Verify URL format: `https://<workspace-id>.cloud.databricks.com` (no trailing slash)
- Check if workspace URL is correct
- Ensure you have access to the workspace

## Deployment Issues

### Bundle Validation Fails

**Symptoms**: `databricks bundle validate` returns errors

**Common Errors**:

1. **"variable 'X' has not been set"**

   **Solution**: Provide the variable:
   ```bash
   databricks bundle validate --target dev \
     --var="databricks_host=https://..."
   ```

   Or create `databricks.yml.local`:
   ```yaml
   targets:
     dev:
       variables:
         databricks_host: https://your-workspace.cloud.databricks.com
   ```

2. **"invalid YAML"**

   **Solution**: Check YAML syntax:
   ```bash
   # Install yamllint
   pip install yamllint

   # Check files
   yamllint databricks.yml
   yamllint resources/*.yml
   ```

3. **"resource not found"**

   **Solution**: Verify resource files are included:
   ```yaml
   include:
     - resources/*.yml
     - resources/*/*.yml
   ```

### Deployment Succeeds But Resources Not Created

**Symptoms**: Deployment completes but jobs/pipelines missing

**Possible Causes**:

1. **Wrong target**

   **Solution**: Verify target in deployment command:
   ```bash
   # For dev
   databricks bundle deploy --target dev

   # For prod
   databricks bundle deploy --target prod
   ```

2. **Resources filtered by presets**

   **Solution**: Check if presets affect your resources (e.g., `name_prefix`)

3. **Deployment to wrong workspace**

   **Solution**: Verify workspace host in configuration

**Verification**:
```bash
# List deployed resources
databricks jobs list | grep sample_job
databricks pipelines list | grep speech_to_text
```

## Local Development Issues

### Import Errors: "No module named 'speech_to_text_asset_bundle'"

**Symptoms**: Python can't find the module

**Solution**:
```bash
cd speech_to_text_asset_bundle

# Install in editable mode
pip install -e .
# or
pip install -e ".[dev]"
# or
uv sync --dev
```

### Tests Fail: "databricks-connect not configured"

**Symptoms**: Tests fail with databricks-connect errors

**Solution**:
```bash
# Install databricks-connect
pip install "databricks-connect>=15.4,<15.5"

# Configure (optional for basic tests)
databricks-connect configure
```

### Linting Fails: "ruff command not found"

**Symptoms**: Can't run ruff linter

**Solution**:
```bash
# Install dev dependencies
cd speech_to_text_asset_bundle
pip install -e ".[dev]"

# Or install ruff directly
pip install ruff

# Run linter
ruff check .
```

### Build Fails: "uv command not found"

**Symptoms**: Can't build wheel with uv

**Solution**:
```bash
# Install uv
pip install uv

# Or use alternative build tool
pip install build
python -m build --wheel
```

## Configuration Issues

### Variable Not Applied

**Symptoms**: Variable in `databricks.yml.local` not used

**Possible Causes**:

1. **Wrong file location**

   **Solution**: File must be at `speech_to_text_asset_bundle/databricks.yml.local`

2. **Wrong YAML structure**

   **Solution**: Verify structure:
   ```yaml
   targets:
     dev:
       variables:
         databricks_host: https://...
   ```

3. **File committed to git**

   **Solution**: 
   - File should be in `.gitignore`
   - Remove from git: `git rm --cached databricks.yml.local`

### Can't Find .databricks.yml.example

**Symptoms**: Looking for example configuration file

**Solution**:
```bash
# File is at
cat speech_to_text_asset_bundle/.databricks.yml.example

# Create your local config
cp speech_to_text_asset_bundle/.databricks.yml.example \
   speech_to_text_asset_bundle/databricks.yml.local

# Edit with your values
```

## Path Filter Issues

### Documentation Changes Trigger Workflow

**Symptoms**: Expected workflow to NOT run on doc changes

**Solution**: This is correct behavior if:
- Changes include files in `speech_to_text_asset_bundle/**`
- Changes include files in `.github/workflows/**`

Workflows will not run if changes are ONLY to:
- `docs/**`
- `*.md` files in root
- Other non-filtered paths

**Verification**:
```bash
# Check what changed in commit
git diff --name-only HEAD~1

# If any file matches the filter, workflow runs
```

### Workflow Should Run But Doesn't

**Symptoms**: Changed filtered files but workflow didn't run

**Possible Causes**:

1. **Syntax error in path filter**

   **Solution**: Verify workflow path filter:
   ```yaml
   on:
     push:
       paths:
         - 'speech_to_text_asset_bundle/**'
         - '.github/workflows/**'
   ```

2. **Branch protection rules**

   **Solution**: Check repository Settings → Branches

## Getting More Help

### Enable Debug Logging

For GitHub Actions:
1. Go to Settings → Secrets and variables → Actions
2. Add repository secret: `ACTIONS_STEP_DEBUG` = `true`
3. Re-run workflow

For Databricks CLI:
```bash
# Add --debug flag
databricks bundle deploy --target dev --debug

# Or set environment variable
export DATABRICKS_DEBUG=1
databricks bundle validate
```

### Check Logs

**GitHub Actions**:
- Go to Actions tab
- Click on workflow run
- Expand failed step to see detailed logs

**Databricks**:
- Jobs: Job Runs → Click run → View logs
- Pipelines: Pipeline → Updates → Click update → View logs

### Useful Commands

```bash
# Verify authentication
databricks auth whoami

# List workspaces
databricks auth profiles

# Test connectivity
databricks repos list

# Validate without deploying
databricks bundle validate --target dev

# Dry-run deployment
databricks bundle deploy --target dev --dry-run

# Force deployment (bypass checks - use with caution)
databricks bundle deploy --target dev --force
```

### Still Stuck?

1. **Check Databricks Documentation**: [Asset Bundles Docs](https://docs.databricks.com/dev-tools/bundles/)
2. **Review workflow logs** carefully for specific error messages
3. **Compare with working examples** in the repository
4. **Open an issue** in the GitHub repository with:
   - What you tried to do
   - What happened (error messages, logs)
   - What you expected
   - Environment details (OS, Python version, etc.)

## Common Error Messages Reference

| Error Message | Common Cause | Solution |
|---------------|--------------|----------|
| "variable 'X' has not been set" | Missing variable | Provide via CLI or databricks.yml.local |
| "Unable to exchange GitHub token" | OIDC setup incorrect | Check federation policy and CLIENT_ID |
| "permission denied" | Insufficient permissions | Grant service principal access |
| "repository not found" | Git repo not created | Create repo in Databricks workspace |
| "invalid host" | Wrong URL format | Use https://<workspace>.cloud.databricks.com |
| "No module named..." | Package not installed | Run `pip install -e .` |
| "databricks command not found" | CLI not installed | Run `pip install databricks-cli` |

## Prevention Best Practices

To avoid issues:

✅ Always validate before deploying: `databricks bundle validate`  
✅ Test in dev before promoting to prod  
✅ Run linter and tests before committing  
✅ Use `databricks.yml.local` for local config (never commit it)  
✅ Keep federation policies up to date  
✅ Document any custom configuration  
✅ Review workflow logs after successful deployments  
✅ Keep dependencies up to date
