#!/bin/bash
# Debug script for web app connection issues

echo "🔍 Debugging Kali AI Orchestrator Web App..."
echo ""

# Check if container is running
echo "1. Container Status:"
if docker ps | grep -q kali-orchestrator; then
    echo "   ✅ Container is running"
    CONTAINER_ID=$(docker ps | grep kali-orchestrator | awk '{print $1}')
    echo "   Container ID: $CONTAINER_ID"
else
    echo "   ❌ Container is NOT running"
    echo "   Run: docker-compose up -d"
    exit 1
fi
echo ""

# Check container logs
echo "2. Recent Container Logs:"
docker logs --tail=30 kali-orchestrator
echo ""

# Check if port is exposed
echo "3. Port Mapping:"
docker port kali-orchestrator 2>/dev/null | grep 7860 || echo "   ⚠️  Port 7860 not mapped"
echo ""

# Check if process is listening inside container
echo "4. Processes in Container:"
docker exec kali-orchestrator ps aux | grep -E "(python|gradio)" || echo "   ⚠️  No Python/Gradio processes found"
echo ""

# Test connection from inside container
echo "5. Testing from Inside Container:"
docker exec kali-orchestrator curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:7860 2>&1 || echo "   ❌ Cannot connect from inside container"
echo ""

# Test connection from host
echo "6. Testing from Host:"
if curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:7860 2>&1; then
    echo "   ✅ Connection successful!"
else
    echo "   ❌ Connection failed"
    echo ""
    echo "💡 Troubleshooting:"
    echo "   - Check firewall: sudo ufw status"
    echo "   - Restart container: docker-compose restart orchestrator"
    echo "   - View full logs: docker-compose logs -f orchestrator"
fi
echo ""

# Check network
echo "7. Network Configuration:"
docker network inspect kali-ai-orchestrator_orchestrator-network 2>/dev/null | grep -A 5 "Containers" || echo "   ⚠️  Network not found"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Quick Fixes:"
echo "   1. Restart: docker-compose restart orchestrator"
echo "   2. Rebuild: docker-compose up -d --build"
echo "   3. Full logs: docker-compose logs -f orchestrator"
echo ""

