#!/bin/bash
set -e

echo "🚀 Starting Peak Trade Monitoring Stack..."

# Navigate to docker directory
cd "$(dirname "$0")/../docker" || exit 1

# Start Docker Compose
docker-compose -f docker-compose.monitoring.yml up -d

echo ""
echo "✅ Monitoring stack started!"
echo ""
echo "📊 Access points:"
echo "  - Grafana:      http://localhost:3000 (admin/admin)"
echo "  - Prometheus:   http://localhost:9091"
echo "  - AlertManager: http://localhost:9093"
echo ""
echo "🔍 View logs:"
echo "  docker-compose -f docker/docker-compose.monitoring.yml logs -f"
echo ""
echo "🛑 Stop monitoring:"
echo "  docker-compose -f docker/docker-compose.monitoring.yml down"
