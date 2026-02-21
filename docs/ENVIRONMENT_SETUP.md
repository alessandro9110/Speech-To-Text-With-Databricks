# Environment Setup Overview

**This document is now consolidated into more specific setup guides. Please refer to the following documents for complete setup instructions:**

---

## Setup Documentation

### 1. Databricks Setup
**[docs/DATABRICKS_SETUP.md](DATABRICKS_SETUP.md)**

Complete guide for configuring Databricks resources:
- Creating the service principal
- Setting up the catalog and schemas
- Configuring OIDC federation policies for GitHub Actions
- Granting permissions

### 2. GitHub Actions Setup
**[docs/GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md)**

Complete guide for configuring GitHub Actions CI/CD:
- Creating GitHub Environments (Dev and Prod)
- Configuring environment variables and secrets
- Testing the configuration
- Troubleshooting common issues

---

## Quick Setup Checklist

- [ ] **Databricks**: Create catalog `speech_to_text`
- [ ] **Databricks**: Create service principal and note the Application ID (UUID)
- [ ] **Databricks**: Configure federation policies for Dev and Prod environments
- [ ] **Databricks**: Grant permissions on catalog/schemas/volumes
- [ ] **GitHub**: Create Dev and Prod environments
- [ ] **GitHub**: Add `DATABRICKS_HOST` variable to both environments
- [ ] **GitHub**: Add `DATABRICKS_CLIENT_ID` secret to both environments
- [ ] **Databricks**: Create Git folder at `/Workspace/Shared/Speech-To-Text-With-Databricks` (Dev only)
- [ ] **Test**: Push to `dev` branch and verify workflow succeeds

---

## References

- [Back to Main README](../README.md)
- [Databricks Setup Guide](DATABRICKS_SETUP.md)
- [GitHub Actions Setup Guide](GITHUB_ACTIONS_SETUP.md)
