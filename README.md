# Ghostwriter - AI Content Generation Platform

A powerful content generation platform that uses AI to create ready-to-use content for blogs, emails, stories, and social media posts. Built with React (Vite) frontend and FastAPI backend, featuring streaming responses, comprehensive validation, and multiple export formats.

**Repository:** [https://gitea.kood.tech/ravikantpandit/ghostwriter](https://gitea.kood.tech/ravikantpandit/ghostwriter)

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
#optional

Ghostwriter is ready to deploy on Railway! See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for detailed instructions.

**Quick Railway Deployment:**

1. Push your code to your Git remote (e.g. [Gitea](https://gitea.kood.tech/ravikantpandit/ghostwriter))
2. Create a new Railway project
3. Deploy backend service:
   - Root directory: `backend`
   - Set `OPENROUTER_API_KEY` environment variable
4. Deploy frontend service:
   - Root directory: `frontend`
   - Set `VITE_API_BASE_URL` to your backend Railway URL
5. Update backend `CORS_ORIGINS` with frontend URL

For complete Railway deployment guide, see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md).

## Manual Setup

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
   ```bash
   # Get your OpenRouter API key from https://openrouter.ai/keys
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

Create a `.env` file in the root directory (or use `.env.example` as a template):

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
```

### OpenRouter Setup

1. Create an account and API key at [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Set `OPENROUTER_API_KEY=your_key_here`
3. Set `OPENROUTER_MODEL` to one supported model, for example:
   - `openai/gpt-3.5-turbo`
   - `google/gemini-flash-1.5`
   - `anthropic/claude-3-haiku`
   - `meta-llama/llama-3-8b-instruct`
   - `qwen/qwen3.6-plus:free` (example free tier; IDs are always `provider/model`, not `openai/qwen/...`)
4. Optionally set `APP_URL` so OpenRouter usage analytics can attribute requests to your app

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
    "word_target": 900,
    "seo_enabled": true,
    "expertise": "beginner"
  },
  "generation_params": {
    "temperature": 0.7,
    "max_tokens": 2000,
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
  "generation_params": { "temperature": 0.7, "max_tokens": 2000, "top_p": 0.9 }
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
- `word_target`: Target length as a **number** (min 50) — the form may collect a range string and normalize it before calling the API

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
- `word_count`: Word count range - **Minimum: 50 words** (default: "50-300")

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

- **Word Count**: Converts ranges like "50-300" to target integer (175) - **Minimum enforced: 50 words**
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

1. **Backend Tests**: Runs linting (black, isort, flake8) and pytest
2. **Frontend Tests**: Runs ESLint and builds the frontend
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
4. **CORS**: Restrict `allow_origins` in FastAPI CORS middleware to your frontend domain
5. **HTTPS**: Use reverse proxy (Nginx/Traefik) with SSL certificates
6. **Monitoring**: Set up monitoring for logs, metrics, and error tracking
7. **Caching**: Consider Redis for distributed caching in production
8. **Database**: Add database for persistent quota tracking and analytics

## Performance

- **Generation Time**: Sub-60-second generation times for typical content requests
- **Streaming**: Real-time content streaming provides perceived latency < 1s
- **Caching**: Identical requests are cached for 1 hour to reduce API costs
- **Rate Limiting**: Prevents abuse and ensures fair resource usage

## Security

- **Prompt Injection Defense**: Inputs wrapped in delimiters, model instructed to ignore commands
- **Input Validation**: Comprehensive validation prevents malicious inputs
- **Rate Limiting**: Per-IP rate limiting prevents abuse
- **Quota Management**: Daily token and request quotas prevent cost overruns
- **Error Handling**: User-friendly error messages prevent information leakage

## Troubleshooting

### Backend won't start

- Check that `OPENROUTER_API_KEY` is set
- Verify Python 3.11+ is installed (use `python3 --version`)
- On macOS, use `python3` instead of `python`
- Use `pip3` if `pip` is not available
- Check port 8000 is not in use

### Frontend won't connect to backend

- Verify backend is running on http://localhost:8000
- Check `VITE_API_BASE_URL` in frontend `.env` file
- Check CORS settings in backend

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
