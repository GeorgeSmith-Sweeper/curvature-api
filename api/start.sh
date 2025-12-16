#!/bin/bash
# Quick start script for the Curvature API server

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🚀 Starting Curvature API Server..."
echo ""

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv "$SCRIPT_DIR/venv"
    echo "📦 Installing dependencies..."
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# Check if config.py exists
if [ ! -f "$SCRIPT_DIR/config.py" ]; then
    echo "⚠️  Configuration file not found!"
    echo "Please copy config.example.py to config.py and add your API keys:"
    echo "  cp $SCRIPT_DIR/config.example.py $SCRIPT_DIR/config.py"
    exit 1
fi

# Set PYTHONPATH to include the curvature library
# Default to ../../curvature (sibling to curvature-api), otherwise use CURVATURE_PATH env var
CURVATURE_DIR="${CURVATURE_PATH:-$(dirname "$(dirname "$SCRIPT_DIR")")/curvature}"
if [ -d "$CURVATURE_DIR" ]; then
    export PYTHONPATH="$CURVATURE_DIR:$PYTHONPATH"
    echo "✓ Found curvature library at: $CURVATURE_DIR"
else
    echo "⚠️  Curvature library not found at: $CURVATURE_DIR"
    echo "Please set CURVATURE_PATH environment variable or install curvature:"
    echo "  export CURVATURE_PATH=/path/to/curvature"
    echo "  OR"
    echo "  git clone https://github.com/adamfranco/curvature.git"
    exit 1
fi

echo ""
echo "Server will be available at:"
echo "  - API: http://localhost:8000"
echo "  - Web Interface: http://localhost:8000/static/index.html"
echo "  - API Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Activate virtual environment and run the server
cd "$SCRIPT_DIR"
source "$SCRIPT_DIR/venv/bin/activate"
"$SCRIPT_DIR/venv/bin/python" "$SCRIPT_DIR/server.py"
