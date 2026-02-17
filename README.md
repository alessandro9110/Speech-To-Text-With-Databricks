# Speech-To-Text-With-Databricks

A Databricks asset bundle solution for speech-to-text processing with automated deployment via GitHub Actions.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
  - [1. Databricks Service Principal Setup](#1-databricks-service-principal-setup)
  - [2. GitHub Actions Configuration](#2-github-actions-configuration)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Additional Documentation](#additional-documentation)

## Overview

This repository contains a Databricks Asset Bundle for speech-to-text processing. The solution uses:

- **Databricks Asset Bundles** for infrastructure-as-code deployment
- **GitHub Actions** for CI/CD automation with OIDC authentication
- **Service Principal** for secure, token-less authentication between GitHub and Databricks

## Prerequisites

Before setting up this solution, ensure you have:

1. **Databricks Account**
   - Account administrator access (Account Console)
   - A Databricks workspace (AWS, Azure, or GCP)

2. **GitHub Repository**
   - Administrative access to configure environments and secrets
   - Repository: `alessandro9110/Speech-To-Text-With-Databricks`

3. **Databricks CLI (Optional)**
   - Install: `pip install databricks-cli` or use [Databricks CLI installation guide](https://docs.databricks.com/dev-tools/cli/index.html)

## Initial Setup

### 1. Databricks Service Principal Creation

The solution uses a service principal for authentication between GitHub Actions and Databricks. 
Follow these steps to create and configure it.

#### Step 1.1: Create a Service Principal

Using the Databricks UI, create a service principal:
Via the [Databricks UI](https://docs.databricks.com/administration-guide/users-groups/service-principals.html):
1. Navigate to **Account Console** -> **User management** -> **Service principals**
2. Click **Add service principal**
3. Enter a name (e.g., "GitHub Actions Deploy Principal")
4. Save and note the **Application ID (Client ID)**

#### Step 1.2: Assign Workspace Permissions

Grant the service principal access to your workspace:
1. Go to your **Workspace settings** -> **Permissions**
2. Add the service principal with appropriate permissions (e.g., "User" or "Admin")

#### Step 1.3: Configure OIDC Federation Policy

Federation policies allow your automated workloads running outside of Databricks to securely access Databricks APIs, using tokens provided by the workload runtime.

Create the Federation Policy in the Accoun Console:
1. Go to **User Managment** -> **Service principals** -> **GitHub Actions Deploy Principal**
2. Click on **Create Policy** and pass the following values:
   . Issuer URL: https://token.actions.githubusercontent.com
   . Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev (if you Forked or CLoned the repo, use your account_id instead of alessandro9110)
   . Audiences: Service Principal UUID

**Note:** the Federation Policy is only available into Account Console and not for Free Edition.

#### Step 1.4: Create the Git Repo in the Dev environment
In the Dev workspace, create the git repository in the path: Workspace/Shared/

**Note**: This step is only required for the Dev environment, which uses Git folder synchronization. The Prod environment uses direct asset bundle deployment.


### 2. GitHub Actions Configuration

Once the Databricks service principal is configured, set up GitHub Actions:

#### Step 2.1: Create GitHub Environments

Create both Dev and Prod environments:

1. Go to your repository **Settings** > **Environments**
2. Click **New environment**
3. Name it: `Dev`
4. Click **Configure environment**
5. Repeat steps 2-4 for the `Prod` environment

#### Step 2.2: Configure Environment Variables

In both "Dev" and "Prod" environments, add these variables:

| Variable Name | Description | Example Value |
|--------------|-------------|---------------|
| `DATABRICKS_HOST` | Your Databricks workspace URL | `https://xxxxxxxxxxxxxx.cloud.databricks.com` |

#### Step 2.3: Configure Environment Secrets

In both "Dev" and "Prod" environments, add these secrets:

| Secret Name | Description | Value |
|------------|-------------|-------|
| `DATABRICKS_CLIENT_ID` | Service principal Application ID (UUID) | The UUID from Step 1.1 |

#### Step 2.4: Configure OIDC Federation Policy for Prod

Create an additional Federation Policy for the Prod environment:
1. Go to **User Management** -> **Service principals** -> **GitHub Actions Deploy Principal**
2. Click on **Create Policy** and pass the following values:
   - Issuer URL: https://token.actions.githubusercontent.com
   - Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Prod
   - Audiences: Service Principal UUID

**📖 For detailed GitHub Actions setup instructions**, see [.github/ENVIRONMENT_SETUP.md](.github/ENVIRONMENT_SETUP.md)

## Deployment

### Automated Deployment (GitHub Actions)

The repository includes two GitHub Actions workflows for automated deployment:

#### Development Deployment
Automatically updates the Git folder in Databricks when code is pushed to the `dev` branch:

```yaml
# Workflow: .github/workflows/sync_git_folder_dev.yml
# Triggers: On push to 'dev' branch
# Environment: Dev
# Authentication: GitHub OIDC → Databricks Service Principal
```

**What happens during deployment:**
1. Code is pushed to the `dev` branch
2. GitHub Actions workflow triggers
3. GitHub generates a short-lived OIDC token
4. Token is exchanged for Databricks access token via the service principal
5. Databricks repositories are updated with the latest code

#### Production Deployment
Automatically deploys the asset bundle to production when code is pushed to the `main` branch:

```yaml
# Workflow: .github/workflows/deploy_asset_bundle_prod.yml
# Triggers: On push to 'main' branch
# Environment: Prod
# Authentication: GitHub OIDC → Databricks Service Principal
```

**What happens during production deployment:**
1. Code is pushed to the `main` branch
2. GitHub Actions workflow triggers
3. GitHub generates a short-lived OIDC token
4. Token is exchanged for Databricks access token via the service principal
5. Asset bundle is deployed to the production target using `databricks bundle deploy --target prod`

### Manual Deployment (Databricks CLI)

You can also deploy manually using the Databricks CLI:

```bash
# Navigate to the asset bundle directory
cd speech_to_text_asset_bundle

# Deploy to dev environment
databricks bundle deploy --target dev

# Deploy to prod environment
databricks bundle deploy --target prod
```

### Deploy Using Databricks UI

For workspace-based deployments:
1. Open the Databricks workspace
2. Navigate to the asset bundle
3. Click the **deployment rocket** 🚀 in the left sidebar
4. Click **Deploy**

For more details, see [speech_to_text_asset_bundle/README.md](speech_to_text_asset_bundle/README.md)

## Project Structure

```
Speech-To-Text-With-Databricks/
├── .github/
│   ├── workflows/
│   │   ├── sync_git_folder_dev.yml         # Dev environment Git sync workflow
│   │   └── deploy_asset_bundle_prod.yml    # Prod environment deployment workflow
│   ├── ENVIRONMENT_SETUP.md                # Detailed GitHub Actions setup
│   └── RIEPILOGO.md                        # Configuration summary
├── speech_to_text_asset_bundle/
│   ├── databricks.yml                      # Asset bundle configuration
│   ├── resources/                          # Job and pipeline definitions
│   ├── src/                                # Source code and transformations
│   └── README.md                           # Asset bundle documentation
└── README.md                               # This file
```

## Additional Documentation

- **[GitHub Actions Environment Setup](.github/ENVIRONMENT_SETUP.md)** - Detailed guide for configuring GitHub Actions
- **[Configuration Summary](.github/RIEPILOGO.md)** - Quick reference for environment variables and secrets
- **[Asset Bundle Documentation](speech_to_text_asset_bundle/README.md)** - Details on managing the Databricks asset bundle
- **[Databricks Asset Bundles](https://docs.databricks.com/dev-tools/bundles/index.html)** - Official Databricks documentation
- **[GitHub OIDC in Databricks](https://docs.databricks.com/dev-tools/auth/provider-github.html)** - Official guide for GitHub Actions integration

## Troubleshooting

### Deployment Fails with Authentication Error

**Issue**: GitHub Actions workflow fails with authentication errors

**Solution**:
1. Verify the service principal federation policy is correctly configured for the target environment (Dev or Prod)
2. Ensure `DATABRICKS_CLIENT_ID` matches the service principal's Application ID
3. Check that the `subject` in the federation policy matches:
   - Dev: `repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev`
   - Prod: `repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Prod`
4. Confirm the service principal has necessary workspace permissions

### Cannot Update Git Folder (Dev Environment)

**Issue**: Dev workflow fails to update the Databricks Git folder

**Solution**:
1. Verify the service principal has `CAN_MANAGE` permission on the target folder
2. Ensure the workspace path in the workflow matches your workspace structure
3. Check that the repository is properly linked in Databricks

### Asset Bundle Deployment Fails (Prod Environment)

**Issue**: Prod workflow fails to deploy the asset bundle

**Solution**:
1. Verify the service principal has appropriate permissions for asset bundle deployment
2. Check the `databricks.yml` configuration for the `prod` target
3. Ensure the workspace path specified in the prod target is accessible
4. Review the workflow logs for specific error messages

### For more troubleshooting help, see the [ENVIRONMENT_SETUP.md](.github/ENVIRONMENT_SETUP.md#troubleshooting) documentation.

---

## License

See [LICENSE](LICENSE) for details.
