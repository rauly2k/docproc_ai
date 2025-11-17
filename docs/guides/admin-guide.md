# Administrator Guide

## Daily Operations

### Monitor System Health

```bash
# Check all services status
gcloud run services list --region=europe-west1

# Check error rates
gcloud logging read "severity=ERROR" --limit=50 --format=json

# Check Pub/Sub queue depths
gcloud pubsub subscriptions list

# View metrics dashboard
open https://console.cloud.google.com/monitoring/dashboards
```

### Review Daily Metrics

1. Open Cloud Console Monitoring Dashboard
2. Check:
   - Request rate (should be stable)
   - Error rate (should be <1%)
   - Response latency p95 (should be <500ms)
   - Queue depths (should be near 0)
   - Database connections (should be <pool_size)

### Respond to Alerts

**High Error Rate Alert**:
1. Check logs for error patterns:
   ```bash
   gcloud logging read "severity=ERROR" --limit=100
   ```
2. Identify affected service
3. Check recent deployments:
   ```bash
   gcloud run revisions list --service=api-gateway --region=europe-west1
   ```
4. Rollback if necessary:
   ```bash
   gcloud run services update-traffic api-gateway \
     --to-revisions=previous-revision=100 \
     --region=europe-west1
   ```

**API Down Alert**:
1. Check service status:
   ```bash
   gcloud run services describe api-gateway --region=europe-west1
   ```
2. Check database connectivity:
   ```bash
   gcloud sql instances describe documentai-db
   ```
3. Check external dependencies (Firebase, Document AI)
4. Restart service if needed:
   ```bash
   gcloud run services update api-gateway --region=europe-west1
   ```

**High Queue Depth**:
1. Check worker status:
   ```bash
   gcloud run services describe invoice-worker --region=europe-west1
   ```
2. Scale up workers:
   ```bash
   gcloud run services update invoice-worker \
     --max-instances=10 \
     --region=europe-west1
   ```

## User Management

### View User Activity

```sql
-- Connect to database
gcloud sql connect documentai-db --user=postgres

-- Top users by document count
SELECT
  t.email,
  t.name,
  COUNT(d.id) as doc_count,
  t.subscription_tier,
  t.created_at
FROM tenants t
LEFT JOIN documents d ON d.tenant_id = t.id
GROUP BY t.id, t.email, t.name, t.subscription_tier, t.created_at
ORDER BY doc_count DESC
LIMIT 20;

-- Recent uploads
SELECT
  t.email,
  d.filename,
  d.document_type,
  d.status,
  d.created_at
FROM documents d
JOIN tenants t ON t.id = d.tenant_id
ORDER BY d.created_at DESC
LIMIT 50;

-- User signups per day
SELECT
  DATE(created_at) as signup_date,
  COUNT(*) as signups
FROM tenants
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY signup_date DESC;
```

### Delete User Data (GDPR)

```bash
# Create admin script: scripts/delete_user_data.py
python scripts/delete_user_data.py --tenant-id=<tenant_id> --confirm

# This script will:
# 1. Delete all documents from GCS
# 2. Delete all database records
# 3. Log audit trail
# 4. Send confirmation email
```

### Deactivate User Account

```sql
-- Deactivate account
UPDATE tenants
SET is_active = false
WHERE id = '<tenant_id>';

-- Reactivate account
UPDATE tenants
SET is_active = true
WHERE id = '<tenant_id>';
```

## Performance Optimization

### Scale Services

```bash
# API Gateway - Always on with autoscaling
gcloud run services update api-gateway \
  --min-instances=2 \
  --max-instances=20 \
  --region=europe-west1

# Workers - Scale to zero when idle
gcloud run services update invoice-worker \
  --min-instances=0 \
  --max-instances=5 \
  --region=europe-west1
```

### Optimize Database

```sql
-- Check slow queries
SELECT
  query,
  calls,
  mean_exec_time,
  max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Analyze table statistics
ANALYZE documents;
VACUUM ANALYZE documents;

-- Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Check database size
SELECT
  pg_size_pretty(pg_database_size('documentai')) as database_size;

-- Check table sizes
SELECT
  tablename,
  pg_size_pretty(pg_total_relation_size(tablename::text)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::text) DESC;
```

### Clear Redis Cache

```bash
# Connect to Redis
redis-cli -h <redis-host> -p 6379 -a <password>

# Clear all cache
FLUSHDB

# Clear specific pattern
SCAN 0 MATCH rate_limit:* COUNT 100
# Then delete matching keys
```

## Backup and Recovery

### Manual Backup

```bash
# Backup database
gcloud sql backups create --instance=documentai-db

# Backup documents
gsutil -m rsync -r gs://your-bucket-documents ./backup-$(date +%Y%m%d)/

# Verify backup
gsutil ls ./backup-$(date +%Y%m%d)/
```

### Restore from Backup

```bash
# List available backups
gcloud sql backups list --instance=documentai-db

# Restore database
gcloud sql backups restore <BACKUP_ID> \
  --backup-instance=documentai-db

# Restore documents
gsutil -m rsync -r ./backup-20250117/ gs://your-bucket-documents
```

### Point-in-Time Recovery

```bash
# Cloud SQL supports PITR up to 7 days
gcloud sql instances restore-backup documentai-db \
  --backup-run=<BACKUP_RUN_ID> \
  --async
```

## Cost Management

### Review Costs

```bash
# View current month costs by service
gcloud billing accounts list

# Export billing data
gcloud billing accounts get-iam-policy <BILLING_ACCOUNT_ID>

# View budgets and alerts
gcloud billing budgets list --billing-account=<BILLING_ACCOUNT_ID>
```

