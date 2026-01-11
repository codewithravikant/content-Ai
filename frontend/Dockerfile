FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage - Use serve for Railway compatibility
FROM node:18-alpine

WORKDIR /app

# Install serve
RUN npm install -g serve

# Copy built files from build stage
COPY --from=build /app/dist ./dist

# Expose port (Railway will set PORT env var)
EXPOSE 3000

# Start serve - Railway will set PORT environment variable
# Use serve for Railway, or nginx for Docker Compose
CMD serve -s dist -l ${PORT:-3000}
