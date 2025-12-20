#!/bin/bash
set -e

echo "🚀 Starting Peak Trade WebUI..."

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to docker directory
cd "$(dirname "$0")/../docker"

# Start Docker Compose
if docker compose version &> /dev/null; then
    docker compose -f docker-compose.webui.yml up -d
else
    docker-compose -f docker-compose.webui.yml up -d
fi

echo "✅ WebUI started!"
echo ""
echo "🌐 Access points:"
echo "  - Dashboard:   http://localhost:8501"
echo "  - API Docs:    http://localhost:8000/docs"
echo "  - API:         http://localhost:8000"
echo ""
echo "🔍 View logs:"
echo "  cd docker && docker-compose -f docker-compose.webui.yml logs -f"
echo ""
echo "🛑 Stop services:"
echo "  cd docker && docker-compose -f docker-compose.webui.yml down"
