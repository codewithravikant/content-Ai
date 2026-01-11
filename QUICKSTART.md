# Quick Start Guide

## One-Command Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd ghostwriter

# 2. Create .env file
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Run everything (single command!)
docker-compose up --build
```

That's it! The platform will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Testing the Platform

### 1. Generate a Blog Post

1. Open http://localhost:3000
2. Click "📝 Blog Post"
3. Fill in the form:
   - Topic: "Introduction to Machine Learning"
   - Target Audience: "General public"
   - Word Count: "800-1000"
   - Tone: "Engaging"
   - Check "SEO Focus"
4. Click "Generate Blog Post"
5. Edit the generated content
6. Export as PDF, Markdown, or HTML

### 2. Generate an Email

1. Click "✉️ Email"
2. Fill in the form:
   - Purpose: "Follow-up on meeting"
   - Recipient Context: "Client we met last week"
   - Key Points: "Thank them for their time, summarize next steps, request feedback"
   - Tone: "Professional"
   - Urgency: "Medium"
3. Click "Generate Email"
4. Edit and export

## Development

### Backend Development

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt  # Use pip3 if pip is not available
export OPENAI_API_KEY=your_key_here
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend linting
cd frontend
npm run lint

# Generate TypeScript types from OpenAPI
npm run generate-types
```

## Environment Variables

Required:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `OPENAI_MODEL`: Model to use (default: gpt-3.5-turbo)
- `RATE_LIMIT_MAX_REQUESTS`: Max requests per window (default: 10)
- `QUOTA_MAX_TOKENS_PER_DAY`: Daily token limit (default: 50000)

See `.env.example` for all options.

## Troubleshooting

**Docker build fails?**
- Check Docker daemon is running
- Verify Docker Compose is installed
- Review build logs for specific errors

**Backend won't start?**
- Verify `OPENAI_API_KEY` is set in `.env`
- Check port 8000 is not in use
- Review backend logs

**Frontend won't connect?**
- Ensure backend is running
- Check `VITE_API_BASE_URL` in frontend `.env`
- Verify CORS settings

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [LICENSE](LICENSE) for usage terms
- Review API documentation at http://localhost:8000/docs
