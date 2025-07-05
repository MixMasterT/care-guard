#!/bin/bash

# Patient Monitoring System Launcher
# This script starts the pulse server and Streamlit monitoring app

echo "🏥 Starting Patient Monitoring System..."

# Check if we're in the right directory
if [ ! -f "patient/pulse-server.py" ]; then
    echo "❌ Error: pulse-server.py not found. Please run this script from the project root."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run 'uv sync' first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Start pulse server in background
echo "💓 Starting pulse server..."
cd patient
python pulse-server.py &
PULSE_SERVER_PID=$!
cd ..

# Wait a moment for server to start
sleep 2

# Check if pulse server started successfully
if ! kill -0 $PULSE_SERVER_PID 2>/dev/null; then
    echo "❌ Error: Pulse server failed to start"
    exit 1
fi

echo "✅ Pulse server started (PID: $PULSE_SERVER_PID)"

# Start Streamlit app
echo "📊 Starting Streamlit monitoring app..."
cd patient
streamlit run monitor.py

# Cleanup: kill pulse server when Streamlit exits
echo "🛑 Shutting down pulse server..."
kill $PULSE_SERVER_PID
echo "✅ Monitoring system stopped" 