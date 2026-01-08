#!/bin/bash

echo "================================"
echo "Bird Tracker - One-Click Startup"
echo "================================"
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[1/8] Python found"
python3 --version

# Check Node/npm installation
if ! command -v npm &> /dev/null; then
    echo "ERROR: npm is not installed or not in PATH"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "[2/8] npm found"
npm --version

# Install Python requirements
echo ""
echo "[3/8] Installing Python requirements..."
cd "$SCRIPT_DIR/scripts"
python3 -m pip install -r requirements.txt --quiet --disable-pip-version-check
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install Python requirements"
    exit 1
fi
echo "Python requirements installed"

# Check for OpenAI API key
echo ""
echo "[4/8] Checking OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable is not set"
    echo "The bird analysis feature will not work without it"
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " user_key
    if [ ! -z "$user_key" ]; then
        export OPENAI_API_KEY="$user_key"
        echo "API key set for this session"
    else
        echo "Continuing without API key - only YOLO detection will work"
    fi
else
    echo "OpenAI API key found"
fi

# Install npm dependencies if needed
cd "$SCRIPT_DIR"
if [ ! -d "node_modules" ]; then
    echo ""
    echo "[5/8] Installing npm dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install npm dependencies"
        exit 1
    fi
else
    echo "[5/8] npm dependencies already installed"
fi

# Create initial metrics.json if it doesn't exist
echo ""
echo "[6/8] Initializing metrics file..."
mkdir -p public
if [ ! -f "public/metrics.json" ]; then
    echo '{"total_visits":0,"visits":[],"species_counts":{}}' > public/metrics.json
    echo "Created initial metrics.json"
else
    echo "metrics.json already exists"
fi

# Build the dashboard
echo ""
echo "[7/8] Building dashboard..."
npm run build
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build dashboard"
    exit 1
fi
echo "Dashboard built successfully"

# Start the Python scripts in background
echo ""
echo "[8/8] Starting bird detection scripts..."
cd "$SCRIPT_DIR/scripts"

# Start bird counter
python3 pilot_bird_counter_fixed.py > "$SCRIPT_DIR/bird_counter.log" 2>&1 &
COUNTER_PID=$!
sleep 2

# Start analyzer (in watch mode)
python3 pilot_analyze_captures_fixed.py --watch > "$SCRIPT_DIR/bird_analyzer.log" 2>&1 &
ANALYZER_PID=$!
sleep 2

echo "Bird detection scripts started in background"
echo "  Bird Counter PID: $COUNTER_PID"
echo "  Bird Analyzer PID: $ANALYZER_PID"

# Start web server for dashboard
echo ""
echo "================================"
echo "STARTUP COMPLETE!"
echo "================================"
echo ""
echo "Bird Counter: Running (PID: $COUNTER_PID)"
echo "Bird Analyzer: Running (PID: $ANALYZER_PID)"
echo "Dashboard: http://localhost:8080"
echo ""
echo "The dashboard will open in your browser in 3 seconds..."
echo ""
echo "To stop everything:"
echo "  kill $COUNTER_PID $ANALYZER_PID"
echo "  or press Ctrl+C"
echo ""
echo "Logs:"
echo "  Bird Counter: $SCRIPT_DIR/bird_counter.log"
echo "  Bird Analyzer: $SCRIPT_DIR/bird_analyzer.log"
echo "================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all processes..."
    kill $COUNTER_PID $ANALYZER_PID 2>/dev/null
    echo "Stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait a moment then open browser
sleep 3

# Try to open browser (works on most systems)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080 &> /dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:8080 &> /dev/null &
fi

# Start Python HTTP server
cd "$SCRIPT_DIR/public"
python3 -m http.server 8080
