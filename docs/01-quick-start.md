# Quick Start Guide

Get up and running with Speech-To-Text-With-Databricks in 10 minutes.

## Prerequisites Check

Before starting, ensure you have:

- [ ] Databricks account with workspace access
- [ ] GitHub account with admin access to the repository
- [ ] Python 3.10+ installed locally (for local development)
- [ ] Databricks CLI installed: `pip install databricks-cli`

## Step 1: Clone Repository (1 minute)

```bash
git clone https://github.com/alessandro9110/Speech-To-Text-With-Databricks.git
cd Speech-To-Text-With-Databricks
```

## Step 2: Configure Databricks Service Principal (3 minutes)

### Create Service Principal

1. Go to **Databricks Account Console**
2. Navigate to **User Management** → **Service Principals**
3. Click **Add service principal**
4. Name it: `GitHub Actions Deploy Principal`
5. **Save the Application ID (UUID)** - you'll need this

### Add OIDC Federation Policies

Create two federation policies for the service principal:

**Dev Environment**:
```
Issuer: https://token.actions.githubusercontent.com
Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev
Audiences: <service-principal-uuid>
```

**Prod Environment**:
```
Issuer: https://token.actions.githubusercontent.com
Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Prod
Audiences: <service-principal-uuid>
```

### Grant Workspace Permissions

1. Go to **Workspace Settings** → **Permissions**
2. Add the service principal with **User** or **Admin** role

## Step 3: Configure GitHub Environments (3 minutes)

### Create Environments

1. Go to repository **Settings** → **Environments**
2. Create two environments: `Dev` and `Prod`

### Configure Dev Environment

**Variables**:
| Name | Value |
|------|-------|
| `DATABRICKS_HOST` | `https://your-workspace.cloud.databricks.com` |

**Secrets**:
| Name | Value |
|------|-------|
| `DATABRICKS_CLIENT_ID` | Service principal UUID from Step 2 |

### Configure Prod Environment

Same as Dev environment (repeat above).

## Step 4: Create Git Repository in Databricks (1 minute)

**For Dev environment only**:

1. Open your Databricks workspace
2. Go to **Workspace** → **Shared**
3. Create Git repository:
   - URL: `https://github.com/alessandro9110/Speech-To-Text-With-Databricks`
   - Path: `/Workspace/Shared/Speech-To-Text-With-Databricks`
   - Branch: `dev`

## Step 5: Test Deployment (2 minutes)

### Test Dev Deployment

```bash
# Create a test commit
git checkout dev
echo "# Test" >> test.md
git add test.md
git commit -m "Test dev deployment"
git push origin dev
```

Check:
1. Go to **Actions** tab in GitHub
2. Verify "Sync Git Folder Dev" workflow runs successfully
3. Check Databricks workspace: `/Workspace/Shared/Speech-To-Text-With-Databricks`

### Test Prod Deployment

```bash
# Merge to main (via PR in real workflow)
git checkout main
git merge dev
git push origin main
```

Check:
1. Go to **Actions** tab in GitHub
2. Verify "Deploy Asset Bundle Prod" workflow runs successfully
3. Check Databricks workspace: `/Workspace/Shared/.bundle/speech_to_text_asset_bundle/prod/`

## Step 6: (Optional) Local Development Setup

```bash
cd speech_to_text_asset_bundle

# Install dependencies
pip install -e ".[dev]"
# or faster: uv sync --dev

# Configure Databricks CLI
databricks auth login --host https://your-workspace.cloud.databricks.com

# Create local configuration
cp .databricks.yml.example databricks.yml.local

# Edit databricks.yml.local with your values
# Then deploy locally
databricks bundle deploy --target dev
```

## Verification Checklist

After completing setup, verify:

- [ ] Service principal created in Databricks
- [ ] Two federation policies configured (Dev and Prod)
- [ ] Service principal has workspace permissions
- [ ] Two GitHub environments created (Dev and Prod)
- [ ] Environment variables set in both environments
- [ ] Environment secrets set in both environments
- [ ] Git repository created in Databricks (Dev only)
- [ ] Dev workflow runs successfully
- [ ] Prod workflow runs successfully
- [ ] (Optional) Local development working

## What You've Set Up

✅ **OIDC Authentication** - Secure, token-less authentication  
✅ **Dev Environment** - For active development with Git sync  
✅ **Prod Environment** - For production deployments  
✅ **CI/CD Pipelines** - Automated deployment on push  
✅ **Databricks Asset Bundle** - Infrastructure as code  

## Next Steps

### Start Development

```bash
# Create a feature branch
git checkout dev
git checkout -b feature/my-feature

# Make changes
cd speech_to_text_asset_bundle
# Edit files...

# Test locally
ruff check .
pytest
databricks bundle validate --target dev

# Commit and push
git add .
git commit -m "Add my feature"
git push origin feature/my-feature

# Create PR to dev branch
```

### Explore the Project

- **Jobs**: Check `resources/sample_job.job.yml`
- **Pipelines**: Check `resources/speech_to_text_asset_bundle_etl.pipeline.yml`
- **Code**: Browse `src/` directory
- **Tests**: Check `tests/` directory

### Learn More

- [Project Overview](00-project-overview.md) - Understand the architecture
- [Development Workflow](08-development-workflow.md) - Learn development best practices
- [Configuration Guide](06-configuration-guide.md) - Understand all configuration options
- [Repository Structure](07-repository-structure.md) - Navigate the codebase

## Troubleshooting

### Workflow Authentication Error

**Problem**: GitHub Actions workflow fails with authentication error

**Solution**:
1. Verify `DATABRICKS_CLIENT_ID` is correct service principal UUID
2. Check federation policy subject matches: `repo:owner/repo:environment:EnvName`
3. Ensure service principal has workspace permissions

### Git Repository Not Found (Dev)

**Problem**: Dev workflow fails - repository not found

**Solution**:
1. Create Git repository in Databricks at `/Workspace/Shared/Speech-To-Text-With-Databricks`
2. Ensure service principal has `CAN_MANAGE` permission on the folder
3. Verify repository is linked to correct GitHub URL and branch

### Bundle Validation Error

**Problem**: `databricks bundle validate` fails

**Solution**:
1. Check YAML syntax in `databricks.yml` and resource files
2. Ensure all required variables are provided
3. Run with verbose: `databricks bundle validate --target dev --debug`

### Local Development Issues

**Problem**: Can't deploy locally

**Solution**:
1. Authenticate: `databricks auth login`
2. Create `databricks.yml.local` with required variables
3. Check you're in the right directory: `cd speech_to_text_asset_bundle`

## Need Help?

- **Documentation**: Check [docs/README.md](README.md) for comprehensive docs
- **Troubleshooting**: See [13-troubleshooting.md](13-troubleshooting.md) for common issues
- **GitHub Issues**: Open an issue in the repository
- **Databricks Docs**: [Official Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)

## Success!

If you've completed all steps, you now have:
- ✅ A fully configured CI/CD pipeline
- ✅ Secure OIDC-based authentication
- ✅ Dev and Prod environments
- ✅ Ready for development and deployment

**Happy coding! 🚀**
