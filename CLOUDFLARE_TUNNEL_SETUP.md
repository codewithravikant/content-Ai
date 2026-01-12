# Cloudflare Tunnel Setup (Deprecated)

⚠️ **This document is deprecated.** Cloudflare Tunnel setup is no longer needed for this project.

## New Approach: Hugging Face Inference API

This project now uses the **Hugging Face Inference API** instead of local servers with Cloudflare tunnels. This approach:

- ✅ Requires no local server setup
- ✅ No tunnel configuration needed
- ✅ Fully cloud-based (Railway + Hugging Face)
- ✅ Simplified architecture
- ✅ HTTPS ready out of the box

## Migration Guide

If you were previously using Falcon API with Cloudflare tunnel, you should now:

1. **Get a Hugging Face API token:**
   - Sign up at [huggingface.co](https://huggingface.co)
   - Go to Settings → Access Tokens
   - Create a new token

2. **Update your environment variables:**
   - Remove `FALCON_API_BASE_URL` and `FALCON_API_KEY`
   - Add `HF_API_KEY=hf_your-token-here`
   - Set `AI_PROVIDER=huggingface`

3. **For Railway deployment:**
   - Set `HF_API_KEY` as a secret environment variable
   - Set `AI_PROVIDER=huggingface`
   - See [RAILWAY_ENV_VARIABLES.md](./RAILWAY_ENV_VARIABLES.md) for details

## Why This Change?

The Hugging Face Inference API provides:
- Direct cloud-based access to models
- No infrastructure management
- Better reliability (no tunnel dependencies)
- Easier deployment on Railway
- Support for many open-source models

For setup instructions, see the main [README.md](./README.md) file.
