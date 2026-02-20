# Speech-To-Text-With-Databricks

A Databricks asset bundle solution for speech-to-text processing with automated deployment via GitHub Actions.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
  - [1. Databricks Catalog Creation](#1-databricks-catalog-creation)
  - [2. Databricks Service Principal Setup](#2-databricks-service-principal-setup)
  - [3. GitHub Actions Configuration](#3-github-actions-configuration)
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

### 1. Databricks Catalog Creation

Before deploying the asset bundle, you must manually create the required catalog in Databricks:

**Catalog Name:** **`text_to_speech`** (used by both Dev and Prod environments)

**Steps to create a catalog:**
1. Navigate to your Databricks workspace
2. Go to **Data** in the left sidebar
3. Click **Create Catalog**
4. Enter the catalog name: `text_to_speech`
5. Click **Create**

**Note:** Ensure the service principal (configured in the next step) has the necessary permissions on this catalog.

### 2. Databricks Service Principal Creation

The solution uses a service principal for authentication between GitHub Actions and Databricks. 
Follow these steps to create and configure it.

#### Step 2.1: Create a Service Principal

Using the Databricks UI, create a service principal:
Via the [Databricks UI](https://docs.databricks.com/administration-guide/users-groups/service-principals.html):
1. Navigate to **Account Console** -> **User management** -> **Service principals**
2. Click **Add service principal**
3. Enter a name (e.g., "GitHub Actions Deploy Principal")
4. Save and note the **Application ID (Client ID)**

#### Step 2.2: Assign Workspace Permissions

Grant the service principal access to your workspace:
1. Go to your **Workspace settings** -> **Permissions**
2. Add the service principal with appropriate permissions (e.g., "User" or "Admin")

#### Step 2.3: Configure OIDC Federation Policy

Federation policies allow your automated workloads running outside of Databricks to securely access Databricks APIs, using tokens provided by the workload runtime.

Create the Federation Policy in the Accoun Console:
1. Go to **User Managment** -> **Service principals** -> **GitHub Actions Deploy Principal**
2. Click on **Create Policy** and pass the following values:
   . Issuer URL: https://token.actions.githubusercontent.com
   . Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev (if you Forked or CLoned the repo, use your account_id instead of alessandro9110)
   . Audiences: Service Principal UUID

**Note:** the Federation Policy is only available into Account Console and not for Free Edition.

#### Step 2.4: Create the Git Repo in the Dev environment
In the Dev workspace, create the git repository in the path: Workspace/Shared/

**Note**: This step is only required for the Dev environment, which uses Git folder synchronization. The Prod environment uses direct asset bundle deployment.


### 3. GitHub Actions Configuration

Once the Databricks service principal is configured, set up GitHub Actions:

#### Step 3.1: Create GitHub Environments

Create both Dev and Prod environments:

1. Go to your repository **Settings** > **Environments**
2. Click **New environment**
3. Name it: `Dev`
4. Click **Configure environment**
5. Repeat steps 2-4 for the `Prod` environment

#### Step 3.2: Configure Environment Variables

In both "Dev" and "Prod" environments, add these variables:

| Variable Name | Description | Example Value |
|--------------|-------------|---------------|
| `DATABRICKS_HOST` | Your Databricks workspace URL | `https://xxxxxxxxxxxxxx.cloud.databricks.com` |

#### Step 3.3: Configure Environment Secrets

In both "Dev" and "Prod" environments, add these secrets:

| Secret Name | Description | Value |
|------------|-------------|-------|
| `DATABRICKS_CLIENT_ID` | Service principal Application ID (UUID) | The UUID from Step 2.1 |

#### Step 3.4: Configure OIDC Federation Policy for Prod

Create an additional Federation Policy for the Prod environment:
1. Go to **User Management** -> **Service principals** -> **GitHub Actions Deploy Principal**
2. Click on **Create Policy** and pass the following values:
   - Issuer URL: https://token.actions.githubusercontent.com
   - Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Prod
   - Audiences: Service Principal UUID

**📖 For detailed GitHub Actions environment setup instructions for the Dev environment**, see [docs/ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md). The Prod environment follows the same pattern, plus the additional policy configuration described above.

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

# Deploy to dev environment with variables
databricks bundle deploy --target dev --var="databricks_host=https://your-workspace.cloud.databricks.com"

# Deploy to prod environment with variables
databricks bundle deploy --target prod \
  --var="databricks_host=https://your-workspace.cloud.databricks.com" \
  --var="admin_user_email=your-email@example.com"
```

**Note:** For local deployments, you can create a `databricks.yml.local` file with your configuration to avoid passing variables on the command line. See [speech_to_text_asset_bundle/README.md](speech_to_text_asset_bundle/README.md) for details.

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
├── .ai-dev-kit/                     # AI Dev Kit versioning and (optionally) skills for local/experimental use
├── .claude/                         # Claude agent skills (mirrors .github/skills for Anthropic/Claude integrations)
├── .github/                         # GitHub configuration, CI/CD workflows, Copilot/agent skills
│   └── skills/                      # Skills for Copilot/AI agents (Databricks, MLflow, etc.)
├── docs/                            # Additional project documentation
├── speech_to_text_asset_bundle/     # Databricks Asset Bundle solution
├── .gitignore                       # Repository-level Git ignore rules
├── LICENSE                          # Project license
└── README.md                        # This file - main project documentation
```

### Folder Descriptions

#### `.ai-dev-kit/`
Contains versioning for the AI Dev Kit and (optionally) local/experimental skills. Used for local agent/skill development or version pinning.

#### `.claude/`
Contains skills for Claude/Anthropic agent integrations. Mirrors the structure of `.github/skills` but is used for Anthropic/Claude-specific agent skills.

#### `.github/`
Contains GitHub-specific configuration, CI/CD workflows, Copilot agent definitions, and skills for Copilot/AI agents.
   - `workflows/`: GitHub Actions workflow definitions for CI/CD automation
   - `skills/`: Skills for Copilot/AI agents (Databricks, MLflow, etc.)
   - `agents/`: Custom Copilot agent definitions
   - `instructions/`: Guidelines and workflow rules
   - `copilot-instructions.md`: Global Copilot configuration and code review rules

#### `docs/`
Additional documentation beyond the main README:
   - `ENVIRONMENT_SETUP.md`: Step-by-step guide for configuring GitHub Actions environments
   - `copilot-agents.md`: Documentation on custom Copilot agents available in this repository

#### `speech_to_text_asset_bundle/`
The core Databricks Asset Bundle solution for speech-to-text processing. Contains:
   - Configuration files (databricks.yml, pyproject.toml)
   - Resource definitions (jobs, pipelines)
   - Source code (Python packages, DLT transformations, notebooks)
   - Tests and fixtures

**For detailed documentation of the asset bundle structure and development workflow**, see [speech_to_text_asset_bundle/README.md](speech_to_text_asset_bundle/README.md)

## Additional Documentation

- **[GitHub Actions Environment Setup](docs/ENVIRONMENT_SETUP.md)** - Detailed guide for configuring GitHub Actions
- **[Copilot Agents Documentation](docs/copilot-agents.md)** - Information about custom Copilot agents in this repository
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

### For more troubleshooting help, see the [ENVIRONMENT_SETUP.md](docs/ENVIRONMENT_SETUP.md#troubleshooting) documentation.

---

## License

See [LICENSE](LICENSE) for details.
