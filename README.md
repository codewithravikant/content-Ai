# Ghostwriter - AI Content Generation Platform

A powerful content generation platform that uses AI to create ready-to-use content for blogs, emails, stories, and social media posts. Built with React (Vite) frontend and FastAPI backend, featuring streaming responses, comprehensive validation, and multiple export formats.

**Repository:** [https://gitea.kood.tech/ravikantpandit/ghostwriter](https://gitea.kood.tech/ravikantpandit/ghostwriter)

## testing deployment 
https://web-aiforme.up.railway.app/


## Features

- **Multiple Content Types**: Blog Posts, Email, Social Media Posts, LinkedIn Posts, and Job Applications with content-specific inputs
- **Streaming Responses**: Real-time content generation using Server-Sent Events (SSE)
- **Input Validation**: Comprehensive validation and normalization to prevent API errors
- **Prompt Engineering**: Zero-shot and few-shot prompting with prompt injection defenses
- **Post-Processing**: Automatic structure parsing, word count validation, AI artifact removal
- **Rich Editor**: Tiptap editor with live Markdown preview
- **Multiple Export Formats**: Plain text, Markdown, HTML, and PDF export
- **Form Persistence**: LocalStorage persistence to prevent data loss
- **Rate Limiting & Quotas**: Per-IP rate limiting and daily token quotas
- **Caching**: In-memory caching for identical requests
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Observability**: Structured logging and metrics
- **Docker Support**: Single-command deployment with Docker Compose
- **CI/CD**: GitHub Actions pipeline for linting, testing, and Docker builds

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   React     │────────▶│   FastAPI   │────────▶│ OpenRouter  │
│  Frontend   │◀────────│   Backend   │◀────────│   API       │
└─────────────┘         └─────────────┘         └─────────────┘
     │                        │
     │                        │
     ▼                        ▼
  localStorage          Rate Limiter
                        Cache
                        Quota Manager
```

## Prerequisites

- Docker and Docker Compose (recommended — avoids local Python/Node version issues)
- OR Node.js 18+ and Python 3.11+ (3.11 is the most predictable for backend wheels; 3.13 works with current `requirements.txt`)
- An OpenRouter API key ([openrouter.ai/keys](https://openrouter.ai/keys)) — **for shared keys, rotation, or access questions, contact the maintainer** (see [Support](#support))

## Quick Start (Docker)

1. **Clone the repository**
   ```bash
   git clone https://gitea.kood.tech/ravikantpandit/ghostwriter.git
   cd ghostwriter
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENROUTER_API_KEY
   ```

3. **Run with Docker Compose** (single command)
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build both frontend and backend Docker images
   - Start the backend API on http://localhost:8000
   - Start the frontend on http://localhost:3000
   - No manual dependency installation required!

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Deploy on Railway

Ghostwriter is ready for a **single-service Railway deployment** (recommended).  
See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for full details.

**Quick Railway Deployment (single service):**

1. Push your code to your Git remote (e.g. [Gitea](https://gitea.kood.tech/ravikantpandit/ghostwriter))
2. Create a new Railway project and add **one service** from this repo
3. Keep service root at repo root (`.`) so Railway uses `railway.toml` + root `Dockerfile`
4. Generate a public domain for the service
5. Set service Variables:
   - `GHOSTWRITER_ENV=production`
   - `CORS_ORIGINS=https://<your-service-domain>`
   - `OPENROUTER_API_KEY=<your-key>`
   - `OPENROUTER_MODEL=<your-model>` (optional)
   - Email variables (`EMAIL_BACKEND`, `RESEND_*` or `SMTP_*`) as needed
6. Deploy and verify:
   - `https://<your-service-domain>/health`
   - Open app root URL and generate content

For details and troubleshooting, see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md).

## Manual Setup

Use the steps below **from the repository root** unless a step says otherwise.

### Plug-and-play: configure OpenRouter from the terminal

