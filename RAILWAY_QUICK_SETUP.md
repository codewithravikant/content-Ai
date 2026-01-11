# Railway Quick Setup Guide for Content AI

## Prerequisites
- Railway account (sign up at https://railway.app)
- GitHub repository connected
- OpenAI API key

## Quick Deployment Steps

### 1. Deploy Backend Service

1. **Create New Service** in Railway dashboard
2. **Connect GitHub** → Select your repository
3. **Configure Service:**
   - Root Directory: `backend`
   - Build Command: (auto-detected)
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. **Set Environment Variables (as SECRETS):**
   ```
   OPENAI_API_KEY=sk-your-key-here (🔒 SECRET)
   OPENAI_MODEL=gpt-3.5-turbo
   CORS_ORIGINS=https://your-frontend.railway.app
   ```

5. **Generate Public URL** for backend (e.g., `https://content-ai-backend.railway.app`)

### 2. Deploy Frontend Service

1. **Create New Service** in Railway dashboard
2. **Connect GitHub** → Select the same repository
3. **Configure Service:**
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Start Command: `npm run start`

4. **Set Environment Variables (as SECRETS):**
   ```
   VITE_API_BASE_URL=https://your-backend.railway.app (🔒 SECRET)
   ```

5. **Generate Public URL** for frontend

### 3. Update CORS

After frontend is deployed, update backend's `CORS_ORIGINS`:
```
CORS_ORIGINS=https://your-frontend.railway.app
```

## Important: Secrets Configuration

⚠️ **ALWAYS mark sensitive variables as SECRETS in Railway:**

1. Go to Service → Variables tab
2. Click "+ New Variable"
3. Enter name and value
4. **✅ Check "Secret" checkbox**
5. Click "Add"

Secret variables are:
- Encrypted at rest
- Hidden from logs
- Not visible in UI (masked)

## Environment Variables Reference

### Backend (Required)
- `OPENAI_API_KEY` - Your OpenAI API key (🔒 SECRET)
- `CORS_ORIGINS` - Frontend URL (after frontend is deployed)

### Backend (Optional)
- `OPENAI_MODEL` - Model to use (default: `gpt-3.5-turbo`)
- `RATE_LIMIT_MAX_REQUESTS` - Max requests (default: `10`)
- `QUOTA_MAX_TOKENS_PER_DAY` - Daily token limit (default: `50000`)

### Frontend (Required)
- `VITE_API_BASE_URL` - Backend service URL (🔒 SECRET)

## Verification

1. Backend health check: `https://your-backend.railway.app/health`
2. Frontend should load and connect to backend
3. Test content generation

## Troubleshooting

- **CORS errors**: Update `CORS_ORIGINS` with frontend URL
- **API key errors**: Verify `OPENAI_API_KEY` is set as secret
- **Connection errors**: Check `VITE_API_BASE_URL` matches backend URL

For detailed setup, see [RAILWAY_ENV_VARIABLES.md](./RAILWAY_ENV_VARIABLES.md)
