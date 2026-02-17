# GitHub Actions Environment Setup

This document explains how to configure the variables and secrets required for the `sync_git_folder_dev.yml` workflow.

## Prerequisites

1. A Databricks service principal configured with workload identity federation for GitHub Actions
2. Administrative access to the GitHub repository to configure environments

## Configuring the "Dev" Environment

The `sync_git_folder_dev.yml` workflow requires the following variables and secrets configured in the GitHub environment named **"Dev"**.

### Step 1: Create the Environment

If the "Dev" environment doesn't already exist:

1. Go to the GitHub repository settings
2. Navigate to **Settings** > **Environments**
3. Click on **New environment**
4. Name the environment: `Dev`
5. Click on **Configure environment**

### Step 2: Configure Variables

In the "Dev" environment, add the following **Environment variables**:

| Variable Name | Description | Example |
|---------------|-------------|---------|
| `DATABRICKS_HOST` | The Databricks workspace URL | `https://dbc-3cceb672-6c68.cloud.databricks.com` |

**How to add:**
1. In the "Dev" environment configuration page
2. Scroll to the **Environment variables** section
3. Click on **Add variable**
4. Enter the name and value
5. Click on **Add variable**

### Step 3: Configure Secrets

In the "Dev" environment, add the following **Environment secrets**:

| Secret Name | Description | How to obtain |
|-------------|-------------|---------------|
| `DATABRICKS_CLIENT_ID` | The client ID (UUID) of the service principal configured for OIDC authentication | Obtain it from the service principal configuration in Databricks |

**How to add:**
1. In the "Dev" environment configuration page
2. Scroll to the **Environment secrets** section
3. Click on **Add secret**
4. Enter the name and value
5. Click on **Add secret**

## OIDC Authentication with Databricks

The workflow uses GitHub OIDC (OpenID Connect) to authenticate with Databricks, which is a more secure method compared to using long-lived tokens.

### OIDC Requirements:

1. **Service Principal in Databricks**: You must have a service principal configured in your Databricks account
2. **Federation Policy**: The service principal must have a federation policy that allows access from GitHub Actions

### Service Principal Configuration (if not already done):

```bash
# Create a federation policy for the service principal
databricks account service-principal-federation-policy create <SERVICE_PRINCIPAL_ID> --json '{
  "oidc_policy": {
    "issuer": "https://token.actions.githubusercontent.com",
    "audiences": [ "<DATABRICKS_ACCOUNT_ID>" ],
    "subject": "repo:<GITHUB_ORG>/<GITHUB_REPO>:environment:Dev"
  }
}'
```

**Note**: Replace `<GITHUB_ORG>/<GITHUB_REPO>` with `alessandro9110/Speech-To-Text-With-Databricks` for this repository.

## Configuration Verification

After configuring the variables and secrets:

1. Go to the **Actions** tab in the repository
2. Find the "Sync Git Folder Dev" workflow
3. If necessary, manually run the workflow to test the configuration
4. Verify that the workflow completes successfully

## Troubleshooting

### Error: "DATABRICKS_HOST is not set"
- Verify that the `DATABRICKS_HOST` variable is configured in the "Dev" environment
- Ensure that the environment name in the workflow exactly matches the configured one

### Error: "DATABRICKS_CLIENT_ID is not set"
- Verify that the `DATABRICKS_CLIENT_ID` secret is configured in the "Dev" environment
- Ensure that the value is correct

### OIDC authentication error
- Verify that the service principal has the federation policy configured correctly
- Verify that the `subject` in the policy matches the repository and environment pattern
- Ensure that the `id-token: write` permissions are set in the workflow (already present)

## References

- [Databricks - Enable workload identity federation for GitHub Actions](https://docs.databricks.com/dev-tools/auth/provider-github)
- [GitHub Docs - Using environments for deployment](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Docs - Configuring OpenID Connect in cloud providers](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers)