**Typical local flow (first time on a machine or clone):**

1. **Save the API key** (once per machine / clone)  
   ```bash
   make configure
   ```  
   This interactively writes `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` into **`backend/.env`** (creates it from `backend/.env.example` if needed, `chmod 600`).

2. **Install dependencies** (once, or after `make clean`)  
   ```bash
   make setup
   ```

3. **Run the backend and frontend together**  
   ```bash
   make dev
   ```  
   - Backend: http://localhost:8000  
   - Frontend: http://localhost:3000  
   - API docs: http://localhost:8000/docs  

**One-liner** (after you are comfortable with the prompts in step 1):

```bash
make configure && make setup && make dev
```

After the first successful `make setup`, you usually only need `make dev` unless you change the key, run `make clean`, or switch machines.

**Optional variants**

- **Repo root `.env` as well** (same OpenRouter variables only): `make configure-root` — or run `make configure` first, then `make configure-root` if you need both files aligned.
- **Alias:** `make init-env` is the same as `make configure`.
- **CI / automation:** `make configure` needs an interactive TTY. In pipelines, set secrets in your platform and use non-interactive `.env` files or environment variables instead.

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   # Or if pip is not available, use: pip3 install -r requirements.txt
   ```

4. **Set environment variables**

   **Option A — recommended:** from the repo root, run `make configure` (see [Plug-and-play](#plug-and-play-configure-openrouter-from-the-terminal) above).

   **Option B — manual:** copy the example and edit, or export for the current shell only:

   ```bash
   cp .env.example .env   # inside backend/
   # Edit .env: set OPENROUTER_API_KEY (and optionally OPENROUTER_MODEL)
   ```

   ```bash
   # Or one-off exports (not persisted):
   export OPENROUTER_API_KEY=your_openrouter_api_key_here
   export OPENROUTER_MODEL=openai/gpt-3.5-turbo  # Optional
   ```
   
   **Important Notes:**
   - OpenRouter gives one key to route across multiple model providers
   - Model names use `provider/model` format (example: `google/gemini-flash-1.5`)
   - Get your OpenRouter API key from: https://openrouter.ai/keys
   - See [API_KEY_SETUP.md](./API_KEY_SETUP.md) for detailed setup instructions

5. **Run the server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create .env file** (optional — if you omit it, the dev app uses same-origin `/api`, which Vite proxies to `http://localhost:8000`)
   ```bash
   # Only if you need direct calls to the backend (not via /api proxy):
   # echo "VITE_API_BASE_URL=http://localhost:8000" > .env
   ```

4. **Run the development server**
   ```bash
   npm run dev
   ```

5. **Build for production**
   ```bash
   npm run build
   npm run preview
   ```

## Environment Variables

The backend loads environment variables from **two** files, in order: the repository root `.env`, then **`backend/.env`** (which overrides the root file). You can put `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` in either place; using `backend/.env` keeps backend secrets next to the FastAPI app.

Create a `.env` file in the project root and/or `backend/.env` (templates: `.env.example` at the root and [`backend/.env.example`](backend/.env.example)):

```env
# OpenRouter configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-3.5-turbo
APP_URL=http://localhost:3000

# AI Generation Settings
AI_TIMEOUT=60  # Timeout in seconds for AI API calls

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Quota Management
QUOTA_MAX_TOKENS_PER_DAY=50000
QUOTA_MAX_REQUESTS_PER_DAY=100

# Frontend API URL (optional; default in app is /api — Vite/nginx proxy to backend)
# VITE_API_BASE_URL=http://localhost:8000

# CORS
CORS_ORIGINS=http://localhost:3000

# Logging (default is quiet: WARNING). Use LOG_LEVEL=INFO or DEBUG for request/token/AI logs.
# GHOSTWRITER_DEBUG=1 sets DEBUG when LOG_LEVEL is unset (includes postprocess detail).
# LOG_LEVEL=WARNING
```

