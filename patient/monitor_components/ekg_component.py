def create_ekg_component():
    """Create an EKG chart component with real-time heartbeat visualization."""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Real-time EKG Chart</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 10px;
                background-color: #1e1e1e;
                color: #ffffff;
            }
            
            .chart-container {
                position: relative;
                width: 100%;
                height: 300px;
                background-color: #2d2d2d;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .status-bar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                background-color: #333;
                border-radius: 8px 8px 0 0;
                border-bottom: 1px solid #555;
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #ff0000;
            }
            
            .status-dot.connected {
                background-color: #00ff00;
            }
            
            .heart-rate {
                font-size: 18px;
                font-weight: bold;
                color: #00ff00;
            }
            
            .chart-area {
                position: relative;
                width: 100%;
                height: 250px;
            }
            
            .grid-line {
                stroke: #444;
                stroke-width: 1;
                opacity: 0.5;
            }
            
            .ekg-line {
                stroke: #00ff00;
                stroke-width: 2;
                fill: none;
            }
            
            .time-marker {
                stroke: #ffffff;
                stroke-width: 1;
                opacity: 0.3;
            }
            
            .time-marker-text {
                fill: #ffffff;
                font-size: 10px;
                opacity: 0.7;
            }
            
            .axis text {
                fill: #ffffff;
                font-size: 10px;
            }
            
            .axis path,
            .axis line {
                stroke: #555;
            }
        </style>
    </head>
    <body>
        <div class="chart-container">
            <div class="status-bar">
                <div class="status-indicator">
                    <div id="status" class="status-dot"></div>
                    <span id="statusText">Connecting...</span>
                </div>
                <div class="heart-rate">
                    <span id="heartRate">-- BPM</span>
                </div>
            </div>
            <div class="chart-area">
                <svg id="ekgChart" width="100%" height="100%"></svg>
            </div>
        </div>
        
        <script>
            // Configuration
            const config = {
                width: 800,
                height: 250,
                timeWindow: 30000,  // 30 seconds
                updateInterval: 16,  // ~60 FPS
                gridSpacing: 50
            };
            
            // State variables
            let websocket;
            let isConnected = false;
            let scenarioRunning = false;
            let heartbeatData = [];
            let heartbeatTimes = [];
            let lastHeartbeatTime = 0;
            let heartRate = 0;
            let animationId;
            
            // D3 elements
            let svg, chartGroup, xScale, yScale, lineGenerator;
            let containerWidth, containerHeight;
            
            // Initialize the chart
            function initChart() {
                const container = document.querySelector('.chart-container');
                containerWidth = container.clientWidth;
                containerHeight = container.clientHeight - 50; // Account for status bar
                
                // Clear existing chart
                d3.select('#ekgChart').selectAll('*').remove();
                
                // Create SVG
                svg = d3.select('#ekgChart')
                    .attr('width', containerWidth)
                    .attr('height', containerHeight);
                
                // Create chart group
                chartGroup = svg.append('g')
                    .attr('class', 'chart-group');
                
                // Create scales
                const now = Date.now();
                xScale = d3.scaleTime()
                    .domain([now - config.timeWindow, now])
                    .range([0, containerWidth - 40]);
                
                yScale = d3.scaleLinear()
                    .domain([0, 100])
                    .range([containerHeight - 40, 20]);
                
                // Create line generator
                lineGenerator = d3.line()
                    .x(d => xScale(d.timestamp))
                    .y(d => yScale(d.value))
                    .curve(d3.curveMonotoneX);
                
                // Add grid lines
                const gridGroup = chartGroup.append('g').attr('class', 'grid');
                
                // Vertical grid lines (time)
                for (let i = 0; i <= containerWidth; i += config.gridSpacing) {
                    gridGroup.append('line')
                        .attr('class', 'grid-line')
                        .attr('x1', i)
                        .attr('y1', 0)
                        .attr('x2', i)
                        .attr('y2', containerHeight);
                }
                
                // Horizontal grid lines (amplitude)
                for (let i = 0; i <= containerHeight; i += config.gridSpacing) {
                    gridGroup.append('line')
                        .attr('class', 'grid-line')
                        .attr('x1', 0)
                        .attr('y1', i)
                        .attr('x2', containerWidth)
                        .attr('y2', i);
                }
                
                // Add axes
                const yAxis = d3.axisLeft(yScale)
                    .ticks(5);
                
                chartGroup.append('g')
                    .attr('class', 'axis')
                    .attr('transform', 'translate(20, 0)')
                    .call(yAxis);
            }
            
            // Update the chart with new data
            function updateChart() {
                if (!scenarioRunning) return;
                
                const now = Date.now();
                
                // Update x-scale domain to show rolling window
                xScale.domain([now - config.timeWindow, now]);
                
                // Remove old data points
                const cutoffTime = now - config.timeWindow;
                heartbeatData = heartbeatData.filter(d => d.timestamp >= cutoffTime);
                
                // Update the line
                chartGroup.selectAll('.ekg-line').remove();
                
                if (heartbeatData.length > 1) {
                    chartGroup.append('path')
                        .attr('class', 'ekg-line')
                        .attr('d', lineGenerator(heartbeatData));
                }
                
                // Update time markers only when simulation is running
                updateTimeMarkers(now);
                
                // Update axes - properly clear and recreate
                chartGroup.selectAll('.axis').remove();
                
                const yAxis = d3.axisLeft(yScale)
                    .ticks(5);
                
                chartGroup.append('g')
                    .attr('class', 'axis')
                    .attr('transform', 'translate(20, 0)')
                    .call(yAxis);
            }
            
            // Update time markers
            function updateTimeMarkers(currentTime) {
                const timeMarkersGroup = chartGroup.select('.time-markers');
                
                // Only update time markers if simulation is running
                if (!scenarioRunning) {
                    // Show "No Simulation" message when not running
                    timeMarkersGroup.selectAll('*').remove();
                    timeMarkersGroup.append('text')
                        .attr('class', 'time-marker-text')
                        .attr('x', containerWidth / 2)
                        .attr('y', containerHeight / 2)
                        .attr('text-anchor', 'middle')
                        .style('font-size', '16px')
                        .style('fill', '#666')
                        .text('No Simulation Running');
                    return;
                }
                
                // Clear existing markers and recreate them for animation
                timeMarkersGroup.selectAll('*').remove();
                
                // Get the time range from the current x-scale domain
                const domain = xScale.domain();
                const startTime = domain[0].getTime();
                const endTime = domain[1].getTime();
                
                // Add time markers every 5 seconds within the visible time range
                const firstMarker = Math.ceil(startTime / 5000) * 5000; // Round up to next 5-second mark
                
                for (let markerTime = firstMarker; markerTime <= endTime; markerTime += 5000) {
                    const x = xScale(new Date(markerTime));
                    
                    // Only add markers if they're within the visible area
                    if (x >= 20 && x <= containerWidth - 20) {
                        timeMarkersGroup.append('line')
                            .attr('class', 'time-marker')
                            .attr('x1', x)
                            .attr('y1', 0)
                            .attr('x2', x)
                            .attr('y2', containerHeight - 20);
                        
                        const date = new Date(markerTime);
                        const hours = date.getHours().toString().padStart(2, '0');
                        const minutes = date.getMinutes().toString().padStart(2, '0');
                        const seconds = date.getSeconds().toString().padStart(2, '0');
                        const timeString = `${hours}:${minutes}:${seconds}`;
                        
                        timeMarkersGroup.append('text')
                            .attr('class', 'time-marker-text')
                            .attr('x', x)
                            .attr('y', containerHeight - 5)
                            .text(timeString);
                    }
                }
            }
            
            // Add a heartbeat event to the data
            function addHeartbeat(serverTimestamp) {
                // Only process heartbeats if scenario is running
                if (!scenarioRunning) {
                    return;
                }
                
                const now = Date.now();
                
                // Use server timestamp if provided, otherwise use client time
                const heartbeatTime = serverTimestamp || now;
                
                // Store heartbeat time for BPM calculation
                heartbeatTimes.push(heartbeatTime);
                
                // Keep only heartbeats from the last 60 seconds for BPM calculation
                const cutoffTime = heartbeatTime - 60000;
                heartbeatTimes = heartbeatTimes.filter(time => time >= cutoffTime);
                
                // Calculate heart rate based on recent heartbeats
                if (heartbeatTimes.length >= 2) {
                    const intervals = [];
                    for (let i = 1; i < heartbeatTimes.length; i++) {
                        intervals.push(heartbeatTimes[i] - heartbeatTimes[i-1]);
                    }
                    const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
                    heartRate = Math.round(60000 / avgInterval);
                    
                    document.getElementById('heartRate').textContent = heartRate + ' BPM';
                }
                
                lastHeartbeatTime = now;
                
                // Create EKG waveform data points
                const baseline = 50;
                const amplitude = 30;
                const duration = 200;  // Shorter duration for more compact beats
                
                // Generate EKG-like waveform
                const waveform = generateEKGWaveform(baseline, amplitude, duration);
                
                // Add waveform to data using server timestamp for accurate positioning
                waveform.forEach((value, index) => {
                    heartbeatData.push({
                        value: value,
                        timestamp: heartbeatTime + index * 1  // Use server timestamp + 1ms intervals for smoother waveform
                    });
                });
                
                // Remove old data points (older than 30 seconds)
                const cutoffTimestamp = heartbeatTime - config.timeWindow;
                heartbeatData = heartbeatData.filter(d => d.timestamp >= cutoffTimestamp);
            }
            
            // Generate EKG-like waveform
            function generateEKGWaveform(baseline, amplitude, duration) {
                const points = [];
                const steps = duration;  // 1ms intervals
                
                for (let i = 0; i < steps; i++) {
                    let value = baseline;
                    
                    // P wave (small bump)
                    if (i >= 10 && i < 25) {
                        value = baseline + amplitude * 0.25 * Math.sin((i - 10) * Math.PI / 15);
                    }
                    // QRS complex (sharp spike)
                    else if (i >= 35 && i < 55) {
                        if (i < 40) {
                            value = baseline - amplitude * 0.15;  // Q wave
                        } else if (i < 45) {
                            value = baseline + amplitude;  // R wave
                        } else {
                            value = baseline - amplitude * 0.25;  // S wave
                        }
                    }
                    // T wave (rounded bump)
                    else if (i >= 70 && i < 100) {
                        value = baseline + amplitude * 0.35 * Math.sin((i - 70) * Math.PI / 30);
                    }
                    
                    points.push(value);
                }
                
                return points;
            }
            
            // Start scenario
            function startScenario() {
                scenarioRunning = true;
                document.getElementById('statusText').textContent = 'Simulation Running';
                document.getElementById('status').classList.add('connected');
                chartGroup.append('g').attr('class', 'time-markers');
                startAnimation();
                // Clear previous data when starting new simulation
                heartbeatData = [];
                heartbeatTimes = [];
                heartRate = 0;
                document.getElementById('heartRate').textContent = '-- BPM';
            }
            
            // Stop scenario
            function stopScenario() {
                scenarioRunning = false;
                document.getElementById('statusText').textContent = 'No Simulation';
                document.getElementById('status').classList.remove('connected');
                document.getElementById('heartRate').textContent = '-- BPM';
                stopAnimation();
            }
            
            // Start animation loop
            function startAnimation() {
                if (animationId) return;
                
                function animate() {
                    updateChart();
                    animationId = requestAnimationFrame(animate);
                }
                animate();
            }
            
            // Stop animation loop
            function stopAnimation() {
                if (animationId) {
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }
            }
            
            // Connect to WebSocket
            function connectWebSocket() {
                const wsUrl = 'ws://localhost:8092';
                
                websocket = new WebSocket(wsUrl);
                
                websocket.onopen = function(event) {
                    isConnected = true;
                    document.getElementById('status').classList.add('connected');
                    document.getElementById('statusText').textContent = 'Connected';
                };
                
                websocket.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        
                        if (data.event_type === 'scenario_started') {
                            startScenario();
                        } else if (data.event_type === 'heartbeat') {
                            addHeartbeat(data.timestamp);
                        } else if (data.event_type === 'scenario_stopped' || data.event_type === 'scenario_complete') {
                            stopScenario();
                        }
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };
                
                websocket.onclose = function(event) {
                    isConnected = false;
                    document.getElementById('status').classList.remove('connected');
                    document.getElementById('statusText').textContent = 'Disconnected';
                    
                    // Try to reconnect after 3 seconds
                    setTimeout(connectWebSocket, 3000);
                };
                
                websocket.onerror = function(error) {
                    document.getElementById('statusText').textContent = 'Connection Error';
                    document.getElementById('status').classList.remove('connected');
                };
            }
            
            // Initialize everything
            function init() {
                initChart();
                connectWebSocket();
                
                // Handle window resize
                window.addEventListener('resize', function() {
                    stopAnimation();
                    setTimeout(() => {
                        initChart();
                        if (scenarioRunning) {
                            startAnimation();
                        }
                    }, 100);
                });
            }
            
            // Start when page loads
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', init);
            } else {
                init();
            }
        </script>
    </body>
    </html>
    """
    
    return html_content 