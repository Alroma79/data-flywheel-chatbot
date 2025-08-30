# Railway Deployment Guide

## Overview

Deploy the Data Flywheel Chatbot to Railway using Docker for a live demo environment. This guide provides step-by-step instructions for a fast, demo-ready deployment.

⚠️ **Demo Environment Notice**: This deployment uses SQLite for simplicity. The filesystem is ephemeral - data will be lost on container restarts. For production use, consider PostgreSQL integration.

## Prerequisites

- GitHub account with this repository
- Railway account (free tier available)
- OpenAI API key

## Step-by-Step Deployment

### 1. Create Railway Service

1. **Sign up/Login to Railway**
   - Go to [railway.app](https://railway.app)
   - Sign in with your GitHub account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `data-flywheel-chatbot` repository
   - Railway will automatically detect the Dockerfile

### 2. Configure Environment Variables

In your Railway project dashboard, go to **Variables** tab and add:

#### Required Variables
```
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

#### Recommended Variables
```
APP_TOKEN=your-secure-bearer-token-here
ENV=production
DEBUG=false
```

#### CORS Configuration
```
CORS_ORIGINS=["https://your-app-name.up.railway.app","http://localhost:8000"]
```
*Replace `your-app-name` with your actual Railway subdomain*

#### Optional Variables (with defaults)
```
DATABASE_URL=sqlite:///./chatbot.db
DEFAULT_MODEL=gpt-4o
DEFAULT_TEMPERATURE=0.7
```

### 3. Deploy and Verify

1. **Trigger Deployment**
   - Railway automatically deploys on variable changes
   - Or click "Deploy" in the dashboard
   - Wait for build to complete (~3-5 minutes)

2. **Get Your App URL**
   - Find your app URL in the Railway dashboard
   - Format: `https://your-app-name.up.railway.app`

3. **Verify Health**
   - Visit: `https://your-app-name.up.railway.app/health`
   - Expected response: `{"status":"healthy","version":"1.0.0"}`

4. **Test Frontend**
   - Visit: `https://your-app-name.up.railway.app/`
   - Should load the chatbot interface

## Environment Variable Details

### OPENAI_API_KEY (Required)
Your OpenAI API key for AI model access.
```
OPENAI_API_KEY=sk-proj-your-key-here
```

### APP_TOKEN (Recommended)
Bearer token for protected endpoints. Generate a secure random string:
```bash
# Generate secure token
openssl rand -hex 32
# or
python -c "import secrets; print(secrets.token_hex(32))"
```

### CORS_ORIGINS (Important)
Configure allowed origins for web requests:
```
CORS_ORIGINS=["https://your-app-name.up.railway.app"]
```

### ENV (Optional)
Set to `production` for production optimizations:
```
ENV=production
```

## Post-Deployment Setup

### 1. Seed Demo Data
Use the Railway app URL in seed scripts:

```bash
# Update baseUrl in scripts to your Railway URL
export BASE_URL="https://your-app-name.up.railway.app"

# Run seed script (modify for Railway URL)
curl -X POST "$BASE_URL/api/v1/knowledge/files" \
     -F "file=@docs/sample_knowledge.txt"
```

### 2. Test Complete Workflow
1. Visit your Railway app URL
2. Upload `docs/sample_knowledge.txt`
3. Ask: "What is a data flywheel?"
4. Verify knowledge sources appear
5. Test feedback buttons
6. Load chat history

## Security Configuration

### Protected Endpoints
With `APP_TOKEN` set, these endpoints require authentication:
- `POST /api/v1/config` (create configurations)
- `GET /api/v1/chat-history` (view history)

### Usage Example
```bash
curl -X GET "https://your-app-name.up.railway.app/api/v1/chat-history" \
     -H "Authorization: Bearer your-app-token-here"
```

### CORS Security
Restrict CORS to your Railway domain only:
```
CORS_ORIGINS=["https://your-app-name.up.railway.app"]
```

## Monitoring and Maintenance

### Health Monitoring
- Health endpoint: `https://your-app-name.up.railway.app/health`
- Railway provides built-in monitoring and logs
- Set up uptime monitoring with external services if needed

### Viewing Logs
1. Go to Railway dashboard
2. Select your service
3. Click "Logs" tab
4. View real-time application logs

### Scaling
Railway automatically handles:
- Container restarts on crashes
- Basic load balancing
- SSL certificate management

## Limitations (Demo Environment)

### Data Persistence
- **SQLite database is ephemeral**
- Data lost on container restarts/deployments
- Uploaded files stored in container filesystem (also ephemeral)

### Scaling
- Single container deployment
- No horizontal scaling configured
- Suitable for demo/testing, not high-traffic production

### Storage
- No persistent volume mounts
- File uploads limited by container storage
- Consider cloud storage integration for production

## Troubleshooting

### Common Issues

#### 1. Build Failures
```
Error: Docker build failed
```
**Solution**: Check Dockerfile syntax and ensure all files are committed to GitHub

#### 2. Environment Variables Not Loading
```
Error: OPENAI_API_KEY not found
```
**Solution**: Verify environment variables are set in Railway dashboard

#### 3. CORS Errors
```
Error: CORS policy blocked
```
**Solution**: Update `CORS_ORIGINS` to include your Railway domain

#### 4. Health Check Fails
```
Error: /health returns 500
```
**Solution**: Check logs for startup errors, verify environment variables

### Debug Steps
1. **Check Railway Logs**
   - Dashboard → Service → Logs
   - Look for startup errors or crashes

2. **Verify Environment Variables**
   - Dashboard → Variables
   - Ensure all required variables are set

3. **Test Locally First**
   - Ensure Docker build works locally
   - Test with same environment variables

4. **Check GitHub Integration**
   - Verify Railway has access to your repository
   - Ensure latest code is pushed to GitHub

## Production Considerations

For production deployment, consider:

### Database Migration
```
# Add PostgreSQL service in Railway
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### File Storage
```
# Use cloud storage for uploads
AWS_S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

### Monitoring
- Set up application monitoring (Sentry, DataDog)
- Configure log aggregation
- Set up alerts for errors and downtime

### Security
- Use Railway's secret management
- Enable additional security headers
- Implement rate limiting
- Add authentication for admin endpoints

## Cost Estimation

Railway pricing (as of 2024):
- **Hobby Plan**: $5/month for basic apps
- **Pro Plan**: $20/month for production apps
- **Usage-based**: Additional costs for high resource usage

Demo deployment typically stays within free tier limits for testing purposes.

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: Community support
- **GitHub Issues**: For application-specific issues

---

**Quick Deploy Checklist:**
- [ ] Fork/clone repository to your GitHub
- [ ] Create Railway account
- [ ] Create new project from GitHub repo
- [ ] Set OPENAI_API_KEY environment variable
- [ ] Set CORS_ORIGINS with your Railway domain
- [ ] Deploy and verify /health endpoint
- [ ] Test frontend at your Railway URL
- [ ] Upload sample knowledge file
- [ ] Test complete chat workflow

Your Data Flywheel Chatbot should now be live and accessible worldwide! 🚀
