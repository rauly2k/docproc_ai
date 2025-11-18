# Terraform Infrastructure

This directory contains Terraform configuration for deploying DocProc AI infrastructure to Google Cloud Platform.

## Prerequisites

- Terraform >= 1.5.0
- Google Cloud SDK (`gcloud`)
- GCP Project with billing enabled
- Required APIs enabled (automated by Terraform)

## Infrastructure Components

### Modules

1. **IAM** (`modules/iam/`)
   - Cloud Run service account
   - IAM roles and permissions

2. **Cloud Storage** (`modules/storage/`)
   - Uploads bucket
   - Processed files bucket
   - Embeddings backup bucket

3. **Cloud SQL** (`modules/cloud_sql/`)
   - PostgreSQL 15 instance
   - pgvector extension enabled
   - Automated backups (prod)
   - Database user with password in Secret Manager

4. **Pub/Sub** (`modules/pubsub/`)
   - Topics for each worker type
   - Subscriptions with retry policies
   - IAM bindings for publisher/subscriber

5. **Cloud Run** (`modules/cloud_run/`)
   - API Gateway service
   - Invoice worker service
   - OCR worker service
   - Summarizer worker service
   - RAG ingest worker service
   - Document filling worker service

6. **Monitoring** (`modules/monitoring/`)
   - Uptime checks
   - Alerting policies
   - Dashboards

## Setup Instructions

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Create terraform.tfvars

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

### 3. Review the Plan

```bash
terraform plan
```

### 4. Apply Infrastructure

```bash
terraform apply
```

### 5. Get Outputs

```bash
terraform output
terraform output -json > outputs.json
```

## Configuration

### Variables

- `project_id` - GCP Project ID
- `region` - GCP region (default: europe-west1)
- `environment` - Environment name (dev/staging/prod)
- `database_version` - PostgreSQL version (default: POSTGRES_15)
- `database_tier` - Cloud SQL tier (default: db-f1-micro)

### Environment-specific Configuration

Create separate `.tfvars` files for each environment:

```bash
# Development
terraform apply -var-file="dev.tfvars"

# Staging
terraform apply -var-file="staging.tfvars"

# Production
terraform apply -var-file="prod.tfvars"
```

## State Management

Terraform state is stored in GCS:
- Bucket: `docai-terraform-state`
- Prefix: `terraform/state`

Create the state bucket before first apply:

```bash
gsutil mb -p docai-mvp-prod -l europe-west1 gs://docai-terraform-state
gsutil versioning set on gs://docai-terraform-state
```

## Deployment Workflow

1. **Plan**: Review changes
   ```bash
   terraform plan -out=tfplan
   ```

2. **Apply**: Deploy infrastructure
   ```bash
   terraform apply tfplan
   ```

3. **Destroy** (if needed):
   ```bash
   terraform destroy
   ```

## Cost Estimation

Use `terraform cost` or Infracost to estimate costs before applying:

```bash
# Using Infracost
infracost breakdown --path .
```

## Security Notes

- Database passwords stored in Secret Manager
- Service account with least-privilege IAM roles
- Private networking for Cloud SQL
- VPC egress restrictions on Cloud Run

## Outputs

After applying, Terraform provides:

- `api_gateway_url` - API Gateway public URL
- `database_connection_name` - Cloud SQL connection string
- `uploads_bucket` - GCS uploads bucket name
- `pubsub_topics` - All Pub/Sub topic names
- `worker_services` - Worker service URLs

## Troubleshooting

### API Not Enabled

If you get "API not enabled" errors:

```bash
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
# ... enable other required APIs
```

### State Lock Issues

If state is locked:

```bash
terraform force-unlock <LOCK_ID>
```

### Import Existing Resources

```bash
terraform import google_cloud_run_v2_service.api_gateway \
  projects/PROJECT_ID/locations/REGION/services/SERVICE_NAME
```

## Maintenance

### Updating Modules

```bash
terraform get -update
```

### Validating Configuration

```bash
terraform validate
terraform fmt -recursive
```

## CI/CD Integration

This Terraform configuration is designed to work with GitHub Actions:

```yaml
- name: Terraform Apply
  run: |
    terraform init
    terraform plan -out=tfplan
    terraform apply tfplan
```

See `.github/workflows/terraform.yml` for full CI/CD setup.