### OpenRouter Setup

1. Create an account and API key at [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Set `OPENROUTER_API_KEY=your_key_here` in your **root** `.env` and/or **`backend/.env`** (same variable name; `backend/.env` wins if both are set).
3. Set `OPENROUTER_MODEL` to one supported model, for example:
   - `openai/gpt-3.5-turbo`
   - `google/gemini-flash-1.5`
   - `anthropic/claude-3-haiku`
   - `meta-llama/llama-3-8b-instruct`
   - `qwen/qwen3.6-plus:free` (example free tier; IDs are always `provider/model`, not `openai/qwen/...`)
4. Optionally set `APP_URL` so OpenRouter usage analytics can attribute requests to your app

### Email Verification (OTP) Setup

When `GHOSTWRITER_REQUIRE_EMAIL_LOGIN=true`, the backend sends one-time verification codes by the configured email backend.

Quick helper:

```bash
make email-help
```

Choose one delivery option in `backend/.env`:

**A) Local Mailpit (dev default)**

```env
EMAIL_BACKEND=smtp
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_FROM=ghostwriter@localhost
```

- Run Mailpit in another terminal: `make mailpit`
- Open inbox UI: `http://localhost:8025`

**B) Resend (real inbox, HTTP API)**

```env
EMAIL_BACKEND=resend
RESEND_API_KEY=re_xxxxxxxx
RESEND_FROM=onboarding@resend.dev
```

- Create key at [https://resend.com/api-keys](https://resend.com/api-keys)
- For production, prefer a verified domain sender

**C) Gmail SMTP (real inbox, App Password)**

```env
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USE_SSL=1
SMTP_USER=codewithravikant@gmail.com
SMTP_PASSWORD=<16-char Google App Password>
SMTP_FROM=Content AI <codewithravikant@gmail.com>
```

- Gmail requires 2FA and an App Password (do not use your normal account password)
- Restart backend after changing env values

### Secret Management

For production deployments, use a secret manager:
- **AWS Secrets Manager**: Store `OPENROUTER_API_KEY` and retrieve at runtime
- **GCP Secret Manager**: Similar approach for GCP deployments
- **Docker Secrets**: Use Docker secrets for containerized deployments
- **Kubernetes Secrets**: Use K8s secrets for orchestrated deployments

Example with AWS Secrets Manager (Python):
```python
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='ghostwriter/openrouter-key')
api_key = secret['SecretString']
```

### Encryption and decryption (examples)

Use these patterns to keep secrets off disk in plaintext when sharing backups or committing *encrypted* blobs only (never commit keys or passwords).

**1) OpenSSL (file at rest)**

Encrypt a local env file (you will be prompted for a password; use a strong secret and store it in a password manager, not in git):

```bash
openssl enc -aes-256-cbc -salt -pbkdf2 -in backend/.env -out backend/.env.enc
# Decrypt when you need to run locally:
openssl enc -aes-256-cbc -d -pbkdf2 -in backend/.env.enc -out backend/.env
```

**2) Python `cryptography` (Fernet — string secrets)**

