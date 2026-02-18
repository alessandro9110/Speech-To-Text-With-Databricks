# Security Best Practices

This document describes the security measures implemented in this project and best practices to follow.

## Overview

This project implements security-first principles:
- ✅ **No secrets in code** - All sensitive values are configurable
- ✅ **OIDC authentication** - No long-lived tokens
- ✅ **Public repo safe** - No workspace URLs or personal data committed
- ✅ **Environment separation** - Dev and prod isolated
- ✅ **Least privilege** - Service principals with minimal permissions

## Security Improvements History

### Before (Exposed Secrets)
The repository previously contained:
- ❌ Hardcoded Databricks workspace URLs
- ❌ Personal email addresses
- ❌ Workspace-specific paths

### After (Secure Configuration)
Now uses:
- ✅ Configurable variables
- ✅ Dynamic workspace references
- ✅ Git-ignored local config files
- ✅ Environment-based secrets

See [BEFORE_AFTER.md](../BEFORE_AFTER.md) and [SECURITY_CHANGES_IT.md](../SECURITY_CHANGES_IT.md) for details.

## Authentication Security

### OIDC vs Token-Based Authentication

**OIDC (Used in this project)**:
- ✅ Short-lived tokens (expire quickly)
- ✅ No secrets in code
- ✅ Scoped to specific repository and environment
- ✅ Automatic token rotation
- ✅ Auditable in both GitHub and Databricks
- ✅ Can't be stolen and reused elsewhere

**Token-Based (NOT used)**:
- ❌ Long-lived credentials
- ❌ Risk of token leakage
- ❌ Manual rotation required
- ❌ Broad permissions

### Federation Policy Security

Federation policies control which GitHub repositories can authenticate to Databricks.

**Secure Policy Example**:
```yaml
Issuer: https://token.actions.githubusercontent.com
Subject: repo:alessandro9110/Speech-To-Text-With-Databricks:environment:Dev
Audiences: <service-principal-uuid>
```

**Key Security Features**:
- Issuer validates token is from GitHub
- Subject restricts to specific repository and environment
- Audiences ensures token is for this service principal

**Security Best Practices**:
- ✅ Create separate policies for Dev and Prod
- ✅ Use specific subjects (include environment)
- ✅ Don't use wildcards in subject
- ❌ Don't reuse same policy across multiple repos

## Secrets Management

### What Should Be Secrets

Store in GitHub Secrets (Settings → Environments → [Dev/Prod] → Secrets):
- ✅ Service principal Client ID (UUID)
- ✅ Any API keys or tokens (if needed in future)
- ✅ Credentials for external services

### What Should Be Variables

Store in GitHub Variables (Settings → Environments → [Dev/Prod] → Variables):
- ✅ Databricks workspace URL (not a secret, but environment-specific)
- ✅ Non-sensitive configuration values

### What Should NEVER Be Committed

Never commit to the repository:
- ❌ Tokens or passwords
- ❌ API keys
- ❌ Service principal secrets
- ❌ Workspace URLs (use variables instead)
- ❌ Personal email addresses
- ❌ `databricks.yml.local` file (contains local config)
- ❌ `.env` files with secrets

### Protecting Local Configuration

The project uses `.gitignore` to protect:
```gitignore
databricks.yml.local
.env
*.pem
*.key
```

**Best Practice**:
```bash
# Create local config
cp .databricks.yml.example databricks.yml.local

# Edit with your values (NEVER commit this file)
vim databricks.yml.local

# Verify it's ignored
git status  # Should not show databricks.yml.local
```

## Service Principal Security

### Principle of Least Privilege

Grant only necessary permissions:

**Development**:
- Read/write access to dev schema
- Deploy to user-specific folders
- Create dev resources

**Production**:
- Read/write access to prod schema
- Deploy to shared folders
- Create prod resources
- Require approval for changes

### Permission Recommendations

**Minimum Permissions**:
- Workspace: User role
- Folders: CAN_MANAGE on deployment paths
- Unity Catalog: CREATE and USE on speech_to_text catalog

**Additional for Production**:
- Limited to specific admin users
- Audit logging enabled
- Separate service principal per environment (recommended)

