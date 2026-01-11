# Procfile for Railway/Heroku deployment
# Railway will use nixpacks.toml or Dockerfile, but this can be used as fallback

web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