Install once: `pip install cryptography`.

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()  # store key securely, e.g. env var or vault
f = Fernet(key)
ciphertext = f.encrypt(b"sk-your-openrouter-key-here")
plaintext = f.decrypt(ciphertext).decode()
```

**3) Operational notes**

- Prefer platform secrets (Railway, Docker secrets, cloud KMS) over ad-hoc file encryption for production.
- **API keys:** provisioning, rotation, or team access — **contact the maintainer** (see [Support](#support)).
- Do not commit `backend/.env`, decrypted payloads, or Fernet keys.

## API Endpoints

### Generate Content (POST /generate)

Generate content based on user input.

**Request:**
```json
{
  "content_type": "blog_post",
  "context": {
    "topic": "Introduction to Machine Learning",
    "audience": "General public",
    "tone": "engaging"
  },
  "specifications": {
    "word_target": 450,
    "seo_enabled": true,
    "expertise": "beginner"
  },
  "generation_params": {
    "temperature": 0.7,
    "max_tokens": 1200,
    "top_p": 0.9
  }
}
```

**Response:**
```json
{
  "content": "# Introduction to Machine Learning\n\n...",
  "metadata": {
    "word_count": 897,
    "sections": ["Introduction", "Main Section 1", "Conclusion"],
    "tokens_used": 1200,
    "estimated_read_time": "4 minutes",
    "seo_keywords": ["machine learning", "ai", "algorithms"]
  }
}
```

#### Example payloads (every `content_type`)

Use the same endpoint: `POST /generate` with `Content-Type: application/json`. Optional `generation_params` controls temperature and length.

**`blog_post`**
```json
{
  "content_type": "blog_post",
  "context": {
    "topic": "Benefits of morning walks",
    "audience": "General health readers",
    "tone": "friendly"
  },
  "specifications": {
    "word_target": 200,
    "seo_enabled": false,
    "expertise": "beginner"
  },
  "generation_params": { "temperature": 0.7, "max_tokens": 1200, "top_p": 0.9 }
}
```

**`email`**
```json
{
  "content_type": "email",
  "context": {
    "purpose": "Follow up after product demo",
    "recipient_context": "Prospect at a mid-size SaaS company",
    "key_points": "Thank them; summarize next steps; propose a call next week",
    "tone": "professional"
  },
  "specifications": {
    "urgency_level": "medium",
    "cta": "Reply with a time that works"
  },
  "generation_params": { "temperature": 0.7, "max_tokens": 2000, "top_p": 0.9 }
}
```

**`social_media`**
```json
{
  "content_type": "social_media",
  "context": {
    "platform": "x",
    "topic": "Why readable code matters",
    "tone": "casual",
    "goal": "engagement"
  },
  "specifications": { "hashtag_count": 3, "word_target": 120 },
  "generation_params": { "temperature": 0.7, "max_tokens": 2000, "top_p": 0.9 }
}
```

**`linkedin`**
```json
{
  "content_type": "linkedin",
  "context": {
    "topic": "Lessons from shipping an MVP",
    "target_audience": "Engineering leaders and founders",
    "engagement_goal": "comments and shares",
    "tone": "professional"
  },
  "specifications": { "word_target": 200, "include_hashtags": true },
  "generation_params": { "temperature": 0.7, "max_tokens": 2000, "top_p": 0.9 }
}
```

**`job_application`**
```json
{
  "content_type": "job_application",
  "context": {
    "position_title": "Senior Backend Engineer",
    "company_name": "Example Corp",
    "key_qualifications": "Python, FastAPI, Postgres, distributed systems, and team leadership experience",
    "experience_level": "senior"
  },
  "specifications": {
    "application_type": "cover_letter",
    "word_target": 300
  },
  "generation_params": { "temperature": 0.7, "max_tokens": 2000, "top_p": 0.9 }
}
```

**curl (local backend)**

```bash
curl -sS -X POST 'http://127.0.0.1:8000/generate' \
  -H 'Content-Type: application/json' \
  -d @payload.json
```

With the Vite dev proxy (frontend on port 3000): `POST http://localhost:3000/api/generate` with the same JSON body.

### Stream Generation (GET /generate/stream)

Stream content generation using Server-Sent Events (SSE).

**Query Parameters:**
- `data`: JSON-encoded GenerateRequest

**Response:** Server-Sent Events stream

### Export PDF (POST /export/pdf)

Export content to PDF format (backend rendering).

**Request:**
```json
{
  "content": "# Blog Post Title\n\n...",
  "content_type": "blog_post"
}
```

**Response:** PDF binary file