### Cost Optimization Actions

1. **Reduce Cloud Run idle time**:
   ```bash
   # Set min instances to 0 for workers
   gcloud run services update invoice-worker --min-instances=0
   ```

2. **Optimize database instance**:
   ```bash
   # Use smaller instance if possible
   gcloud sql instances patch documentai-db --tier=db-n1-standard-1
   ```

3. **Clean old documents**:
   ```bash
   # Set lifecycle policy on GCS buckets
   gsutil lifecycle set lifecycle-policy.json gs://your-bucket
   ```

4. **Use Gemini Flash by default**:
   ```bash
   # Update environment variable
   gcloud run services update api-gateway \
     --update-env-vars GEMINI_DEFAULT_MODEL=gemini-1.5-flash
   ```

### Estimated Monthly Costs

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Run (API) | 2M requests | $40 |
| Cloud Run (Workers) | 10K jobs | $15 |
| Cloud SQL | db-n1-standard-2 | $95 |
| Cloud Storage | 100GB | $2 |
| Pub/Sub | 2M messages | $8 |
| Document AI | 10K pages | $150 |
| Vertex AI | 500K tokens | $20 |
| Redis | 1GB | $30 |
| **Total** | | **~$360/month** |

## Security Tasks

### Rotate Secrets

```bash
# 1. Database password
gcloud sql users set-password postgres \
  --instance=documentai-db \
  --password=<NEW_PASSWORD>

# 2. Update Secret Manager
echo -n "<NEW_PASSWORD>" | gcloud secrets versions add database-password --data-file=-

# 3. Restart services
gcloud run services update api-gateway --region=europe-west1
```

### Review IAM Permissions

```bash
# List service accounts
gcloud iam service-accounts list

# Review permissions for specific service account
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:api-gateway@$PROJECT_ID.iam.gserviceaccount.com"

# Audit all permissions
gcloud projects get-iam-policy $PROJECT_ID > iam-audit-$(date +%Y%m%d).json
```

### Security Scan

```bash
# Backend security scan
cd backend
pip install bandit safety
bandit -r . -f json -o security-report.json
safety check

# Frontend security scan
cd frontend
npm audit
npm audit fix

# Review security report
cat backend/security-report.json | jq '.results[] | select(.issue_severity=="HIGH")'
```

### Review Audit Logs

```sql
-- Recent access to sensitive documents
SELECT
  a.action,
  a.user_id,
  t.email,
  a.resource_type,
  a.resource_id,
  a.timestamp
FROM audit_logs a
JOIN tenants t ON t.id = a.tenant_id
WHERE a.resource_type = 'document'
  AND a.timestamp >= NOW() - INTERVAL '7 days'
ORDER BY a.timestamp DESC
LIMIT 100;

-- Failed authentication attempts
SELECT
  ip_address,
  COUNT(*) as attempts,
  MAX(timestamp) as last_attempt
FROM audit_logs
WHERE action = 'auth_failed'
  AND timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY ip_address
HAVING COUNT(*) > 5
ORDER BY attempts DESC;
```

## Troubleshooting

### High Memory Usage

```bash
# Check memory usage
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/memory/utilizations"' \
  --format=json

# Increase memory
gcloud run services update api-gateway \
  --memory=2Gi \
  --region=europe-west1
```

### Database Connection Pool Exhausted

```sql
-- Check active connections
SELECT
  COUNT(*) as active_connections,
  max_conn as max_connections
FROM pg_stat_activity,
  (SELECT setting::int as max_conn FROM pg_settings WHERE name='max_connections') as s
GROUP BY max_connections;

-- Kill idle connections
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '10 minutes';
```

```bash
# Increase connection pool size
gcloud run services update api-gateway \
  --update-env-vars DB_POOL_SIZE=10,DB_MAX_OVERFLOW=20
```

### Worker Processing Stuck

```bash
# Check Pub/Sub subscription
gcloud pubsub subscriptions describe invoice-processing-sub

# Check unacked messages
gcloud pubsub subscriptions pull invoice-processing-sub --limit=1

# Restart worker
gcloud run services update invoice-worker --region=europe-west1

# Increase timeout
gcloud run services update invoice-worker \
  --timeout=900 \
  --region=europe-west1
```

### Out of Disk Space

```bash
# Check database storage
gcloud sql instances describe documentai-db \
  --format="value(settings.dataDiskSizeGb)"

# Increase storage
gcloud sql instances patch documentai-db \
  --storage-size=50GB \
  --storage-auto-increase
```

## Monitoring Dashboards

### Key Metrics Dashboard

Access: `https://console.cloud.google.com/monitoring/dashboards`

Widgets to monitor:
1. **API Request Rate** (requests/minute)
2. **Error Rate** (errors/total requests)
3. **Response Latency** (p50, p95, p99)
4. **Pub/Sub Queue Depth** (messages waiting)
5. **Database Connections** (active/max)
6. **Worker Processing Time** (seconds/job)
7. **Cache Hit Rate** (Redis)

### Custom Metrics Queries

```bash
# Request rate
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"' \
  --format=json

# Error rate
gcloud monitoring time-series list \
  --filter='metric.type="logging.googleapis.com/log_entry_count" AND severity="ERROR"' \
  --format=json
```

## Support

For administrative issues:
- Internal docs: /docs/admin-guide.md
- Cloud Console: console.cloud.google.com
- Emergency: devops@documentai.com
