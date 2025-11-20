# CI/CD Setup Guide

This repository includes GitHub Actions workflows for automated testing, building, and deployment.

## 📋 Workflows Overview

### 1. **CI Workflow** (`ci.yml`)
- Runs on every push and pull request
- Tests code quality and builds Docker image
- **No secrets required** - works out of the box

### 2. **Full CD Pipeline** (`deploy.yml`)
- Comprehensive deployment to multiple cloud platforms
- Includes security scanning
- Requires secrets configuration (see below)

## 🚀 Quick Start (CI Only)

The basic CI workflow works immediately after pushing to GitHub. No configuration needed!

```bash
git add .
git commit -m "Add CI/CD workflows"
git push origin main
```

Check the **Actions** tab in your GitHub repository to see the workflow running.

## ☁️ Cloud Deployment Setup

### Option 1: Google Cloud Run (Recommended for Beginners)

#### Prerequisites
1. Create a Google Cloud project
2. Enable Cloud Run API
3. Create a service account with Cloud Run Admin role

#### Setup Steps

1. **Create Service Account Key**
   ```bash
   gcloud iam service-accounts create agentry-deployer \
     --display-name="Agentry Deployer"
   
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:agentry-deployer@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   gcloud iam service-accounts keys create key.json \
     --iam-account=agentry-deployer@PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Add GitHub Secrets**
   Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
   
   - `GCP_SA_KEY`: Contents of `key.json`
   - `GROQ_API_KEY`: Your Groq API key
   - `GEMINI_API_KEY`: Your Gemini API key

3. **Enable Deployment**
   The GCP deployment job is enabled by default in `deploy.yml`

### Option 2: AWS ECS

#### Prerequisites
1. Create an AWS account
2. Create an ECS cluster named `agentry-cluster`
3. Create an ECR repository named `agentry`
4. Create an ECS service named `agentry-service`

#### Setup Steps

1. **Create IAM User**
   - Create user with `AmazonECS_FullAccess` and `AmazonEC2ContainerRegistryFullAccess`
   - Generate access keys

2. **Add GitHub Secrets**
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
   - `GROQ_API_KEY`: Your Groq API key
   - `GEMINI_API_KEY`: Your Gemini API key

3. **Enable Deployment**
   In `deploy.yml`, change line:
   ```yaml
   if: github.ref == 'refs/heads/main' && github.event_name == 'push' && false
   ```
   to:
   ```yaml
   if: github.ref == 'refs/heads/main' && github.event_name == 'push'
   ```

### Option 3: Azure Container Instances

#### Prerequisites
1. Create an Azure account
2. Create a resource group named `agentry-rg`

#### Setup Steps

1. **Create Service Principal**
   ```bash
   az ad sp create-for-rbac \
     --name "agentry-deployer" \
     --role contributor \
     --scopes /subscriptions/{subscription-id}/resourceGroups/agentry-rg \
     --sdk-auth
   ```

2. **Add GitHub Secrets**
   - `AZURE_CREDENTIALS`: Output from the above command
   - `GROQ_API_KEY`: Your Groq API key
   - `GEMINI_API_KEY`: Your Gemini API key

3. **Enable Deployment**
   Same as AWS - change the `if` condition in `deploy.yml`

## 🔒 Required GitHub Secrets

### For All Deployments
- `GROQ_API_KEY` - Your Groq API key (optional if using only Ollama)
- `GEMINI_API_KEY` - Your Gemini API key (optional if using only Ollama)

### For Google Cloud Run
- `GCP_SA_KEY` - Service account JSON key

### For AWS ECS
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

### For Azure
- `AZURE_CREDENTIALS` - Service principal credentials

## 📦 Container Registry

By default, images are pushed to **GitHub Container Registry (ghcr.io)**, which is:
- ✅ Free for public repositories
- ✅ Integrated with GitHub Actions
- ✅ No additional setup required

Images will be available at:
```
ghcr.io/rudramodi360/agentry:latest
```

## 🔐 Security Scanning

The pipeline includes **Trivy** security scanning that:
- Scans Docker images for vulnerabilities
- Uploads results to GitHub Security tab
- Runs on every build

View results in: `Security` → `Code scanning alerts`

## 🎯 Deployment Triggers

| Event | CI Workflow | Deploy Workflow |
|-------|-------------|-----------------|
| Push to `main` | ✅ Runs | ✅ Deploys |
| Push to `develop` | ✅ Runs | ❌ Builds only |
| Pull Request | ✅ Runs | ❌ Builds only |
| Release | ✅ Runs | ✅ Deploys with version tag |

## 🛠️ Customization

### Change Deployment Region
Edit `deploy.yml` and modify the region:

**GCP:**
```yaml
--region us-central1  # Change to your preferred region
```

**AWS:**
```yaml
aws-region: us-east-1  # Change to your preferred region
```

**Azure:**
```yaml
location: eastus  # Change to your preferred region
```

### Adjust Resources
Modify CPU and memory limits in `deploy.yml`:

```yaml
--memory 512Mi  # Increase for larger workloads
--cpu 1         # Increase for more processing power
```

## 📊 Monitoring Deployments

### GitHub Actions
- Go to `Actions` tab in your repository
- Click on any workflow run to see detailed logs

### Cloud Platform Logs
- **GCP**: Cloud Console → Cloud Run → agentry → Logs
- **AWS**: CloudWatch → Log Groups → /ecs/agentry
- **Azure**: Portal → Container Instances → agentry → Logs

## 🐛 Troubleshooting

### Build Fails
1. Check if `uv.lock` is committed
2. Verify `pyproject.toml` syntax
3. Review Docker build logs in Actions

### Deployment Fails
1. Verify all required secrets are set
2. Check cloud platform quotas
3. Review service account permissions

### Image Not Found
1. Ensure GitHub Container Registry is enabled
2. Check if image was pushed successfully
3. Verify image name matches in deployment config

## 🔄 Manual Deployment

You can manually trigger deployments:

1. Go to `Actions` tab
2. Select `CI/CD Pipeline` workflow
3. Click `Run workflow`
4. Select branch and click `Run workflow`

## 📝 Next Steps

1. **Add Tests**: Create `tests/` directory and add pytest tests
2. **Add Linting**: Install ruff and black:
   ```bash
   uv add --dev ruff black pytest
   ```
3. **Configure Monitoring**: Set up cloud platform monitoring and alerts
4. **Add Staging Environment**: Create a `staging` branch for pre-production testing

## 🤝 Contributing

When contributing:
1. Create a feature branch
2. Push and create a Pull Request
3. CI will automatically run tests
4. Merge to `main` triggers deployment

---

**Need help?** Check the [GitHub Actions documentation](https://docs.github.com/en/actions) or open an issue.
