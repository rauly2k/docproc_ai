# Administrator Guide

## Daily Operations

### Monitor System Health

```bash
# Check all services status
gcloud run services list --region=europe-west1

# Check error rates
gcloud logging read "severity=ERROR" --limit=50 --format=json

# Check queue depths
gcloud pubsub subscriptions list
```

### Review Metrics

1. Open Cloud Console Monitoring Dashboard
2. Check:
   - Request rate
   - Error rate
   - Response latency
   - Queue depths
   - Database connections

### Respond to Alerts

**High Error Rate Alert**:
1. Check logs for error patterns
2. Identify affected service
3. Check recent deployments
4. Rollback if necessary

**API Down Alert**:
1. Check service status
2. Check database connectivity
3. Check external dependencies (Firebase, Document AI)
4. Restart service if needed

## User Management

### View User Activity

```sql
-- Connect to database
gcloud sql connect documentai-db --user=postgres

-- Top users by document count
SELECT tenant_id, COUNT(*) as doc_count
FROM documents
GROUP BY tenant_id
ORDER BY doc_count DESC
LIMIT 20;

-- Recent uploads
SELECT tenant_id, filename, created_at
FROM documents
ORDER BY created_at DESC
LIMIT 50;
```

### Delete User Data (GDPR)

```bash
# Use admin script
python scripts/delete_user_data.py --tenant-id=<tenant_id> --confirm
```

## Performance Optimization

### Scale Services

```bash
# Increase max instances
gcloud run services update api-gateway \
  --max-instances=20 \
  --region=europe-west1
```

### Optimize Database

```sql
-- Check slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Analyze tables
ANALYZE documents;
VACUUM ANALYZE documents;
```

## Backup and Recovery

### Manual Backup

```bash
# Backup database
gcloud sql backups create --instance=documentai-db

# List backups
gcloud sql backups list --instance=documentai-db
```

### Restore from Backup

```bash
# Restore to point in time
gcloud sql backups restore <BACKUP_ID> \
  --backup-instance=documentai-db \
  --backup-id=<BACKUP_ID>
```

### Backup Documents

```bash
# Sync GCS bucket to local
gsutil -m rsync -r gs://your-bucket-documents ./backup/
```

## Cost Management

### Review Costs

```bash
# View current month costs
gcloud billing accounts list
gcloud billing budgets list
```

### Optimize Costs

1. **Reduce Cloud Run idle time**: Set min instances to 0 for workers
2. **Optimize database**: Use smallest instance that meets performance
3. **Clean old documents**: Delete documents older than retention period
4. **Use Gemini Flash**: Set as default over Pro model

## Security Tasks

### Rotate Secrets

```bash
# Update database password
gcloud sql users set-password postgres \
  --instance=documentai-db \
  --password=<NEW_PASSWORD>

# Update Secret Manager
gcloud secrets versions add database-password \
  --data-file=new-password.txt
```

### Review IAM Permissions

```bash
# List service accounts
gcloud iam service-accounts list

# Review permissions
gcloud projects get-iam-policy $PROJECT_ID
```

### Security Scan

```bash
# Run security scan
python scripts/security_scan.py

# Review results
cat security-report.json
```

## Incident Response

### 1. Detect Issue

- Monitor alerts
- Check logs
- Review metrics

### 2. Assess Impact

- How many users affected?
- Which services down?
- Data loss risk?

### 3. Mitigate

- Rollback if recent deployment
- Scale up if capacity issue
- Restart if service stuck

### 4. Communicate

- Update status page
- Notify affected users
- Post incident report

### 5. Post-Mortem

- Document timeline
- Identify root cause
- Create action items
- Update runbooks
