# Project Overview

## What is Speech-To-Text-With-Databricks?

This repository contains a **Databricks Asset Bundle (DAB)** solution for speech-to-text processing. It demonstrates modern best practices for Databricks development, including infrastructure-as-code, CI/CD automation, and secure authentication.

## Key Features

### 🏗️ Infrastructure as Code
- **Databricks Asset Bundles** for defining and deploying all resources
- Version-controlled configuration
- Reproducible deployments across environments

### 🔐 Secure Authentication
- **OIDC (OpenID Connect)** integration with GitHub Actions
- Service principal-based authentication (no long-lived tokens)
- No hardcoded secrets in the repository

### 🚀 Automated CI/CD
- **GitHub Actions workflows** for automated deployment
- Separate dev and prod environments
- Path-based workflow triggers (only runs when relevant files change)

### 🔧 Development-Ready
- Local development tools (pytest, ruff, uv)
- Delta Live Tables (DLT) pipeline support
- Wheel-based Python packaging

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Repository                       │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Dev Branch      │         │  Main Branch     │         │
│  │  (Development)   │         │  (Production)    │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
│           │                             │                    │
│           ▼                             ▼                    │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │ sync_git_folder  │         │ deploy_bundle    │         │
│  │  _dev.yml        │         │  _prod.yml       │         │
│  └────────┬─────────┘         └────────┬─────────┘         │
└───────────┼──────────────────────────────┼──────────────────┘
            │                              │
            │ OIDC Token                   │ OIDC Token
            ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Databricks Workspace                       │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Dev Environment │         │ Prod Environment │         │
│  │  (Git Folder)    │         │ (Shared Folder)  │         │
│  │                  │         │                  │         │
│  │  - Jobs          │         │  - Jobs          │         │
│  │  - Pipelines     │         │  - Pipelines     │         │
│  │  - Notebooks     │         │  - Resources     │         │
│  └──────────────────┘         └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Deployment Strategies

#### Development Environment (dev branch)
- Uses **Git folder synchronization**
- Updates repository in `/Workspace/Shared/Speech-To-Text-With-Databricks`
- Enables quick iterative development
- Resources prefixed with user name

#### Production Environment (main branch)
- Uses **Direct asset bundle deployment**
- Deploys to `/Workspace/Shared/.bundle/`
- Production-grade configuration
- Resources prefixed with `prod_`

## Technologies Used

### Databricks
- **Delta Live Tables (DLT)** - Data pipelines
- **Unity Catalog** - Data governance (catalog: `speech_to_text`, schemas: `dev`/`prod`)
- **Jobs** - Orchestration
- **Serverless** - Compute for pipelines

### Python Stack
- **Python 3.10-3.12** - Language version
- **uv** - Fast Python package installer and build tool
- **pytest** - Testing framework
- **ruff** - Linting and formatting
- **databricks-connect** - Local Databricks development

### CI/CD
- **GitHub Actions** - Automation
- **OIDC** - Secure authentication
- **Databricks CLI** - Deployment tool

## Project Goals

1. **Security First**: No secrets in code, OIDC authentication, secure by default
2. **Developer Experience**: Easy local development, quick feedback loops
3. **Production Ready**: Robust deployment, proper environments, monitoring
4. **Maintainable**: Clear structure, comprehensive documentation, automated testing

## What's Included

### Resources Defined
- ✅ **1 Job** (`sample_job`) - Orchestrates notebook, Python wheel, and pipeline tasks
- ✅ **1 Pipeline** (`speech_to_text_asset_bundle_etl`) - DLT pipeline with transformations
- ✅ **1 Notebook** (`sample_notebook.ipynb`) - Example notebook
- ✅ **Python Package** - Wheel-based package with entry point
- ✅ **2 DLT Transformations** - Sample data processing

### CI/CD Workflows
- ✅ **Dev Deployment** - Auto-syncs Git folder on push to dev branch
- ✅ **Prod Deployment** - Auto-deploys bundle on push to main branch
- ⚠️ **PR Validation** - Not yet implemented (planned)

### Testing & Quality
- ✅ **Unit Tests** - pytest-based tests
- ✅ **Linting** - ruff configuration
- ⚠️ **Integration Tests** - Not yet implemented (planned)

## Current Limitations

1. **No PR Workflows**: There are no automated lint/test/validate workflows for pull requests yet
2. **Sample Data Only**: Current transformations use sample taxi data
3. **No Speech-to-Text Implementation**: The actual speech-to-text functionality is not yet implemented
4. **Basic Testing**: Limited test coverage

## Next Steps

See [Contributing Guide](17-contributing.md) for how to extend this project.
