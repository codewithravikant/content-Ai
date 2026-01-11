# Railway Environment Variables Setup

This document explains how to configure environment variables as **secrets** in Railway to keep them secure and hidden from public view.

## ⚠️ Important: Environment Variables as Secrets

All sensitive environment variables **MUST** be set as **secrets** in Railway. Secrets are:
- ✅ Encrypted at rest
- ✅ Hidden from logs and build outputs
- ✅ Not visible in the Railway dashboard UI (only masked)
- ✅ Secure for production use

## Required Environment Variables

### Backend Service

Set these in your **Backend** service on Railway:

| Variable Name | Description | Required | Example |
|--------------|-------------|-----------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (starts with `sk-` or `sk-proj-`) | ✅ **Yes** | `sk-...` |
| `OPENAI_MODEL` | OpenAI model to use | No | `gpt-3.5-turbo` (default) |
| `AI_TIMEOUT` | Timeout for AI requests (seconds) | No | `60` (default) |
| `PORT` | Port for the backend service | No | Auto-set by Railway |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No | `https://your-frontend.railway.app` |
| `RATE_LIMIT_MAX_REQUESTS` | Max requests per window | No | `10` (default) |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window (seconds) | No | `60` (default) |
| `QUOTA_MAX_TOKENS_PER_DAY` | Daily token quota | No | `50000` (default) |
| `QUOTA_MAX_REQUESTS_PER_DAY` | Daily request quota | No | `100` (default) |

### Frontend Service

Set these in your **Frontend** service on Railway:

| Variable Name | Description | Required | Example |
|--------------|-------------|-----------|---------|
| `VITE_API_BASE_URL` | Backend API URL | ✅ **Yes** | `https://your-backend.railway.app` |
| `PORT` | Port for the frontend service | No | Auto-set by Railway |

## How to Set Environment Variables as Secrets in Railway

### Method 1: Railway Dashboard (Recommended)

1. **Navigate to your service** in Railway dashboard
2. Click on the **"Variables"** tab
3. Click **"+ New Variable"**
4. Enter the variable name (e.g., `OPENAI_API_KEY`)
5. Enter the variable value
6. **✅ IMPORTANT: Check the "Secret" checkbox** - This makes it a secret variable
7. Click **"Add"**

### Method 2: Railway CLI

```bash
# Install Railway CLI if not already installed
npm i -g @railway/cli

# Login to Railway
railway login

# Link your project
railway link

# Set a secret variable
railway variables set OPENAI_API_KEY=sk-your-key-here --secret

# Set multiple variables
railway variables set OPENAI_API_KEY=sk-your-key-here --secret
railway variables set VITE_API_BASE_URL=https://your-backend.railway.app --secret
```

### Method 3: Railway.toml (Not Recommended for Secrets)

⚠️ **Warning**: Do NOT put secrets in `railway.toml` or commit them to git. Use Railway dashboard or CLI instead.

## Step-by-Step Setup for Content AI

### 1. Deploy Backend Service

1. Create a new service in Railway
2. Connect your GitHub repository
3. Set root directory to: `backend`
4. Add environment variables as **secrets**:
   ```
   OPENAI_API_KEY=sk-your-openai-api-key (SECRET ✅)
   OPENAI_MODEL=gpt-3.5-turbo
   CORS_ORIGINS=https://your-frontend.railway.app
   ```
5. Railway will auto-detect Python and install dependencies
6. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Generate a public URL for your backend

### 2. Deploy Frontend Service

1. Create another service in Railway
2. Connect the same GitHub repository
3. Set root directory to: `frontend`
4. Add environment variables as **secrets**:
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app (SECRET ✅)
   ```
5. Railway will auto-detect Node.js and build the frontend
6. Generate a public URL for your frontend

### 3. Update CORS Settings

After deploying frontend, update the backend's `CORS_ORIGINS` variable:
```
CORS_ORIGINS=https://your-frontend.railway.app
```

## Verifying Secrets are Set Correctly

1. In Railway dashboard, go to your service → Variables tab
2. Secret variables will show as `••••••••` (masked)
3. You should see a lock icon 🔒 next to secret variables
4. **Never** see the actual values in logs or build outputs

## Security Best Practices

✅ **DO:**
- Always mark sensitive variables as **secrets**
- Use Railway's secret management
- Rotate API keys regularly
- Use different keys for development and production

❌ **DON'T:**
- Commit `.env` files to git
- Put secrets in `railway.toml`
- Share API keys in chat or documentation
- Use the same key for multiple projects

## Troubleshooting

### "Invalid API key" error
- Verify `OPENAI_API_KEY` is set as a secret
- Check the key starts with `sk-` or `sk-proj-`
- Ensure it's not a Google API key (starts with `AIza`)

### CORS errors
- Set `CORS_ORIGINS` to your frontend URL
- Include protocol (`https://`)
- No trailing slash

### Frontend can't connect to backend
- Verify `VITE_API_BASE_URL` is set correctly
- Check backend URL is accessible
- Ensure backend service is running

## Example Railway Service Configuration

### Backend Service
```
Root Directory: backend
Build Command: (auto-detected)
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check: /health
```

### Frontend Service
```
Root Directory: frontend
Build Command: npm run build
Start Command: npm run start
Static Assets: dist/
```

## Need Help?

If you encounter issues:
1. Check Railway service logs
2. Verify all required environment variables are set as secrets
3. Ensure backend URL is correct in frontend `VITE_API_BASE_URL`
4. Check CORS settings match your frontend URL

For more details, see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
