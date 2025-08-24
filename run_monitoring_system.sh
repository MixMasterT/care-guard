#!/bin/bash

# Patient Monitoring System Launcher
# This script starts the biometric scenario server and Streamlit monitoring app

echo "🏥 Starting Patient Monitoring System..."

# Check if we're in the right directory
if [ ! -f "patient/biometric_scenario_server.py" ]; then
    echo "❌ Error: biometric_scenario_server.py not found. Please run this script from the project root."
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

# Start biometric scenario server in background
echo "💓 Starting biometric scenario server..."
cd patient
python biometric_scenario_server.py &
BIOMETRIC_SERVER_PID=$!
cd ..

# Wait a moment for server to start
sleep 2

# Check if biometric server started successfully
if ! kill -0 $BIOMETRIC_SERVER_PID 2>/dev/null; then
    echo "❌ Error: Biometric scenario server failed to start"
    exit 1
fi

echo "✅ Biometric scenario server started (PID: $BIOMETRIC_SERVER_PID)"

# Check if agentic monitor is already running
if curl -s http://localhost:8502 > /dev/null 2>&1; then
    echo "✅ Agentic monitor already running on port 8502"
    AGENTIC_MONITOR_PID=""
else
    # Start agentic monitor in background
    echo "🤖 Starting agentic monitor app..."
    cd patient
    streamlit run agentic_monitor_app.py --server.port 8502 --server.headless true &
    AGENTIC_MONITOR_PID=$!
    cd ..
fi

# Wait a moment for agentic monitor to start (only if we started it)
if [ ! -z "$AGENTIC_MONITOR_PID" ]; then
    sleep 3
    
    # Check if agentic monitor started successfully
    if ! kill -0 $AGENTIC_MONITOR_PID 2>/dev/null; then
        echo "❌ Error: Agentic monitor failed to start"
        kill $BIOMETRIC_SERVER_PID
        exit 1
    fi
    
    echo "✅ Agentic monitor started (PID: $AGENTIC_MONITOR_PID)"
fi

# Start Streamlit app
echo "📊 Starting Streamlit monitoring app..."
cd patient
streamlit run monitor.py

# Cleanup: kill servers when Streamlit exits
echo "🛑 Shutting down servers..."
kill $BIOMETRIC_SERVER_PID
if [ ! -z "$AGENTIC_MONITOR_PID" ]; then
    kill $AGENTIC_MONITOR_PID
fi
echo "✅ Monitoring system stopped" 