### Service Principal Rotation

**Best Practices**:
1. Create new service principal
2. Update GitHub secrets with new Client ID
3. Update federation policies
4. Test deployment
5. Remove old service principal
6. Document rotation date

**Frequency**: Rotate at least annually or when:
- Team member leaves with access
- Potential compromise detected
- Security policy requires it

## Workspace Security

### Environment Isolation

**Dev Environment**:
- User-specific deployment paths
- Development mode enabled
- Paused triggers by default
- Less restrictive permissions

**Prod Environment**:
- Shared deployment path (single source of truth)
- Production mode
- Requires approvals (via PR process)
- Strict permissions

### Path Security

**Dev Paths**:
```
/Workspace/Users/${workspace.current_user.user_name}/.bundle/...
```
- User-specific (isolated)
- No cross-user access issues

**Prod Paths**:
```
/Workspace/Shared/.bundle/speech_to_text_asset_bundle/prod/
```
- Shared (single deployment)
- Controlled access via permissions

### Catalog and Schema Security

**Unity Catalog**: `speech_to_text`
- Proper access controls
- Separate dev and prod schemas
- Data governance policies

**Schemas**:
- `dev`: Development data (can be reset)
- `prod`: Production data (protected)

## GitHub Security

### Branch Protection

**Recommended Settings**:

**Main Branch (Production)**:
- ✅ Require pull request reviews (1+ approver)
- ✅ Require status checks to pass
- ✅ Require conversation resolution
- ✅ Restrict who can push
- ✅ Require signed commits (optional but recommended)

**Dev Branch**:
- ✅ Require pull request reviews (optional)
- ✅ Allow force pushes (careful!)

### Environment Protection

**Prod Environment Protection**:
- ✅ Required reviewers (1+ approver)
- ✅ Wait timer (optional)
- ✅ Deployment branches: main only

**Dev Environment Protection**:
- Less restrictive
- Faster iteration

### Repository Secrets

**Access Control**:
- Limit who can view/edit secrets
- Use environment-specific secrets
- Audit secret access regularly

**Organization Secrets** (if applicable):
- Share common secrets across repos
- Centralized management
- Better for multi-repo setups

## CI/CD Security

### Workflow Security

**Permissions** (already configured):
```yaml
permissions:
  id-token: write  # For OIDC
  contents: read   # For checkout
```

