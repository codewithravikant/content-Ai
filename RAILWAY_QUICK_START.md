# Railway Quick Start Guide

## Deploy Ghostwriter on Railway in 5 Minutes

### Prerequisites
- GitHub account
- Railway account ([railway.app](https://railway.app))
- OpenAI API key

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your Ghostwriter repository
5. Railway will detect it's a monorepo

### Step 3: Deploy Backend Service

1. Click **"Add Service"** → **"GitHub Repo"**
2. Select your repository
3. In service settings:
   - **Root Directory**: Set to `backend`
   - Railway will auto-detect Python and use `nixpacks.toml`

4. **Add Environment Variables**:
   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_MODEL=gpt-3.5-turbo
   CORS_ORIGINS=*
   ```
   (You'll update CORS_ORIGINS after frontend deploys)

5. Railway will automatically:
   - Build the service
   - Deploy it
   - Generate a public URL (e.g., `https://ghostwriter-backend-production.up.railway.app`)

6. **Copy the backend URL** from Railway dashboard

### Step 4: Deploy Frontend Service

1. In the same Railway project, click **"Add Service"** → **"GitHub Repo"**
2. Select the same repository
3. In service settings:
   - **Root Directory**: Set to `frontend`
   - Railway will auto-detect Node.js and use `nixpacks.toml`

4. **Add Environment Variable**:
   ```
   VITE_API_BASE_URL=https://your-backend-url.railway.app
   ```
   Replace with your actual backend URL from Step 3

5. Railway will automatically build and deploy

6. **Copy the frontend URL** from Railway dashboard

### Step 5: Update CORS (Important!)

1. Go back to your **Backend Service** in Railway
2. Click **"Variables"** tab
3. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://your-frontend-url.railway.app
   ```
   Replace with your actual frontend URL from Step 4

4. Railway will automatically redeploy with the new CORS settings

### Step 6: Test Your Deployment

1. Visit your frontend URL (from Step 4)
2. Try generating content
3. Check Railway logs if there are any issues

## Environment Variables Reference

### Backend Service Variables
- `OPENAI_API_KEY` - **Required**: Your OpenAI API key
- `OPENAI_MODEL` - Optional: Model to use (default: `gpt-3.5-turbo`)
- `CORS_ORIGINS` - **Required**: Frontend URL (comma-separated if multiple)
- `PORT` - Auto-set by Railway (don't set manually)

### Frontend Service Variables
- `VITE_API_BASE_URL` - **Required**: Backend service URL
- `PORT` - Auto-set by Railway (don't set manually)

## Troubleshooting

**Frontend can't connect to backend:**
- Check `VITE_API_BASE_URL` is set correctly
- Verify backend URL is accessible
- Check CORS_ORIGINS includes frontend URL

**CORS errors:**
- Ensure `CORS_ORIGINS` includes your frontend URL exactly
- No trailing slashes in URLs
- Use `https://` not `http://`

**Build fails:**
- Check Railway logs for specific errors
- Verify all environment variables are set
- Ensure code is pushed to GitHub

**Port binding errors:**
- Railway sets `$PORT` automatically - don't hardcode ports
- Use `0.0.0.0` as host (not `localhost`)

## Next Steps

- Add custom domain in Railway dashboard
- Set up monitoring and alerts
- Configure auto-scaling if needed
- Set up CI/CD for automatic deployments

For detailed deployment guide, see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
