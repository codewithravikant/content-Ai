#!/bin/bash

# Generate frontend TypeScript types from FastAPI OpenAPI spec
# This keeps frontend types in sync with backend schemas

set -e

echo "Generating TypeScript types from FastAPI OpenAPI spec..."

# Ensure backend is running or use a local OpenAPI spec
BACKEND_URL=${BACKEND_URL:-http://localhost:8000}
OPENAPI_JSON=${OPENAPI_JSON:-./openapi.json}

# Download OpenAPI spec if backend is running
if curl -f "$BACKEND_URL/openapi.json" > "$OPENAPI_JSON" 2>/dev/null; then
    echo "✓ Downloaded OpenAPI spec from $BACKEND_URL"
else
    echo "⚠ Backend not running. Using existing $OPENAPI_JSON if available."
    if [ ! -f "$OPENAPI_JSON" ]; then
        echo "✗ Error: Cannot find OpenAPI spec. Please ensure backend is running or provide $OPENAPI_JSON"
        exit 1
    fi
fi

# Install openapi-typescript-codegen if not already installed
if ! command -v openapi-typescript-codegen &> /dev/null; then
    echo "Installing openapi-typescript-codegen..."
    npm install -g openapi-typescript-codegen
fi

# Generate types
cd frontend
openapi-typescript-codegen \
    --input "../$OPENAPI_JSON" \
    --output "./src/api/generated" \
    --client "axios" \
    --useOptions \
    --name "GhostwriterApi"

echo "✓ TypeScript types generated in frontend/src/api/generated"
echo ""
echo "Note: You may need to update imports in your components to use the generated types."
echo "Example: import { GenerateRequest, GenerateResponse } from './api/generated'"
