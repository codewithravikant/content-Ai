# Content AI - AI Content Generation Platform

A powerful content generation platform that uses AI to create ready-to-use content for blogs, emails, stories, and social media posts. Built with React (Vite) frontend and FastAPI backend, featuring streaming responses, comprehensive validation, and multiple export formats.

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
│   React     │────────▶│   FastAPI   │────────▶│   OpenAI    │
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

- Docker and Docker Compose (recommended - avoids Python version issues!)
- OR Node.js 18+ and Python 3.11 or 3.12 (Python 3.13 not fully supported yet)
- **AI Provider**: Either:
  - OpenAI API key, OR
  - Falcon AI API accessible via Cloudflare tunnel (see [CLOUDFLARE_TUNNEL_SETUP.md](./CLOUDFLARE_TUNNEL_SETUP.md))

## Quick Start (Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/codewithravikant/content-Ai.git
   cd Content-AI
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
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

Content AI is ready to deploy on Railway! See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) for detailed instructions.

**Quick Railway Deployment:**

1. Push your code to GitHub
2. Create a new Railway project
3. Deploy backend service:
   - Root directory: `backend`
   - Set `OPENAI_API_KEY` environment variable
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
   # IMPORTANT: Get your OpenAI API key from https://platform.openai.com/account/api-keys
   # OpenAI API keys start with "sk-" or "sk-proj-"
   # Do NOT use Google API keys (which start with "AIza")
   export OPENAI_API_KEY=sk-your_openai_api_key_here
   export OPENAI_MODEL=gpt-3.5-turbo  # Optional
   ```
   
   **Important Notes:**
   - OpenAI API keys always start with `sk-` or `sk-proj-`
   - If you see an error about "AIza" in your key, you're using a Google API key by mistake
   - Get your OpenAI API key from: https://platform.openai.com/account/api-keys
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

3. **Create .env file** (optional, defaults to http://localhost:8000)
   ```bash
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env
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

Create a `.env` file in the root directory:

```env
# AI Provider Configuration (choose one: "openai" or "falcon")
AI_PROVIDER=openai

# OpenAI API Configuration (when AI_PROVIDER=openai)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo
AI_TIMEOUT=60

# Falcon API Configuration (when AI_PROVIDER=falcon)
# Base URL of your Falcon API (e.g., Cloudflare tunnel URL)
FALCON_API_BASE_URL=https://your-falcon-tunnel-url.trycloudflare.com
# Optional: API key if Falcon requires authentication
FALCON_API_KEY=your_falcon_api_key_if_needed
# Optional: Timeout for Falcon API requests (default: 120 seconds)
FALCON_TIMEOUT=120

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=10
RATE_LIMIT_WINDOW_SECONDS=60

# Quota Management
QUOTA_MAX_TOKENS_PER_DAY=50000
QUOTA_MAX_REQUESTS_PER_DAY=100

# Frontend API URL (optional)
VITE_API_BASE_URL=http://localhost:8000

# CORS Configuration
CORS_ORIGINS=*
```

### Using Falcon API (Self-Hosted)

Content AI supports using Falcon AI API as an alternative to OpenAI. This is useful when:
- You want to use a self-hosted AI model
- You want to avoid OpenAI API costs
- You have a local Falcon instance accessible via Cloudflare tunnel

**Setup Steps:**

1. **Set up Cloudflare Tunnel** (see [CLOUDFLARE_TUNNEL_SETUP.md](./CLOUDFLARE_TUNNEL_SETUP.md))
   - Create a tunnel pointing to your local Falcon API
   - Get the tunnel URL (e.g., `https://your-tunnel-url.trycloudflare.com`)

2. **Configure Environment Variables:**
   ```env
   AI_PROVIDER=falcon
   FALCON_API_BASE_URL=https://your-tunnel-url.trycloudflare.com
   ```

3. **Start the application** - It will automatically use Falcon instead of OpenAI

**For Railway Deployment:**
- Set `AI_PROVIDER=falcon` as an environment variable
- Set `FALCON_API_BASE_URL` to your Cloudflare tunnel URL
- Keep secrets marked as "Secret" in Railway dashboard

### Secret Management

For production deployments, use a secret manager:
- **AWS Secrets Manager**: Store `OPENAI_API_KEY` and retrieve at runtime
- **GCP Secret Manager**: Similar approach for GCP deployments
- **Docker Secrets**: Use Docker secrets for containerized deployments
- **Kubernetes Secrets**: Use K8s secrets for orchestrated deployments

Example with AWS Secrets Manager (Python):
```python
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='content-ai/openai-key')
api_key = secret['SecretString']
```

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
  "service": "content-ai"
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

**Required Fields:**
- `topic`: Blog post topic (3-200 characters)
- `target_audience`: Target audience (3-100 characters)
- `word_count`: Word count range (e.g., "100-300") - **Minimum: 50 words**
- `tone`: Tone (professional, casual, friendly, formal, engaging, persuasive)

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
- `platform`: Platform name (Twitter/X, Instagram, LinkedIn, Facebook) (2-50 characters)
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
3. **AI Artifact Removal**: Removes phrases like "As an AI assistant"
4. **Formatting Standardization**: Fixes spacing, headers, and markdown issues
5. **Section Validation**: Ensures required sections are present

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

- Check that `OPENAI_API_KEY` is set
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

- Verify `OPENAI_API_KEY` is valid
- Check API quota/billing status
- Review backend logs for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

See [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.
