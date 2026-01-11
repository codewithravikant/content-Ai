# Railway Deployment Guide

This guide will help you deploy Ghostwriter on Railway.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. An OpenAI API key
3. A GitHub account (if deploying from Git)

## Deployment Options

Railway supports deploying this application in two ways:

### Option 1: Deploy as Separate Services (Recommended)

This is the recommended approach as it allows independent scaling and easier management.

#### Step 1: Create a New Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo" (or "Empty Project" for manual setup)

#### Step 2: Deploy Backend Service

1. In your Railway project, click "New Service"
2. Select "GitHub Repo" and choose your repository
3. Railway will detect the `backend/` directory automatically
4. Configure the service:
   - **Root Directory**: `backend`
   - **Build Command**: (auto-detected by Nixpacks)
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Set Environment Variables**:
   ```
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-3.5-turbo
   AI_TIMEOUT=60
   RATE_LIMIT_MAX_REQUESTS=10
   RATE_LIMIT_WINDOW_SECONDS=60
   QUOTA_MAX_TOKENS_PER_DAY=50000
   QUOTA_MAX_REQUESTS_PER_DAY=100
   CORS_ORIGINS=*
   ```
   (You'll update CORS_ORIGINS after deploying frontend)

6. Railway will automatically:
   - Build the service
   - Deploy it
   - Generate a public URL (e.g., `https://ghostwriter-backend.railway.app`)

#### Step 3: Deploy Frontend Service

1. In the same Railway project, click "New Service" again
2. Select "GitHub Repo" and choose the same repository
3. Configure the service:
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Start Command**: `npx serve -s dist -l $PORT`

4. **Set Environment Variables**:
   ```
   VITE_API_BASE_URL=https://your-backend-service.railway.app
   ```
   Replace `your-backend-service` with your actual backend Railway URL

5. After deployment, update backend's `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://your-frontend-service.railway.app
   ```

#### Step 4: Configure Service URLs

1. Get your backend service URL from Railway dashboard
2. Update frontend environment variable `VITE_API_BASE_URL` with backend URL
3. Redeploy frontend if needed
4. Update backend `CORS_ORIGINS` with frontend URL

### Option 2: Deploy with Docker Compose (Monorepo)

Railway also supports Docker Compose deployments:

1. Create a new Railway project
2. Add `railway.json` configuration (already included)
3. Railway will detect `docker-compose.yml`
4. Set all environment variables in Railway dashboard
5. Deploy

**Note**: For monorepo deployments, you may need to configure Railway to build from the root directory.

## Environment Variables Reference

### Backend Service

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | Yes |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-3.5-turbo` | No |
| `AI_TIMEOUT` | AI request timeout (seconds) | `60` | No |
| `PORT` | Server port (set by Railway) | `8000` | Auto |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` | No |
| `RATE_LIMIT_MAX_REQUESTS` | Max requests per window | `10` | No |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window size | `60` | No |
| `QUOTA_MAX_TOKENS_PER_DAY` | Daily token quota | `50000` | No |
| `QUOTA_MAX_REQUESTS_PER_DAY` | Daily request quota | `100` | No |

### Frontend Service

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `VITE_API_BASE_URL` | Backend API URL | `/api` (prod) | No |
| `PORT` | Server port (set by Railway) | `3000` | Auto |

## Railway-Specific Features

### Health Checks

Railway will automatically check:
- Backend: `/health` endpoint
- Frontend: Root path `/`

### Custom Domain

1. In Railway dashboard, go to your service
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Update `CORS_ORIGINS` to include your custom domain

### Environment Variables

Railway supports:
- **Shared Variables**: Set at project level (available to all services)
- **Service Variables**: Set at service level (specific to that service)

For this app:
- Set `OPENAI_API_KEY` as a **Shared Variable** (if both services need it)
- Set `VITE_API_BASE_URL` as **Frontend Service Variable**
- Set `CORS_ORIGINS` as **Backend Service Variable**

### Logs and Monitoring

Railway provides:
- Real-time logs in dashboard
- Log aggregation and search
- Metrics and monitoring
- Error tracking

### Scaling

Railway auto-scales based on:
- CPU usage
- Memory usage
- Request volume

You can also manually scale in the dashboard.

## Troubleshooting

### Backend Issues

**Service won't start:**
- Check `OPENAI_API_KEY` is set correctly
- Verify Python dependencies installed
- Check logs for specific errors

**CORS errors:**
- Ensure `CORS_ORIGINS` includes your frontend URL
- Check for trailing slashes in URLs
- Verify frontend `VITE_API_BASE_URL` matches backend URL

**Port binding errors:**
- Railway sets `$PORT` automatically - don't hardcode port
- Ensure using `0.0.0.0` as host (not `localhost`)

### Frontend Issues

**Build fails:**
- Check Node.js version (should be 18+)
- Verify all dependencies in `package.json`
- Check for TypeScript errors

**API calls fail:**
- Verify `VITE_API_BASE_URL` is set correctly
- Check backend service is running
- Ensure CORS is configured properly

**Static files not serving:**
- Verify `dist` directory is built
- Check `nixpacks.toml` or build configuration
- Ensure start command serves from `dist`

## Updating Deployment

### Via Git (Recommended)

1. Push changes to your GitHub repository
2. Railway will automatically detect changes
3. Railway will rebuild and redeploy

### Manual Deploy

1. In Railway dashboard, go to your service
2. Click "Deploy" → "Redeploy"
3. Or use Railway CLI: `railway up`

## Railway CLI (Optional)

Install Railway CLI for easier management:

```bash
npm i -g @railway/cli
railway login
railway link  # Link to your project
railway up    # Deploy
railway logs  # View logs
railway variables  # Manage environment variables
```

## Cost Considerations

Railway offers:
- **Free tier**: $5/month credit
- **Hobby**: $20/month (includes custom domains)
- **Pro**: $100/month (higher limits)

Ghostwriter typically uses:
- Backend: ~512MB RAM, low CPU
- Frontend: ~256MB RAM, minimal CPU

Both services should fit comfortably in the free tier for moderate usage.

## Support

For Railway-specific issues:
- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)

For Ghostwriter issues:
- Check the main README.md
- Review logs in Railway dashboard
