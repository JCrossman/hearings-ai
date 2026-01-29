# Operations Guide

This document covers day-to-day operational tasks for the Hearings AI application.

## Service Status

**Current State**: ⏸️ Shut down for overnight (2026-01-29)

### Quick Status Check
```bash
# Check API status
az containerapp show \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --query "properties.configuration.ingress.external" \
  --output tsv

# Check Static Web App status
az staticwebapp show \
  --name hearingsai-web \
  --resource-group rg-hearingsai-dev \
  --query "defaultHostname" \
  --output tsv
```

---

## Shutdown Procedures

### Full Shutdown (Prevent Access)
Use this to completely shut down the application overnight or during maintenance.

```bash
# 1. Disable API access (returns 404 for all requests)
az containerapp ingress disable \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev

# 2. Delete Static Web App (temporary removal)
az staticwebapp delete \
  --name hearingsai-web \
  --resource-group rg-hearingsai-dev \
  --yes --no-wait

# Result: Application is completely inaccessible
```

**Cost Impact**: 
- Container App scales to 0 (no compute costs)
- AI Search continues to run (fixed ~$75/month)
- OpenAI, Cosmos DB, Storage have no cost when idle

### Scale Down Only (Keep Services Running)
Use this if you want services available but minimal resources.

```bash
# Scale API to minimum (will auto-scale on demand)
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --min-replicas 0 \
  --max-replicas 1
```

---

## Startup Procedures

### Full Startup (After Shutdown)

**Step 1: Re-enable API**
```bash
az containerapp ingress enable \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --type external \
  --target-port 8000 \
  --transport auto
```

**Step 2: Recreate Static Web App** (if deleted)
```bash
# Option A: Recreate via Bicep
cd infra
az deployment group create \
  -g rg-hearingsai-dev \
  -f modules/staticwebapp.bicep \
  -p name=hearingsai-web location=eastus2

# Option B: Recreate manually via Azure Portal
# - Create new Static Web App named "hearingsai-web"
# - Select Free tier
# - Note the deployment token for GitHub Actions
```

**Step 3: Redeploy Frontend**
```bash
cd web
npm run build
swa deploy dist \
  --app-name hearingsai-web \
  --resource-group rg-hearingsai-dev \
  --env production \
  --no-use-keychain
```

**Step 4: Verify Services**
```bash
# Test API
curl https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io/health

# Test Frontend
curl -I https://lemon-river-0cd056d0f.4.azurestaticapps.net
```

### Scale Up (After Scale Down)
```bash
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --min-replicas 1 \
  --max-replicas 3
```

---

## User Access Management

### Add User to Allowlist
```bash
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --set-env-vars "ALLOWED_USERS=user1@example.com,user2@example.com"
```

### Remove Allowlist (Allow All Authenticated Users)
```bash
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --remove-env-vars "ALLOWED_USERS"
```

See `ALLOWLIST.md` for detailed user management instructions.

---

## Deployment Operations

### Deploy New API Version
```bash
# Build in Azure (recommended - avoids local Docker issues)
az acr build \
  --registry hearingsaiacr \
  --image hearingsai-api:v8 \
  --file api/Dockerfile api/ \
  --platform linux/amd64

# Deploy to Container App
az containerapp update \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --image hearingsaiacr.azurecr.io/hearingsai-api:v8

# Verify deployment
curl https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io/health
```

### Deploy Frontend Updates
```bash
cd web
npm run build

# Deploy to production
swa deploy dist \
  --app-name hearingsai-web \
  --resource-group rg-hearingsai-dev \
  --env production \
  --no-use-keychain

# Verify (wait 1-2 minutes for CDN refresh)
curl -I https://lemon-river-0cd056d0f.4.azurestaticapps.net
```

### Rollback to Previous Version
```bash
# List recent revisions
az containerapp revision list \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --output table

# Activate previous revision
az containerapp revision activate \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --revision hearingsai-api--0000008
```

---

## Monitoring & Logs

### View API Logs
```bash
# Recent logs
az containerapp logs show \
  --name hearingsai-api \
  --resource-group rg-hearingsai-dev \
  --follow

# Logs from specific time
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerAppConsoleLogs_CL | where TimeGenerated > ago(1h)"
```

### Check Application Health
```bash
# API health endpoint
curl https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io/health

# Expected response:
# {"status": "healthy"}
```

### Monitor Search Index
```bash
# Check index statistics
az search index show \
  --service-name hearingsai-dev-srch-43uk2agt \
  --name hearings-index \
  --query "{documents:statistics.documentCount, size:statistics.storageSize}"
```

---

## Data Operations

### Reindex Documents
```bash
cd scripts

# Create .env with Azure credentials
cp api/.env .env

# Run ingestion
python ingest-documents.py

# Expected output: "Indexed 5,693 chunks from 54 documents"
```

### Clear Search Index
```bash
# Delete and recreate index
python scripts/create-search-index.py --recreate
```

### Backup Search Index Data
```bash
# Export search results to JSON
az search index show \
  --service-name hearingsai-dev-srch-43uk2agt \
  --name hearings-index \
  --output json > backup-hearings-index.json
```

---

## Cost Management

### Current Monthly Costs (Approximate)
- **AI Search Basic**: ~$75/month (fixed)
- **Container Apps**: ~$5-20/month (scales to zero)
- **Static Web Apps**: Free tier ($0)
- **OpenAI**: Pay-per-use (~$0-50/month depending on usage)
- **Cosmos DB Serverless**: ~$0-10/month (serverless)
- **Storage**: ~$1/month
- **Total**: ~$80-150/month

### Cost Optimization Tips
1. **Scale to 0 overnight**: Set `min-replicas=0` on Container App
2. **Disable ingress**: Completely shut down API when not needed
3. **Delete Static Web App**: No cost when deleted
4. **Monitor OpenAI usage**: Check Azure Portal for API costs
5. **Consider AI Search Free tier**: For development (10k documents)

### Delete Everything (Nuclear Option)
```bash
# WARNING: This deletes all data and infrastructure
az group delete \
  --name rg-hearingsai-dev \
  --yes --no-wait

# To restore: Run Bicep deployment from infra/ folder
```

---

## Troubleshooting

### API Returns 404
**Cause**: Ingress disabled  
**Fix**: Re-enable ingress (see Startup Procedures)

### Frontend Shows "Service Unavailable"
**Cause**: API is down or ingress disabled  
**Fix**: Check API health, re-enable ingress

### Authentication Fails
**Cause**: Static Web App configuration missing  
**Fix**: Check `staticwebapp.config.json` is in dist folder

### Search Returns No Results
**Cause**: Index empty or not created  
**Fix**: Run `ingest-documents.py` script

### "Access Denied" Error
**Cause**: User not in allowlist  
**Fix**: Add user email to `ALLOWED_USERS` env var

---

## Emergency Contacts

- **Azure Subscription Owner**: [Your Name]
- **GitHub Repository**: https://github.com/JCrossman/hearings-ai
- **Azure Portal**: https://portal.azure.com
- **Resource Group**: rg-hearingsai-dev (Canada Central)

---

## Service URLs

- **Production Web**: https://lemon-river-0cd056d0f.4.azurestaticapps.net
- **API**: https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io
- **API Docs**: https://hearingsai-api.lemonground-4dbaf9d3.canadacentral.azurecontainerapps.io/docs
- **GitHub**: https://github.com/JCrossman/hearings-ai

---

**Last Updated**: 2026-01-29  
**Version**: v0.2.0