**Best Practices**:
- ✅ Minimal permissions (only what's needed)
- ✅ Use specific versions of actions
- ✅ Review action source code
- ❌ Don't use `permissions: write-all`

### Path Filters (Security Feature)

Workflows only run on relevant changes:
```yaml
paths:
  - 'speech_to_text_asset_bundle/**'
  - '.github/workflows/**'
```

**Security Benefit**: Prevents unnecessary runs that could:
- Expose logs unnecessarily
- Consume resources
- Run on malicious changes in other paths

### Secrets in Logs

**Rules**:
- ❌ Never echo secrets: `echo $DATABRICKS_CLIENT_ID`
- ❌ Never print environment variables: `env`
- ❌ Never commit workspace URLs in examples
- ✅ Use placeholders: `https://<DATABRICKS_HOST>`

**GitHub Protection**: GitHub automatically masks registered secrets in logs.

## Code Security

### CodeQL Scanning

**Not yet enabled**, but recommended:

```yaml
# .github/workflows/codeql-analysis.yml
name: CodeQL
on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: github/codeql-action/init@v2
        with:
          languages: python
      - uses: github/codeql-action/analyze@v2
```

### Dependency Security

**Current Dependencies** (from pyproject.toml):
```toml
dependencies = []  # No runtime dependencies (good!)

dev = [
    "pytest",
    "ruff",
    "databricks-dlt",
    "databricks-connect>=15.4,<15.5",
    "ipykernel",
]
```

**Security Practices**:
- ✅ Minimal dependencies
- ✅ Version pinning (databricks-connect)
- ✅ Regular updates
- ❌ No known vulnerabilities (verified)

**Recommendation**: Enable Dependabot:
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/speech_to_text_asset_bundle"
    schedule:
      interval: "weekly"
```

### Code Review Security

**Review Checklist**:
- [ ] No hardcoded secrets
- [ ] No workspace URLs
- [ ] No personal data
- [ ] Proper error handling
- [ ] Input validation
- [ ] SQL injection prevention (if using SQL)

## Data Security

### Data Classification

**Current Data**:
- Sample taxi data (public, non-sensitive)

**If Adding Sensitive Data**:
- ✅ Use Unity Catalog access controls
- ✅ Enable audit logging
- ✅ Encrypt at rest (Databricks default)
- ✅ Encrypt in transit (Databricks default)
- ✅ Tag sensitive columns
- ✅ Implement row-level security

### Data Access

**Principle**: Data access should be:
- Logged and auditable
- Granted based on need
- Regularly reviewed
- Revoked when no longer needed

## Compliance

### Public Repository Considerations

This is a **public repository**, so:
- ✅ No secrets committed
- ✅ No PII (personally identifiable information)
- ✅ No proprietary code (if applicable)
- ✅ Clear license (MIT)
- ✅ Security best practices documented

### Audit Trail

**GitHub Provides**:
- Commit history
- Action logs
- Secret access logs (Enterprise)

**Databricks Provides**:
- Job run logs
- Audit logs (Premium tier)
- Access logs

## Incident Response

### If Secrets Are Compromised

1. **Immediate Actions**:
   - Rotate compromised secrets immediately
   - Update GitHub secrets
   - Invalidate old tokens
   - Review audit logs for unauthorized access

2. **Investigation**:
   - Determine scope of exposure
   - Check for unauthorized changes
   - Review access logs

3. **Remediation**:
   - Fix root cause
   - Update documentation
   - Notify stakeholders if required

### If Secrets Are Committed

1. **Don't just delete the commit** - it's still in history!

2. **Immediate Actions**:
   - Rotate the secret immediately
   - Make secret inactive in source system

3. **Remove from History**:
   ```bash
   # Use BFG Repo Cleaner or git filter-branch
   # This rewrites history - coordinate with team!
   git filter-branch --force --index-filter \
     'git rm --cached --ignore-unmatch path/to/secret' \
     --prune-empty --tag-name-filter cat -- --all
   ```

4. **Force Push** (requires coordination):
   ```bash
   git push origin --force --all
   ```

5. **Notify GitHub** to clear cache

## Security Checklist

### For New Features

- [ ] No secrets in code
- [ ] Secrets in GitHub Secrets
- [ ] Variables in GitHub Variables or databricks.yml.local
- [ ] Input validation implemented
- [ ] Error handling implemented
- [ ] Tests written
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] Deployed to dev first
- [ ] Tested in dev
- [ ] Approved for prod

### For Deployments

- [ ] Bundle validated
- [ ] Tests passed
- [ ] No secrets in logs
- [ ] Correct environment
- [ ] Correct permissions
- [ ] Audit trail maintained

### For Regular Maintenance

- [ ] Review access permissions (monthly)
- [ ] Update dependencies (weekly)
- [ ] Rotate secrets (annually or as needed)
- [ ] Review audit logs (weekly)
- [ ] Update documentation (as needed)
- [ ] Test disaster recovery (quarterly)

## Security Resources

### Databricks Security
- [Databricks Security Guide](https://docs.databricks.com/security/index.html)
- [Unity Catalog Security](https://docs.databricks.com/data-governance/unity-catalog/index.html)
- [Workload Identity Federation](https://docs.databricks.com/dev-tools/auth/index.html)

### GitHub Security
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides)
- [OIDC in GitHub Actions](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

### Python Security
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [OWASP Python Security](https://cheatsheetseries.owasp.org/cheatsheets/Python_Security_Cheat_Sheet.html)

## Contact

For security issues:
1. Do not open public GitHub issues
2. Contact repository maintainers privately
3. Follow responsible disclosure practices

## Conclusion

Security is an ongoing process, not a one-time task. This project implements strong security foundations, but requires continuous vigilance and maintenance to remain secure.

**Key Takeaways**:
- ✅ Use OIDC, not tokens
- ✅ No secrets in code, ever
- ✅ Separate dev and prod
- ✅ Principle of least privilege
- ✅ Regular security reviews
