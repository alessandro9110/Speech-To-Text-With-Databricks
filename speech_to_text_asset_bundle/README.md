# speech_to_text_asset_bundle

The 'speech_to_text_asset_bundle' asset bundle was generated using the Default Python template.

## Getting Started

To deploy and manage this asset bundle, follow these steps:

### 1. Configuration

Before deployment, you need to configure the required variables. There are two methods:

#### Method 1: Using Command Line Variables

Deploy with inline variables:

```bash
# For dev environment
databricks bundle deploy --target dev --var="databricks_host=https://your-workspace.cloud.databricks.com"

# For prod environment
databricks bundle deploy --target prod \
  --var="databricks_host=https://your-workspace.cloud.databricks.com" \
  --var="admin_user_email=your-email@example.com"
```

#### Method 2: Using Local Configuration File

Create a `databricks.yml.local` file (git-ignored) in this directory with your values:

```yaml
targets:
  dev:
    variables:
      databricks_host: https://your-workspace.cloud.databricks.com
  
  prod:
    variables:
      databricks_host: https://your-workspace.cloud.databricks.com
      admin_user_email: your-email@example.com
```

**Required Variables:**
- `databricks_host`: Your Databricks workspace URL
- `admin_user_email`: Admin email for production permissions (prod target only)

See `.databricks.yml.example` for a complete example configuration.

### 2. Deployment

- Click the **deployment rocket** 🚀 in the left sidebar to open the **Deployments** panel, then click **Deploy**.

### 3. Running Jobs & Pipelines

- To run a deployed job or pipeline, hover over the resource in the **Deployments** panel and click the **Run** button.

### 4. Managing Resources

- Use the **Add** dropdown to add resources to the asset bundle.
- Click **Schedule** on a notebook within the asset bundle to create a **job definition** that schedules the notebook.

## Documentation

- For information on using **Databricks Asset Bundles in the workspace**, see: [Databricks Asset Bundles in the workspace](https://docs.databricks.com/aws/en/dev-tools/bundles/workspace-bundles)
- For details on the **Databricks Asset Bundles format** used in this asset bundle, see: [Databricks Asset Bundles Configuration reference](https://docs.databricks.com/aws/en/dev-tools/bundles/reference)
