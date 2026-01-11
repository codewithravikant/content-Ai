# API Key Setup Guide

## Common Issue: Wrong API Key Type

If you're seeing this error:
```
openai.AuthenticationError: Error code: 401 - Incorrect API key provided: AIzaSy...
```

**This means you're using a Google API key instead of an OpenAI API key!**

## How to Fix

### Step 1: Get Your OpenAI API Key

1. Go to [https://platform.openai.com/account/api-keys](https://platform.openai.com/account/api-keys)
2. Sign in or create an OpenAI account
3. Click "Create new secret key"
4. Copy the key (it will start with `sk-` or `sk-proj-`)
5. **Important**: Save it somewhere safe - you won't be able to see it again!

### Step 2: Set the Environment Variable

#### For Local Development (macOS/Linux):
```bash
export OPENAI_API_KEY=sk-your_actual_openai_key_here
```

#### For Local Development (Windows):
```powershell
$env:OPENAI_API_KEY="sk-your_actual_openai_key_here"
```

#### For Docker/Docker Compose:
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=sk-your_actual_openai_key_here
```

#### For Railway:
1. Go to your Railway project dashboard
2. Select your backend service
3. Go to "Variables" tab
4. Add new variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: `sk-your_actual_openai_key_here`
5. Save - Railway will automatically redeploy

## Key Format Reference

| Service | Key Prefix | Example |
|---------|-----------|---------|
| **OpenAI** ✅ | `sk-` or `sk-proj-` | `sk-abc123...` |
| Google API ❌ | `AIza` | `AIzaSy...` |

## Verification

After setting your API key, verify it's correct:

```bash
# Check the first few characters (without exposing full key)
echo $OPENAI_API_KEY | cut -c1-5

# Should output: sk-ab or sk-pr (for OpenAI)
# If you see "AIza", you have the wrong key type!
```

## Common Mistakes

1. **Using Google API Key**: Keys starting with `AIza` are Google Cloud/Google AI keys, not OpenAI
2. **Missing `sk-` prefix**: OpenAI keys always start with `sk-` or `sk-proj-`
3. **Extra spaces**: Make sure there are no spaces around the key
4. **Using quotes incorrectly**: In bash, don't use quotes around the key when using `export`
5. **Wrong environment**: Make sure you're setting the variable in the correct terminal/environment

## Testing Your API Key

You can test if your API key works with a simple curl command:

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

If successful, you'll see a JSON response with available models. If you get a 401 error, your key is invalid.

## Security Best Practices

1. **Never commit API keys to Git** - They're already in `.gitignore`
2. **Use environment variables** - Don't hardcode keys in source code
3. **Rotate keys regularly** - Regenerate keys if you suspect they've been compromised
4. **Use different keys for dev/prod** - Don't reuse the same key
5. **Set usage limits** - Configure spending limits in OpenAI dashboard

## Still Having Issues?

If you've verified your key is correct but still getting errors:

1. Check if your OpenAI account has credits/billing set up
2. Verify the key hasn't been revoked in OpenAI dashboard
3. Check for typos or extra characters in the environment variable
4. Make sure you've restarted the backend server after setting the variable
5. For Docker: Make sure `.env` file is in the correct location and Docker Compose is reading it

For more help, check the [OpenAI API Documentation](https://platform.openai.com/docs/api-reference/authentication).
