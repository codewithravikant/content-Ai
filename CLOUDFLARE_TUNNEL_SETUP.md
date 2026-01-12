# Cloudflare Tunnel Setup for Local API Server

This guide helps you set up Cloudflare Tunnel to securely expose your local API server without exposing your home network or API keys.

## Prerequisites

1. Cloudflare account (free tier works)
2. cloudflared installed on your server
3. SSH access to your server
4. Local machine with a web browser

## Step 1: Authenticate cloudflared (Headless Server Setup)

Since you're on an SSH-only server, you need to authenticate from your local machine:

### Option A: Using the Login URL (Recommended for first time)

1. **On your SSH session** (leave it running):
   ```bash
   cloudflared tunnel login
   ```
   This will show you a URL like:
   ```
   https://dash.cloudflare.com/argotunnel?aud=&callback=https%3A%2F%2F...
   ```

2. **On your LOCAL machine** (laptop/desktop with browser):
   - Copy the entire URL from your SSH session
   - Paste it into your web browser
   - Log in with your Cloudflare account
   - Select the domain you want to use
   - The certificate will automatically download to your server

3. **Wait for confirmation** on your SSH session - it will say something like:
   ```
   You have successfully logged in.
   ```

### Option B: Using Token (Alternative for Headless Setup)

If you prefer token-based authentication:

1. Go to Cloudflare Zero Trust Dashboard: https://one.dash.cloudflare.com/
2. Go to: Networks → Tunnels → Create a tunnel
3. Choose "Cloudflared" as the connector
4. Copy the token shown
5. On your server, create a config file:
   ```bash
   mkdir -p ~/.cloudflared
   nano ~/.cloudflared/config.yml
   ```
6. Add:
   ```yaml
   tunnel: <your-tunnel-id>
   credentials-file: /home/raviadmin/.cloudflared/<tunnel-id>.json
   ```

## Step 2: Create a Tunnel

After authentication, create a tunnel:

```bash
cloudflared tunnel create content-ai-tunnel
```

This will give you a tunnel ID (save it).

## Step 3: Configure the Tunnel

Create a configuration file:

```bash
mkdir -p ~/.cloudflared
nano ~/.cloudflared/config.yml
```

Add this configuration (adjust the port if your API runs on a different port):

```yaml
tunnel: <your-tunnel-id-from-step-2>
credentials-file: /home/raviadmin/.cloudflared/<tunnel-id>.json

ingress:
  # Route API requests to your local server
  - hostname: api.yourdomain.com  # Change to your subdomain
    service: http://localhost:8000  # Change port if needed
  # Catch-all rule (must be last)
  - service: http_status:404
```

**Important Notes:**
- Replace `<your-tunnel-id>` with the actual tunnel ID from step 2
- Replace `api.yourdomain.com` with your actual subdomain
- Change `localhost:8000` if your API runs on a different port
- The catch-all rule (404) must be the last entry

## Step 4: Route DNS

1. Go to your Cloudflare dashboard → DNS settings
2. Add a CNAME record:
   - **Name**: `api` (or whatever subdomain you chose)
   - **Target**: `<tunnel-id>.cfargotunnel.com`
   - **Proxy status**: Proxied (orange cloud ☁️)

## Step 5: Run the Tunnel

### For Testing (Foreground):
```bash
cloudflared tunnel run content-ai-tunnel
```

### For Production (Background Service):

Create a systemd service:

```bash
sudo nano /etc/systemd/system/cloudflared.service
```

Add:
```ini
[Unit]
Description=Cloudflare Tunnel
After=network.target

[Service]
Type=simple
User=raviadmin
ExecStart=/usr/bin/cloudflared tunnel --config /home/raviadmin/.cloudflared/config.yml run
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

## Step 6: Update Frontend Configuration

Once your tunnel is running, update your frontend to use the Cloudflare tunnel URL:

1. In Railway (or wherever your frontend is deployed):
   - Add environment variable: `VITE_API_BASE_URL=https://api.yourdomain.com`
   - Redeploy the frontend

2. Or locally, create `frontend/.env`:
   ```env
   VITE_API_BASE_URL=https://api.yourdomain.com
   ```

## Quick Test (No Domain Needed)

If you don't want to set up DNS yet, you can use a quick tunnel for testing:

```bash
cloudflared tunnel --url http://localhost:8000
```

This will give you a temporary URL like `https://random-name.trycloudflare.com` that you can use immediately.

## Troubleshooting

### Check if tunnel is running:
```bash
cloudflared tunnel list
cloudflared tunnel info content-ai-tunnel
```

### View logs:
```bash
sudo journalctl -u cloudflared -f
```

### Test your API through the tunnel:
```bash
curl https://api.yourdomain.com/health
```

### Common Issues:

1. **"Permission denied"** - Make sure the credentials file has correct permissions:
   ```bash
   chmod 600 ~/.cloudflared/*.json
   ```

2. **"Tunnel not found"** - Verify tunnel ID matches in config.yml

3. **"Connection refused"** - Make sure your local API is running on the correct port

4. **Certificate not found** - Re-run `cloudflared tunnel login`

## Security Benefits

✅ No port forwarding needed on your router
✅ Your home IP is never exposed
✅ API keys stay private (only accessible through tunnel)
✅ SSL/TLS encryption automatically handled by Cloudflare
✅ Can add Cloudflare Access policies for additional authentication
