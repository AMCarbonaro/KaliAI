#!/bin/bash
# Quick status check script for Kali AI Orchestrator

echo "🔍 Checking Kali AI Orchestrator Status..."
echo ""

# Check if containers are running
echo "📦 Container Status:"
docker-compose ps
echo ""

# Check if port is listening
echo "🌐 Port Status:"
if netstat -tuln 2>/dev/null | grep -q ":7860"; then
    echo "✅ Port 7860 is listening"
else
    echo "❌ Port 7860 is NOT listening"
fi
echo ""

# Check container logs
echo "📋 Recent Logs (last 20 lines):"
docker-compose logs --tail=20 orchestrator
echo ""

# Test connection
echo "🔗 Testing Connection:"
if curl -s http://localhost:7860 > /dev/null 2>&1; then
    echo "✅ Web interface is responding"
else
    echo "❌ Web interface is NOT responding"
    echo ""
    echo "💡 Try these commands:"
    echo "   docker-compose logs -f orchestrator  # View full logs"
    echo "   docker-compose restart orchestrator  # Restart the service"
fi

