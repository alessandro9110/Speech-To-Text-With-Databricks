# GitHub Actions Setup Guide

**Purpose**: Step-by-step instructions for configuring GitHub Environments, variables, and secrets required for CI/CD automation.

**Scope**: GitHub environment configuration for Dev and Prod deployments, OIDC authentication setup.

**Prerequisites**: Complete [Databricks Setup](DATABRICKS_SETUP.md) first to obtain the service principal client ID and configure federation policies.

---

## Overview

This repository uses GitHub Actions to automate deployment of the Databricks Asset Bundle:

- **Dev Environment**: Syncs code to Databricks Git folder and deploys bundle on push to `dev` branch
- **Prod Environment**: Deploys bundle to production on push to `main` branch

Both workflows authenticate using **GitHub OIDC** (OpenID Connect) with short-lived tokens instead of long-lived secrets.

---

## 1. Create GitHub Environments

Create separate environments for Dev and Prod deployments:

### Step 1.1: Create Dev Environment

1. Go to your repository **Settings** → **Environments**
2. Click **New environment**
3. Name it: `Dev`
4. Click **Configure environment**
5. (Optional) Add protection rules if needed

### Step 1.2: Create Prod Environment

1. Go to your repository **Settings** → **Environments**
2. Click **New environment**
3. Name it: `Prod`
4. Click **Configure environment**
5. **Recommended**: Enable **Required reviewers** to protect production deployments
   - Add at least one reviewer who must approve production deployments
   - This prevents accidental deployments to production

---

## 2. Configure Dev Environment

### Variables

In the **Dev** environment, add the following **Environment variables**:

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `DATABRICKS_HOST` | Your Databricks workspace URL | `https://<workspace>.cloud.databricks.com` |

**How to add**:
1. Navigate to **Settings** → **Environments** → **Dev**
2. Scroll to **Environment variables**
3. Click **Add variable**
4. Enter name: `DATABRICKS_HOST`
5. Enter value: your workspace URL
6. Click **Add variable**

### Secrets

In the **Dev** environment, add the following **Environment secrets**:

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `DATABRICKS_CLIENT_ID` | Service principal Application ID (UUID) | From Databricks Account Console → Service principals (see [Databricks Setup](DATABRICKS_SETUP.md)) |

**How to add**:
1. Navigate to **Settings** → **Environments** → **Dev**
2. Scroll to **Environment secrets**
3. Click **Add secret**
4. Enter name: `DATABRICKS_CLIENT_ID`
5. Enter value: the service principal UUID from Databricks
6. Click **Add secret**

---

## 3. Configure Prod Environment

### Variables

In the **Prod** environment, add the following **Environment variables**:

| Variable Name | Description | Example Value |
|---------------|-------------|---------------|
| `DATABRICKS_HOST` | Your Databricks workspace URL | `https://<workspace>.cloud.databricks.com` |
| `ADMIN_USER_EMAIL` | (Optional) Admin user email for CAN_MANAGE permissions | `admin@example.com` |

**Note**: `ADMIN_USER_EMAIL` is optional. It can be used to grant a human admin CAN_MANAGE permissions on all prod bundle resources. To enable, uncomment the permissions block in `databricks.yml` (prod target).

### Secrets

In the **Prod** environment, add the following **Environment secrets**:

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `DATABRICKS_CLIENT_ID` | Service principal Application ID (UUID) | From Databricks Account Console → Service principals (see [Databricks Setup](DATABRICKS_SETUP.md)) |

---

## 4. Verify Configuration

### Check Workflows

The repository includes two GitHub Actions workflows:

1. **`sync_git_folder_and_deploy_adb_dev.yml`**
   - Triggers on push to `dev` branch
   - Uses `Dev` environment
   - Syncs Git folder and deploys to dev target

2. **`sync_git_folder_and_deploy_adb_prod.yml`**
   - Triggers on push to `main` branch
   - Uses `Prod` environment
   - Deploys bundle to prod target

### Test the Configuration

After configuring environments:

1. Push a change to the `dev` branch (or manually trigger the workflow)
2. Go to **Actions** tab in the repository
3. Verify the "Sync Git Folder and Deploy Dev" workflow runs successfully
4. Check the workflow logs for any errors

---

## How GitHub OIDC Authentication Works

1. GitHub Actions workflow starts and requests an OIDC token from GitHub
2. GitHub issues a short-lived JWT token with claims (repository, environment, etc.)
3. Workflow sends the token to Databricks
4. Databricks validates the token against the federation policy
5. If valid, Databricks issues a temporary access token
6. Workflow uses the access token to execute Databricks CLI commands

**Security benefits**:
- No long-lived secrets stored in GitHub
- Tokens are short-lived (typically 1 hour)
- Federation policies restrict which repositories/environments can authenticate

---

## Troubleshooting

### Error: "DATABRICKS_HOST is not set"

**Solution**:
- Verify `DATABRICKS_HOST` is configured as a variable (not secret) in the correct environment
- Ensure the environment name in the workflow matches exactly (`Dev` or `Prod`)

### Error: "DATABRICKS_CLIENT_ID is not set"

**Solution**:
- Verify `DATABRICKS_CLIENT_ID` is configured as a secret in the correct environment
- Check that the value is the correct UUID from the service principal

### OIDC Authentication Fails

**Solution**:
- Verify the service principal federation policy subject matches: `repo:<org>/<repo>:environment:<Env>`
- If you forked the repository, update the subject pattern in the federation policy
- Ensure the service principal has workspace access
- Check that `id-token: write` permission is set in the workflow (already present)

### Workflow Cannot Update Git Folder (Dev)

**Solution**:
- Verify the Git folder exists at `/Workspace/Shared/Speech-To-Text-With-Databricks`
- Ensure the service principal has `CAN_MANAGE` permission on the folder
- Check that the repository URL and branch are correct

### Bundle Deployment Fails

**Solution**:
- Verify the service principal has appropriate permissions for asset bundle deployment
- Check the `databricks.yml` configuration for the target
- Review workflow logs for specific error messages
- Ensure the catalog `speech_to_text` exists and service principal has permissions

---

## References

- [Databricks - Enable Workload Identity Federation for GitHub Actions](https://docs.databricks.com/dev-tools/auth/provider-github.html)
- [GitHub Docs - Using Environments for Deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Docs - Configuring OpenID Connect in Cloud Providers](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers)
- [Back to README](../README.md)
