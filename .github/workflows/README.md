# GitHub Actions Workflows

This directory contains CI/CD workflows for DocProc AI.

## Workflows

### 1. Backend CI/CD (`backend-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Changes in `backend/**`

**Jobs:**
- **lint-and-test**: Run Black, Ruff, MyPy, and pytest
- **build-and-push**: Build Docker images and push to Artifact Registry
- **deploy**: Deploy to Cloud Run (main branch only)

**Required Secrets:**
- `GCP_PROJECT_ID` - GCP Project ID
- `GCP_SA_KEY` - GCP Service Account JSON key

### 2. Frontend CI/CD (`frontend-ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Changes in `frontend/**`

**Jobs:**
- **lint-and-build**: ESLint, TypeScript check, tests, build
- **deploy-vercel**: Deploy to Vercel (main/develop only)

**Required Secrets:**
- `VERCEL_TOKEN` - Vercel deployment token
- `VERCEL_ORG_ID` - Vercel organization ID
- `VERCEL_PROJECT_ID` - Vercel project ID

### 3. Terraform (`terraform.yml`)

**Triggers:**
- Push to `main` branch
- Pull requests to `main`
- Changes in `terraform/**`

**Jobs:**
- **terraform-plan**: Format check, validate, plan
- **terraform-apply**: Apply changes (main branch only, requires approval)

**Required Secrets:**
- `GCP_PROJECT_ID` - GCP Project ID
- `GCP_SA_KEY` - GCP Service Account JSON key

### 4. PR Checks (`pr-checks.yml`)

**Triggers:**
- All pull requests

**Jobs:**
- **pr-validation**: Commit messages, TODOs, secrets detection, file sizes
- **code-quality**: Security scan with bandit, detect-secrets
- **dependency-review**: Review dependency changes

## Setup Instructions

### 1. Configure GitHub Secrets

Go to **Settings > Secrets and variables > Actions** and add:

#### GCP Secrets
```
GCP_PROJECT_ID=docai-mvp-prod
GCP_SA_KEY=<JSON content of service account key>
```

#### Vercel Secrets
```
VERCEL_TOKEN=<your-vercel-token>
VERCEL_ORG_ID=<your-org-id>
VERCEL_PROJECT_ID=<your-project-id>
```

### 2. Create GCP Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions CI/CD"

# Grant necessary roles
gcloud projects add-iam-policy-binding docai-mvp-prod \
  --member="serviceAccount:github-actions@docai-mvp-prod.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding docai-mvp-prod \
  --member="serviceAccount:github-actions@docai-mvp-prod.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding docai-mvp-prod \
  --member="serviceAccount:github-actions@docai-mvp-prod.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@docai-mvp-prod.iam.gserviceaccount.com

# Copy the JSON content to GCP_SA_KEY secret
cat github-actions-key.json
```

### 3. Enable GitHub Environments

For production deployments with approval:

1. Go to **Settings > Environments**
2. Create environment: `production`
3. Enable **Required reviewers**
4. Add reviewers for approval

### 4. Branch Protection Rules

Recommended settings for `main` branch:

- Require pull request reviews (1 reviewer)
- Require status checks to pass:
  - `Backend CI/CD / lint-and-test`
  - `Frontend CI/CD / lint-and-build`
  - `PR Checks / pr-validation`
- Require branches to be up to date
- Include administrators

## Workflow Badges

Add to README.md:

```markdown
![Backend CI](https://github.com/rauly2k/docproc_ai/workflows/Backend%20CI%2FCD/badge.svg)
![Frontend CI](https://github.com/rauly2k/docproc_ai/workflows/Frontend%20CI%2FCD/badge.svg)
![Terraform](https://github.com/rauly2k/docproc_ai/workflows/Terraform%20Infrastructure/badge.svg)
```

## Monitoring

### Workflow Runs

View workflow runs at:
```
https://github.com/rauly2k/docproc_ai/actions
```

### Deployment Status

- **Backend**: Cloud Run console
- **Frontend**: Vercel dashboard
- **Infrastructure**: Terraform Cloud (if configured)

## Troubleshooting

### Failed Docker Build

Check:
- Dockerfile syntax
- Dependencies in requirements.txt
- Base image availability

### Failed Deployment

Check:
- Service account permissions
- Cloud Run quotas
- Artifact Registry access

### Failed Tests

Check:
- Test dependencies installed
- Environment variables set
- Database connections (if needed)

## Local Testing

Test workflows locally using `act`:

```bash
# Install act
brew install act

# Run backend workflow
act -j lint-and-test --workflows .github/workflows/backend-ci.yml

# Run with secrets
act -j lint-and-test --secret-file .secrets
```
