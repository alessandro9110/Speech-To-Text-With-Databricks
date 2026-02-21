# Databricks Setup Guide

**Purpose**: Step-by-step instructions for configuring Databricks resources required for the Speech-to-Text solution.

**Scope**: Service Principal creation, catalog and schema setup, federation policies for GitHub Actions OIDC authentication.

---

## Prerequisites

- Databricks Account with Account Administrator access
- A Databricks workspace (AWS, Azure, or GCP)
- Administrative access to create service principals and manage permissions

---

## 1. Create the Catalog

Before deploying the asset bundle, create the required catalog in Databricks:

**Catalog Name**: `speech_to_text`

**Note**: Unity Catalog requires lowercase identifiers with underscores. The catalog uses `speech_to_text` (snake_case) while the repository uses `Speech-To-Text-With-Databricks` (kebab-case) to follow each platform's naming conventions.

### Steps

1. Navigate to your Databricks workspace
2. Go to **Data** in the left sidebar
3. Click **Create Catalog**
4. Enter the catalog name: `speech_to_text`
5. Click **Create**

**Note**: The service principal (configured below) will need permissions on this catalog.

---

## 2. Create a Service Principal

The solution uses a Service Principal for secure authentication between GitHub Actions and Databricks.

### Step 2.1: Create the Service Principal

**Via Databricks UI**:

1. Navigate to **Account Console** → **User management** → **Service principals**
2. Click **Add service principal**
3. Enter a name (e.g., "GitHub Actions Deploy Principal")
4. Save and note the **Application ID (Client ID)** — this UUID will be used in GitHub Secrets

**Via Databricks CLI**:

```bash
databricks account service-principals create --display-name "GitHub Actions Deploy Principal"
```

### Step 2.2: Assign Workspace Permissions

Grant the service principal access to your workspace:

1. Go to your **Workspace settings** → **Permissions**
2. Add the service principal with appropriate permissions (e.g., "User" or "Admin")

### Step 2.3: Grant Catalog and Schema Permissions

The service principal needs the following permissions:

```sql
-- Grant permissions on the catalog
GRANT USE CATALOG ON CATALOG speech_to_text TO `<service_principal_application_id>`;

-- Grant permissions on schemas
GRANT USE SCHEMA, CREATE TABLE ON SCHEMA speech_to_text.audio TO `<service_principal_application_id>`;
GRANT USE SCHEMA, CREATE TABLE ON SCHEMA speech_to_text.prod TO `<service_principal_application_id>`;

-- Grant permissions on volumes (created by the bundle)
GRANT READ VOLUME, WRITE VOLUME ON VOLUME speech_to_text.audio.files TO `<service_principal_application_id>`;
```

**Note**: Replace `<service_principal_application_id>` with the UUID from Step 2.1.

---

## 3. Configure OIDC Federation Policies

Federation policies allow GitHub Actions to securely authenticate with Databricks using short-lived OIDC tokens (no long-lived secrets required).

### Dev Environment Federation Policy

Create the policy in the Account Console:

1. Go to **User Management** → **Service principals** → select your service principal
2. Click **Create Policy** (or **Add Federation Policy**)
3. Configure the policy:
   - **Issuer URL**: `https://token.actions.githubusercontent.com`
   - **Subject**: `repo:<your_github_org>/<your_repo_name>:environment:Dev`
     - Example: `repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev`
   - **Audiences**: `<service_principal_application_id>` (the UUID)
4. Save the policy

### Prod Environment Federation Policy

Repeat the steps above with a different subject:

- **Subject**: `repo:<your_github_org>/<your_repo_name>:environment:Prod`
  - Example: `repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Prod`

**Note**: The subject must exactly match the GitHub repository and environment names, or authentication will fail.

**Via Databricks CLI**:

```bash
# Dev environment policy
databricks account service-principal-federation-policy create <SERVICE_PRINCIPAL_ID> --json '{
  "oidc_policy": {
    "issuer": "https://token.actions.githubusercontent.com",
    "audiences": [ "<SERVICE_PRINCIPAL_UUID>" ],
    "subject": "repo:<GITHUB_ORG>/<GITHUB_REPO>:environment:Dev"
  }
}'

# Prod environment policy
databricks account service-principal-federation-policy create <SERVICE_PRINCIPAL_ID> --json '{
  "oidc_policy": {
    "issuer": "https://token.actions.githubusercontent.com",
    "audiences": [ "<SERVICE_PRINCIPAL_UUID>" ],
    "subject": "repo:<GITHUB_ORG>/<GITHUB_REPO>:environment:Prod"
  }
}'
```

---

## 4. Create Git Repository in Databricks (Dev Only)

For the Dev environment, which uses Git folder synchronization:

1. Open your Databricks workspace
2. Navigate to **Workspace** → **Shared**
3. Click **Create** → **Git folder**
4. Enter your repository URL: `https://github.com/<your-org>/<your-repo-name>`
   - Example: `https://github.com/alessandro9110/Speech-To-Text-With-Databricks`
5. Name the folder: `Speech-To-Text-With-Databricks` (or your repository name)
6. Default branch: `dev`
7. Click **Create**

**Note**: If you forked this repository, use your fork's URL. This step is only required for the Dev environment. The Prod environment uses direct asset bundle deployment.

---

## Verification

After completing the setup:

1. Verify the catalog exists: `SHOW CATALOGS LIKE 'speech_to_text';`
2. Verify service principal has permissions: `SHOW GRANTS ON CATALOG speech_to_text;`
3. Verify federation policies: Check in Account Console → Service principals → Federation policies

---

## Troubleshooting

### Service Principal Cannot Access Catalog

**Solution**:
- Verify `GRANT` statements were executed successfully
- Check that the service principal UUID is correct
- Ensure the workspace is attached to Unity Catalog

### Federation Policy Authentication Fails

**Solution**:
- Verify the subject pattern exactly matches: `repo:<org>/<repo>:environment:<env>`
- Confirm the service principal UUID is correct in the audiences field
- Check that GitHub Actions has `id-token: write` permission

### Git Folder Sync Fails

**Solution**:
- Verify the Git folder exists at `/Workspace/Shared/Speech-To-Text-With-Databricks`
- Ensure the service principal has `CAN_MANAGE` permission on the folder
- Check that the repository URL and branch are correct

---

## References

- [Databricks Service Principals Documentation](https://docs.databricks.com/administration-guide/users-groups/service-principals.html)
- [Enable Workload Identity Federation for GitHub Actions](https://docs.databricks.com/dev-tools/auth/provider-github.html)
- [Unity Catalog Permissions](https://docs.databricks.com/data-governance/unity-catalog/manage-privileges/index.html)
