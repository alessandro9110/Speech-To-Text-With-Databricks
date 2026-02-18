# Repository Structure

This document explains the organization and purpose of each directory and important file in the repository.

## Root Directory

```
Speech-To-Text-With-Databricks/
├── .github/                      # GitHub-specific configuration
├── docs/                         # Documentation (this folder)
├── speech_to_text_asset_bundle/  # Main Databricks Asset Bundle
├── .gitignore                    # Git ignore rules
├── BEFORE_AFTER.md              # Security changes comparison
├── CONFIGURATION.md             # Configuration guide
├── LICENSE                      # License file
├── README.md                    # Main readme
└── SECURITY_CHANGES_IT.md       # Italian security summary
```

## .github/ Directory

Contains GitHub-specific files and workflows.

```
.github/
├── agents/                       # Agent configuration files
│   ├── dab.agent.md             # DAB specialist agent
│   ├── dab-workflow.agent.md    # DAB workflow agent
│   └── readme-docs.agent.md     # Documentation agent
├── instructions/                 # Instructions for agents
│   └── workflow.instructions.md # Workflow coding rules
├── workflows/                    # GitHub Actions workflows
│   ├── deploy_asset_bundle_prod.yml  # Prod deployment
│   └── sync_git_folder_dev.yml       # Dev Git sync
├── copilot-instructions.md      # Copilot instructions
├── ENVIRONMENT_SETUP.md         # GitHub Actions setup guide
└── RIEPILOGO.md                 # Italian configuration summary
```

### Workflow Files

#### deploy_asset_bundle_prod.yml
**Purpose**: Deploy asset bundle to production  
**Triggers**: Push to `main` branch (with path filters)  
**Path Filters**:
- `speech_to_text_asset_bundle/**`
- `.github/workflows/**`

**Environment**: Prod  
**Authentication**: GitHub OIDC  
**Action**: `databricks bundle deploy --target prod`

#### sync_git_folder_dev.yml
**Purpose**: Sync code to Dev Git folder  
**Triggers**: Push to `dev` branch (with path filters)  
**Path Filters**:
- `speech_to_text_asset_bundle/**`
- `.github/workflows/**`

**Environment**: Dev  
**Authentication**: GitHub OIDC  
**Action**: `databricks repos update /Workspace/Shared/Speech-To-Text-With-Databricks --branch dev`

### Agent Configuration Files

These files define specialized AI agents for specific tasks:

- **dab.agent.md**: Expert in Databricks Asset Bundles, enforces public-repo hygiene
- **dab-workflow.agent.md**: Designs GitHub Actions pipelines for DAB
- **readme-docs.agent.md**: Updates documentation based on actual code

## speech_to_text_asset_bundle/ Directory

The main Databricks Asset Bundle project.

```
speech_to_text_asset_bundle/
├── resources/                    # DAB resource definitions
│   ├── sample_job.job.yml       # Job definition
│   └── speech_to_text_asset_bundle_etl.pipeline.yml  # Pipeline definition
├── src/                         # Source code
│   ├── speech_to_text_asset_bundle/     # Python package
│   │   ├── __init__.py
│   │   ├── main.py             # Entry point
│   │   └── taxis.py            # Sample code
│   ├── speech_to_text_asset_bundle_etl/ # DLT pipeline
│   │   ├── README.md
│   │   └── transformations/    # DLT transformations
│   │       ├── sample_trips_*.py
│   │       └── sample_zones_*.py
│   └── sample_notebook.ipynb   # Sample notebook
├── tests/                       # Test files
│   ├── conftest.py             # pytest configuration
│   └── sample_taxis_test.py    # Sample test
├── fixtures/                    # Test fixtures
├── .vscode/                     # VS Code settings
├── databricks.yml              # Main DAB configuration
├── .databricks.yml.example     # Example local config
├── pyproject.toml              # Python project configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # Asset bundle readme
```

### Key Files

#### databricks.yml
**Purpose**: Main Databricks Asset Bundle configuration

**Key Sections**:
- `bundle`: Name and UUID
- `variables`: Configurable parameters (databricks_host, admin_user_email, catalog, schema)
- `artifacts`: Wheel building configuration
- `targets`: Dev and prod environment configurations
- `include`: Resource file patterns