### Health Check (GET /health)

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "ghostwriter"
}
```

### Metrics (GET /metrics)

Get API metrics.

**Response:**
```json
{
  "status": "ok",
  "cache_size": 42
}
```

## Content Types

### Blog Post

**API / JSON (`context` + `specifications`):**
- `topic`: Blog post topic (3-200 characters)
- `audience`: Target audience (3-100 characters) — the UI label is “Target audience”; the API field is `audience`
- `tone`: Tone (professional, casual, friendly, formal, engaging, persuasive)
- `word_target`: Target length as a **number** (**blog: 10–500**; other types may differ) — the form collects a `"min-max"` range and normalizes to the median before calling the API

**Required Fields (UI form):**
- Same as above, plus word count as a range string (e.g. `"100-300"`) which is normalized to `word_target`

**Optional Fields:**
- `seo_focus`: Enable SEO optimization (boolean)
- `expertise_level`: Expertise level (beginner, intermediate, advanced)

**Output Structure:**
- Title (H1)
- Introduction paragraph
- 3-4 main sections with headers (H2)
- Conclusion

### Email

**Required Fields:**
- `purpose`: Email purpose (5-200 characters)
- `recipient_context`: Recipient context (5-500 characters)
- `key_points`: Key points to convey (10-1000 characters)
- `tone`: Tone (professional, casual, friendly, formal, engaging, persuasive)

**Optional Fields:**
- `urgency_level`: Urgency level (low, medium, high)
- `cta`: Call to action (max 100 characters)

**Output Structure:**
- Subject line
- Professional greeting
- Well-organized body paragraphs
- Professional closing

### Social Media Post

**Required Fields:**
- `platform`: Platform id or name (1-50 characters), e.g. `x`, `instagram`, `linkedin`
- `topic`: Post topic (3-500 characters)
- `tone`: Tone (professional, casual, friendly, formal, engaging, persuasive)

**Optional Fields:**
- `goal`: Post goal/purpose (max 200 characters)
- `hashtag_count`: Number of hashtags to include (0-20, default: 3)
- `word_count`: Word count range — **blog: 10–500 words** (default: `"100-300"`)

**Output Structure:**
- Platform-optimized post content
- Relevant hashtags (format: #hashtag1 #hashtag2 ...)

### LinkedIn Post

**Required Fields:**
- `topic`: Post topic (3-500 characters)
- `target_audience`: Target audience (3-200 characters)
- `tone`: Tone (professional, casual, friendly, formal, engaging, persuasive)

**Optional Fields:**
- `engagement_goal`: Engagement goal (max 200 characters)
- `word_count`: Word count range - **Minimum: 50 words** (default: "200-400")
- `include_hashtags`: Include hashtags (boolean, default: true)

**Output Structure:**
- Professional LinkedIn post with hook
- Value-driven content
- Clear takeaway
- Call to action
- Optional hashtags

### Job Application

**Required Fields:**
- `position_title`: Position title (3-200 characters)
- `company_name`: Company name (2-200 characters)
- `key_qualifications`: Key qualifications (10-1000 characters)
- `experience_level`: Experience level (3-50 characters)

**Optional Fields:**
- `application_type`: Application type ("cover_letter" or "application_letter", default: "cover_letter")
- `word_count`: Word count range - **Minimum: 50 words** (default: "300-500")

**Output Structure:**
- Professional greeting
- Introduction paragraph
- 2-3 body paragraphs highlighting qualifications
- Closing paragraph
- Professional sign-off

## Input Validation & Normalization

The platform validates and normalizes all inputs before prompt generation:

- **Word Count**: Converts ranges like `"100-300"` to a target integer (median); **blog posts clamp to 10–500 words**
- **Tone**: Normalizes to lowercase and validates against allowed values
- **Default Parameters**: Sets appropriate temperature, max_tokens, and top_p based on content type
- **Content Type Validation**: Ensures only supported content types are processed

## Prompt Engineering

### Zero-Shot Prompting

Default mode with structured prompts and clear instructions. Suitable for most use cases.

### Few-Shot Prompting

Optional mode with example demonstrations. Enable by setting `use_few_shot: true` in generation parameters.

### Prompt Injection Defense

- User inputs are wrapped in `<user_input>` tags
- System prompts explicitly instruct the model to ignore commands outside these tags
- Prevents prompt injection attacks

## Post-Processing

Generated content undergoes comprehensive post-processing:

1. **Structure Parsing**: Extracts titles, headers, and sections
2. **Word Count Validation**: Validates word count is within ±10% tolerance
3. **AI Artifact Removal**: Removes common boilerplate phrases (e.g. “As an AI assistant”)
4. **Formatting Standardization**: Fixes spacing, headers, and markdown issues
5. **Section Validation**: Checks structure hints (e.g. blog sections); does not discard valid model output for missing punctuation

## Testing

### Backend Tests

Run backend tests:
```bash
cd backend
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Tests

