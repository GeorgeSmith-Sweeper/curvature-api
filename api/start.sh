#!/bin/bash
# Quick start script for the Curvature API server

echo "🚀 Starting Curvature API Server..."
echo ""
echo "Server will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Web Interface: http://localhost:8000/static/index.html"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Run the server
python server.py
