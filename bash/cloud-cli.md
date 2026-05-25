---
id: "bash-cloud-cli"
title: "Cloud CLI Patterns: AWS CLI, gcloud, az"
language: "bash"
category: "devops"
tags: ["bash", "aws", "gcloud", "azure", "cloud-cli", "resource-management"]
version: "n/a"
retrieval_hint: "bash AWS CLI gcloud az cloud CLI resource management common patterns"
last_verified: "2026-05-24"
confidence: "high"
---

# Cloud CLI Patterns: AWS CLI, gcloud, az

## When to Use
- Managing cloud resources from the command line
- Automating cloud infrastructure tasks
- Querying cloud resource metadata
- CI/CD pipeline cloud operations

## Standard Pattern

```bash
# === AWS CLI ===

# --- Configuration ---
# Configure profile
aws configure --profile production
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region: us-east-1
# Default output format: json

# Use specific profile
aws s3 ls --profile production

# --- Common Resource Management ---
# List S3 buckets
aws s3 ls

# Sync directory to S3 (with exclusions)
aws s3 sync ./build/ s3://myapp-bucket/ \
    --exclude "*.map" \
    --exclude "node_modules/*" \
    --delete

# Describe EC2 instances (filter by tag)
aws ec2 describe-instances \
    --filters "Name=tag:Environment,Values=production" \
    --query 'Reservations[].Instances[].{ID:InstanceId,Type:InstanceType,State:State.Name}' \
    --output table

# Get CloudWatch logs
aws logs tail /aws/lambda/my-function --follow

# ECS — update service
aws ecs update-service \
    --cluster production \
    --service api-service \
    --force-new-deployment \
    --region us-east-1

# --- Query with jq ---
# jq is essential for processing AWS CLI JSON output
aws ecr describe-images \
    --repository-name myapp \
    --query 'imageDetails[*].imageTags[]' \
    | jq -r '.[]'  # Extract all tags as plain text

# --- Pagination ---
# Some commands return truncated results
aws s3api list-objects-v2 \
    --bucket my-bucket \
    --max-items 100 \
    --page-size 50

# --- Error Handling ---
if aws s3 cp file.txt s3://bucket/; then
    echo "Upload successful"
else
    echo "Upload failed" >&2
    exit 1
fi


# === Google Cloud CLI (gcloud) ===

# --- Configuration ---
gcloud config set project my-project
gcloud config set compute/zone us-central1-a

# --- Common Commands ---
# List compute instances
gcloud compute instances list \
    --filter="status=RUNNING" \
    --format="table(name,zone,status)"

# Deploy to Cloud Run
gcloud run deploy my-service \
    --image gcr.io/my-project/myapp:latest \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --concurrency 80

# Query Cloud Storage
gsutil ls gs://my-bucket/**
gsutil cp file.txt gs://my-bucket/backups/

# IAM
gcloud projects add-iam-policy-binding my-project \
    --member="serviceAccount:deploy@my-project.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor"

# List with JSON output for scripting
gcloud container images list \
    --repository=gcr.io/my-project \
    --format="json"


# === Azure CLI (az) ===

# --- Login ---
az login  # Interactive
az login --service-principal -u $APP_ID -p $PASSWORD --tenant $TENANT_ID

# --- Common Commands ---
# Resource groups
az group create --name my-rg --location eastus

# VM management
az vm list --resource-group my-rg --output table

# Web app deployment
az webapp deploy \
    --resource-group my-rg \
    --name myapp \
    --src-path ./build.zip \
    --type zip

# Container instances
az container create \
    --resource-group my-rg \
    --name my-container \
    --image myregistry.azurecr.io/myapp:latest \
    --cpu 1 --memory 1.5

# --- Output Format for Scripting ---
# All CLIs support multiple output formats
# AWS:   --output json | text | table
# gcloud: --format=json | table | yaml | csv
# az:    --output json | table | tsv
```

## Common Mistakes

```bash
# WRONG: Hardcoding credentials in scripts
AWS_ACCESS_KEY_ID=AKIA123...  # Security risk!
AWS_SECRET_ACCESS_KEY=abc...  # In version control?!

# CORRECT: Use environment variables or profiles
export AWS_PROFILE=production
aws s3 ls

# Or use IAM roles on EC2/ECS — no credentials needed


# WRONG: Not using --output json for parsing (default table is fragile)
aws ec2 describe-instances
# Parsing table output is unreliable — whitespace-dependent

# CORRECT: Use JSON output with jq
aws ec2 describe-instances --output json | jq '.Reservations[0].Instances[0].InstanceId'


# WRONG: Missing pagination for long lists
aws s3api list-objects-v2 --bucket my-bucket
# Truncated if bucket has >1000 objects!

# CORRECT: Handle pagination
objects=()
next_token=""
while :; do
    result=$(aws s3api list-objects-v2 \
        --bucket my-bucket \
        --max-items 1000 \
        ${next_token:+--starting-token "$next_token"})
    objects+=($(echo "$result" | jq -r '.Contents[].Key'))
    next_token=$(echo "$result" | jq -r '.NextToken // empty')
    [[ -z "$next_token" ]] && break
done


# WRONG: Default region affecting global services
aws s3 ls  # Region-specific endpoint may fail for global services

# CORRECT: Explicit region or use us-east-1 for global services
aws s3 ls --region us-east-1
```

## Gotchas
- **CLI version differences**: AWS CLI v1 vs v2 have different pagination and argument syntax. gcloud alpha/beta commands can change. Use `--version` and pin CLI versions in CI.
- **Default region**: AWS has a default region that affects API calls. Global services (IAM, S3, Route53) may require `us-east-1`. Set `AWS_DEFAULT_REGION` explicitly in scripts.
- **Credential chain precedence**: Environment variables > CLI profile > instance profile. When debugging auth issues, check which credentials are actually being used with `aws sts get-caller-identity`.
- **JSON output character limits**: Cloud APIs may truncate long string fields in default output. Use `--no-cli-pager` (AWS) or `--format=json` to get full output.
- **Rate limiting**: Cloud CLIs are subject to API rate limits. Batch operations should include retry logic with exponential backoff.
- **IAM permission modeling**: CLI commands fail with generic "access denied" errors. Use `iam simulate-principal-policy` (AWS) or `gcloud policies` to debug permission issues.
- **Service account impersonation**: For cross-account access, use `--profile` or `--credentials` flags rather than sharing access keys.

## Related
- bash/scripting-patterns.md
- bash/error-handling.md
- patterns/secret-management.md