Run frontend linting:
```bash
cd frontend
npm run lint
```

### Integration Tests

Run full stack with Docker Compose:
```bash
docker-compose up --build
# Test endpoints manually or with curl/Postman
```

## CI/CD Pipeline

The project includes a GitHub Actions CI/CD pipeline that:

1. **Backend Tests**: Runs linting (black, isort, flake8), pip-audit, and pytest
2. **Frontend Tests**: Runs npm audit, ESLint, and builds the frontend
3. **Docker Build**: Builds both backend and frontend Docker images
4. **Docker Compose Validation**: Validates docker-compose.yml configuration

The pipeline runs on:
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop` branches

## Deployment

### Docker Deployment (Recommended)

Single command deployment:
```bash
docker-compose up -d --build
```

### Production Considerations

1. **Environment Variables**: Use secret managers (AWS/GCP) instead of `.env` files
2. **Rate Limiting**: Adjust `RATE_LIMIT_MAX_REQUESTS` based on expected traffic
3. **Quota Management**: Set `QUOTA_MAX_TOKENS_PER_DAY` based on API budget
4. **CORS**: Set `GHOSTWRITER_ENV=production` and `CORS_ORIGINS` to a comma-separated list of real HTTPS origins (the API refuses to start in production if `CORS_ORIGINS` is missing or wildcard-only)
5. **Client API Key (optional)**: Set `GHOSTWRITER_CLIENT_API_KEY` on the backend to require `Authorization: Bearer`, `X-API-Key`, or (for SSE only) `api_key` query. For the SPA, `VITE_CLIENT_API_KEY` sends the same value (it is **not secret** in the browser). For real protection, put the API behind an authenticated gateway, private network, or BFF instead of relying on a Vite env var
6. **HTTPS**: Use reverse proxy (Nginx/Traefik) with SSL certificates (required if you pass client keys in query strings for SSE)
7. **Monitoring**: Set up monitoring for logs, metrics, and error tracking; use the [OpenRouter dashboard](https://openrouter.ai) for usage, quota, and billing alerts
8. **Caching**: Consider Redis for distributed caching in production
9. **Database**: Add database for persistent quota tracking and analytics

## Performance

- **Generation Time**: Sub-60-second generation times for typical content requests
- **Streaming**: Real-time content streaming provides perceived latency < 1s
- **Caching**: Identical requests are cached for 1 hour to reduce API costs
- **Rate Limiting**: Prevents abuse and ensures fair resource usage

## Security

- **Prompt Injection Defense**: Inputs wrapped in delimiters; post-processing strips common artifacts. Do not log full prompts in shared environments; at `LOG_LEVEL=DEBUG`, only prompt *lengths* are logged (see `log_prompt_sizes_debug` in the backend)
- **Input Validation**: Comprehensive validation prevents malformed requests
- **Rate Limiting**: Per-IP rate limiting reduces abuse
- **Quota Management**: Daily token and request quotas limit OpenRouter cost per IP (in-memory; use a database for multi-instance deployments)
- **Optional Client API Key**: When `GHOSTWRITER_CLIENT_API_KEY` is set, `/generate`, `/generate/stream`, `/export/pdf`, and `/metrics` require the key (`/health` stays unauthenticated for load balancers)
- **Errors**: OpenRouter failures return generic messages to clients; full provider text is logged server-side only
- **CORS**: With `GHOSTWRITER_ENV=production`, missing or unsafe `CORS_ORIGINS` fails startup. In development, unset `CORS_ORIGINS` defaults to explicit localhost origins (not `*`) so credentialed dev requests work
- **Supply Chain**: CI runs `pip-audit` and `npm audit`; keep `requirements.txt` and `package-lock.json` updated

## Troubleshooting

### Local development (`make dev`)

- **`Missing backend/.env` when running `make dev` or `make dev-backend`:** run `make configure` from the repo root, or copy `backend/.env.example` to `backend/.env` and set `OPENROUTER_*` manually.
- **`make configure` exits with “No TTY”:** run it in a normal terminal (not piped/background). In CI, do not rely on `make configure`; provide `.env` or env vars via your provider’s secrets.
- **`npm run build` succeeded but nothing is on port 3000:** `build` only writes `frontend/dist/`. For local UI use `make dev` or `cd frontend && npm run dev`. To test a production bundle locally: `npm run build && npm run preview` (Vite preview still proxies `/api` to `:8000` per `vite.config.ts`).
- **Ports in use:** backend defaults to **8000**, frontend to **3000**. Stop other processes on those ports or adjust the Makefile / Vite port if your project allows it.

### Backend won't start

- **`ModuleNotFoundError: No module named 'app'`**: Run uvicorn from the **`backend/`** directory so the `app` package is on the path, e.g. `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`, or use `make dev-backend` / `./railway-entry.sh` from the repo root (both `cd` into `backend` first). Alternatively: `cd backend && python -m uvicorn app.main:app ...`
- Check that `OPENROUTER_API_KEY` is set (e.g. in `backend/.env` after `make configure`, or exported in the shell)
- If `GHOSTWRITER_ENV=production`, set `CORS_ORIGINS` to explicit origins (not empty, not `*`-only)
- Verify Python 3.11+ is installed (use `python3 --version`)
- On macOS, use `python3` instead of `python`
- Use `pip3` if `pip` is not available
- Check port 8000 is not in use

### Frontend won't connect to backend

- Verify the backend is running on http://localhost:8000 (`curl http://localhost:8000/health`).
- **Default dev setup:** leave `VITE_API_BASE_URL` unset so the app calls same-origin `/api`; Vite proxies `/api` to `http://localhost:8000`. Only set `VITE_API_BASE_URL` if you intentionally call the API cross-origin (and ensure backend CORS allows your origin).
- If you set **`GHOSTWRITER_CLIENT_API_KEY`** on the backend, set matching **`VITE_CLIENT_API_KEY`** in `frontend/.env` or generation requests can return **401**.
- Check CORS settings in the backend if you use a custom frontend origin or direct API URL

### Docker build fails

- Ensure Docker and Docker Compose are installed
- Check Docker daemon is running
- Review Docker build logs for specific errors

### AI generation fails

- Verify `OPENROUTER_API_KEY` is valid
- Check API quota/billing status
- Review backend logs for detailed error messages

## Contributing

1. Fork or clone [the repository](https://gitea.kood.tech/ravikantpandit/ghostwriter)
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a pull request on Gitea

## License

See [LICENSE](LICENSE) file for details.

## Support

- **Repository:** [https://gitea.kood.tech/ravikantpandit/ghostwriter](https://gitea.kood.tech/ravikantpandit/ghostwriter)
- **Issues & contributions:** use the Gitea project issue tracker on the repository above.
- **API keys (OpenRouter):** for provisioning, rotation, team access, or configuration questions — **contact the maintainer** (same channel you use for this repo).