**Targets**:
- `dev`: Development mode, user-prefixed resources, paused triggers
- `prod`: Production mode, shared deployment, permissions required

#### pyproject.toml
**Purpose**: Python project configuration

**Key Sections**:
- `[project]`: Package metadata, dependencies
- `[project.scripts]`: Entry point (`main`)
- `[dependency-groups]`: Dev dependencies (pytest, ruff, databricks-connect)
- `[tool.ruff]`: Linting configuration (line-length: 120)

### Resources

#### sample_job.job.yml
**Purpose**: Defines a Databricks job

**Tasks**:
1. `notebook_task`: Runs sample_notebook.ipynb
2. `python_wheel_task`: Runs Python package entry point (depends on notebook)
3. `refresh_pipeline`: Triggers the DLT pipeline (depends on notebook)

**Configuration**:
- Trigger: Daily (1 day interval)
- Parameters: catalog, schema (from variables)
- Environment: Python 3.10+ with project wheel

#### speech_to_text_asset_bundle_etl.pipeline.yml
**Purpose**: Defines a Delta Live Tables pipeline

**Configuration**:
- Catalog: `${var.catalog}` (speech_to_text)
- Schema: `${var.schema}` (dev or prod)
- Serverless: true
- Libraries: DLT transformations from `src/speech_to_text_asset_bundle_etl/transformations/`
- Dependencies: Editable install of the project

### Source Code Structure

#### speech_to_text_asset_bundle/
Python package for job tasks.

- `main.py`: Entry point with CLI argument parsing
- `taxis.py`: Sample taxi data processing

#### speech_to_text_asset_bundle_etl/
Delta Live Tables pipeline package.

**Transformations**:
- `sample_trips_*.py`: DLT transformation for trips data
- `sample_zones_*.py`: DLT transformation for zones data

### Tests

```
tests/
├── conftest.py              # pytest fixtures and configuration
└── sample_taxis_test.py     # Unit tests for taxis module
```

**Test Tools**:
- pytest: Test runner
- databricks-connect: Local Databricks testing

## Documentation Files

### Root Level
- **README.md**: Main project documentation
- **CONFIGURATION.md**: Detailed configuration guide
- **BEFORE_AFTER.md**: Security changes comparison (English)
- **SECURITY_CHANGES_IT.md**: Security changes summary (Italian)

### .github/
- **ENVIRONMENT_SETUP.md**: GitHub Actions environment setup
- **RIEPILOGO.md**: Italian configuration summary

### docs/
- Comprehensive documentation organized by topic (this folder)

## Configuration Files

### Version Control
- `.gitignore`: Ignores build artifacts, local configs, Python cache

### Development Tools
- `.vscode/`: VS Code workspace settings
- `pyproject.toml`: Python tooling configuration

### Local Configuration (not in git)
- `databricks.yml.local`: Local variable overrides (git-ignored)

## File Naming Conventions

### YAML Files
- `*.job.yml`: Job definitions
- `*.pipeline.yml`: Pipeline definitions
- `*.yml`: Workflow files

### Python Files
- `*_test.py`: Test files
- `main.py`: Entry points
- No special naming for regular modules

### Documentation
- `*.md`: Markdown documentation
- `README.md`: Primary documentation in each directory
- Numbered docs: `00-*.md`, `01-*.md` for ordered reading

## Important Notes

### What's NOT in the Repository
❌ Secrets (tokens, credentials)  
❌ Workspace URLs (use variables)  
❌ Personal email addresses  
❌ `databricks.yml.local` (git-ignored)  
❌ Build artifacts (`dist/`, `*.whl`)  
❌ Python cache (`__pycache__/`, `*.pyc`)

### Path Filters in Workflows
Both workflows only run when changes are made to:
- `speech_to_text_asset_bundle/**` (the DAB project)
- `.github/workflows/**` (workflow files themselves)

This prevents unnecessary workflow runs on documentation-only changes.

## Next Steps

- [Development Workflow](08-development-workflow.md) - Learn how to work with this structure
- [Configuration Guide](06-configuration-guide.md) - Understand configuration options
- [Testing Guide](09-testing-guide.md) - Learn about testing
