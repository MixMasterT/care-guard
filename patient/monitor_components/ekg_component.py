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
                height: 700px;
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
            
            .vital-signs {
                display: flex;
                gap: 20px;
                margin-top: 10px;
            }
            
            .vital-sign {
                display: flex;
                flex-direction: column;
                align-items: center;
                background-color: #333;
                padding: 8px 12px;
                border-radius: 6px;
                min-width: 80px;
            }
            
            .vital-label {
                font-size: 10px;
                color: #aaa;
                margin-bottom: 2px;
            }
            
            .vital-value {
                font-size: 14px;
                font-weight: bold;
                color: #00ff00;
            }
            
            .vital-value.warning {
                color: #ffaa00;
            }
            
            .vital-value.danger {
                color: #ff0000;
            }
            

            
            .respiration-bar-container {
                height: 20px;
                background-color: #1a1a1a;
                border-radius: 4px;
                margin: 10px 0;
                overflow: hidden;
                position: relative;
            }
            
            .respiration-label {
                font-size: 12px;
                color: #0099ff;
                margin-bottom: 5px;
                font-weight: bold;
            }
            
            .respiration-bar {
                height: 100%;
                background: linear-gradient(90deg, #0066cc, #0099ff);
                border-radius: 4px;
                transition: width 0.2s ease-in-out;
                min-width: 25%;
                max-width: 100%;
                width: 25%;
            }
            
            .chart-area {
                position: relative;
                width: 100%;
                height: 500px;
            }
            

            
            .ekg-line {
                stroke: #00ff00;
                stroke-width: 2;
                fill: none;
            }
            
            .time-marker {
                stroke: #999;
                stroke-width: 1;
                opacity: 0.8;
            }
            
            .time-marker-text {
                fill: #999;
                font-size: 11px;
                opacity: 0.9;
            }
            
            .rolling-grid-line {
                stroke: #999;
                stroke-width: 1;
                opacity: 0.4;
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
            <div class="vital-signs" id="vital-signs">
                <div class="vital-sign">
                    <div class="vital-label">Temp</div>
                    <div class="vital-value" id="temperature">--°F</div>
                </div>
                <div class="vital-sign">
                    <div class="vital-label">SpO2</div>
                    <div class="vital-value" id="spo2">--%</div>
                </div>
                <div class="vital-sign">
                    <div class="vital-label">BP</div>
                    <div class="vital-value" id="blood-pressure">--/--</div>
                </div>
                <div class="vital-sign">
                    <div class="vital-label">Pulse</div>
                    <div class="vital-value" id="pulse-strength">--</div>
                </div>
                <div class="vital-sign">
                    <div class="vital-label">ECG</div>
                    <div class="vital-value" id="ecg-rhythm">--</div>
                </div>
            </div>
            <div class="respiration-label">Respiration</div>
            <div class="respiration-bar-container">
                <div class="respiration-bar" id="respirationBar"></div>
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
                updateInterval: 16   // ~60 FPS
            };
            
            // State variables
            let websocket;
            let isConnected = false;
            let scenarioRunning = false;
            let heartbeatData = [];
            let heartbeatTimes = [];
            let respirationTimes = [];
            let lastHeartbeatTime = 0;
            let heartRate = 0;
            let respiratoryRate = 0;
            let currentPulseStrength = 1.0;
            let animationId;
            
            // Respiration bar animation variables
            let respirationBarAnimationId;
            let lastRespirationTime = 0;
            let estimatedRespirationInterval = 3000; // Default 3 seconds
            let pastRespirationInterval = 3000; // Track actual interval for timing
            let respirationBarWidth = 25; // Start at 25%
            let respirationBarExpanding = true;
            
            // D3 elements
            let svg, chartGroup, xScale, yScale, lineGenerator;
            let containerWidth, containerHeight;
            
            // Initialize the chart
            function initChart() {
                const container = document.querySelector('.chart-container');
                containerWidth = container.clientWidth;
                containerHeight = container.clientHeight - 80; // Account for status bar and respiration bar
                
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
                    .domain([0, 140])  // Increased domain to accommodate higher baseline + amplitude (60 + 65 = 125, plus buffer)
                    .range([200, 20]);  // Fixed height: 180px for waveform, leaving space for time markers
                
                // Create line generator
                lineGenerator = d3.line()
                    .x(d => xScale(d.timestamp))
                    .y(d => yScale(d.value))
                    .curve(d3.curveMonotoneX);
                
                // Create time markers group
                chartGroup.append('g').attr('class', 'time-markers');
                

                
                // Note: Y-axis removed as amplitude values are not meaningful to users
            }
            
            // Update the chart with new data
            function updateChart() {
                if (!scenarioRunning) return;
                
                const now = Date.now();
                
                // Update x-scale domain to show rolling window
                xScale.domain([now - config.timeWindow, now]);
                
                // Remove old data points
                const chartCutoffTime = now - config.timeWindow;
                heartbeatData = heartbeatData.filter(d => d.timestamp >= chartCutoffTime);
                
                // Update the line
                chartGroup.selectAll('.ekg-line').remove();
                
                if (heartbeatData.length > 1) {
                    chartGroup.append('path')
                        .attr('class', 'ekg-line')
                        .attr('d', lineGenerator(heartbeatData));
                }
                
                // Update time markers
                updateTimeMarkers(now);
                
                // Note: Y-axis removed as amplitude values are not meaningful to users
            }
            
            // Update time markers - positioned 20px above bottom of rolling grid
            function updateTimeMarkers(currentTime) {
                const timeMarkersGroup = chartGroup.select('.time-markers');
                
                // Clear existing markers
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
                        // Time marker line - extends from bottom to 20px above bottom
                        timeMarkersGroup.append('line')
                            .attr('class', 'time-marker')
                            .attr('x1', x)
                            .attr('y1', 200)  // Bottom of chart area
                            .attr('x2', x)
                            .attr('y2', 180); // 20px above bottom
                        
                        // Rolling vertical grid line - extends full height of chart
                        console.log(`📏 Adding grid line at x=${x}`);
                        timeMarkersGroup.append('line')
                            .attr('class', 'rolling-grid-line')
                            .attr('x1', x)
                            .attr('y1', 0)
                            .attr('x2', x)
                            .attr('y2', 200)
                            .style('stroke', '#999')
                            .style('stroke-width', '1')
                            .style('opacity', '0.4');
                        
                        // Time marker text
                        const date = new Date(markerTime);
                        const hours = date.getHours().toString().padStart(2, '0');
                        const minutes = date.getMinutes().toString().padStart(2, '0');
                        const seconds = date.getSeconds().toString().padStart(2, '0');
                        const timeString = `${hours}:${minutes}:${seconds}`;
                        
                        timeMarkersGroup.append('text')
                            .attr('class', 'time-marker-text')
                            .attr('x', x)
                            .attr('y', 150)  // 50px above bottom (5px above line)
                            .attr('text-anchor', 'middle')
                            .text(timeString);
                    }
                }
            }
            

            
            // Add a heartbeat event to the data
            function addHeartbeat(serverTimestamp, pulseStrength = 1.0) {
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
                const bpmCutoffTime = heartbeatTime - 60000;
                heartbeatTimes = heartbeatTimes.filter(time => time >= bpmCutoffTime);
                
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
                
                // Store current pulse strength for display
                currentPulseStrength = pulseStrength;
                
                // Update pulse strength display
                const pulseElement = document.getElementById('pulse-strength');
                if (pulseElement) {
                    pulseElement.textContent = (pulseStrength * 100).toFixed(0) + '%';
                    // Color code based on pulse strength
                    if (pulseStrength >= 0.8) {
                        pulseElement.className = 'vital-value';
                    } else if (pulseStrength >= 0.5) {
                        pulseElement.className = 'vital-value warning';
                    } else {
                        pulseElement.className = 'vital-value danger';
                    }
                }
                
                // Create EKG waveform data points with pulse strength scaling
                const baseline = 85;  // Increased baseline height by ~30%
                const baseAmplitude = 70;  // Increased base amplitude by additional 20% (50 → 60)
                // Use non-linear scaling to make weak pulses much more visually distinct
                const scaledAmplitude = baseAmplitude * Math.pow(pulseStrength, 1.5);  // Enhanced scaling curve

                const duration = 500;  // Increased duration for wider, more visible beats
                
                // Generate EKG-like waveform with scaled amplitude
                const waveform = generateEKGWaveform(baseline, scaledAmplitude, duration);
                
                // Add waveform to data using server timestamp for accurate positioning
                waveform.forEach((value, index) => {
                    heartbeatData.push({
                        value: value,
                        timestamp: heartbeatTime + index * 3  // Use server timestamp + 1ms intervals for smoother waveform
                    });
                });
                
                // Remove old data points (older than 30 seconds)
                const cutoffTimestamp = heartbeatTime - config.timeWindow;
                heartbeatData = heartbeatData.filter(d => d.timestamp >= cutoffTimestamp);
            }
            
            // Animate the respiration bar
            function animateRespirationBar() {
                if (!scenarioRunning) {
                    return;
                }
                
                const now = Date.now();
                const timeSinceLastRespiration = now - lastRespirationTime;
                
                // Use past interval for timing calculations
                const currentInterval = pastRespirationInterval || estimatedRespirationInterval;
                
                // Calculate progress through the current respiration cycle
                const cycleProgress = (timeSinceLastRespiration % currentInterval) / currentInterval;
                
                // Simple linear animation without complex easing
                if (cycleProgress < 0.5) {
                    // First half: Expand (inhalation)
                    const expandProgress = cycleProgress / 0.5;
                    respirationBarWidth = 25 + (expandProgress * 75); // 25% to 100%
                } else {
                    // Second half: Contract (exhalation)
                    const contractProgress = (cycleProgress - 0.5) / 0.5;
                    respirationBarWidth = 100 - (contractProgress * 75); // 100% to 25%
                }
                
                // Update the respiration bar directly without smoothing
                const respirationBar = document.getElementById('respirationBar');
                if (respirationBar) {
                    respirationBar.style.width = respirationBarWidth + '%';
                }
                
                // Continue animation
                respirationBarAnimationId = requestAnimationFrame(animateRespirationBar);
            }
            
            // Add a respiration event to the data
            function addRespiration(serverTimestamp) {
                // Only process respirations if scenario is running
                if (!scenarioRunning) {
                    return;
                }
                
                const now = Date.now();
                
                // Use server timestamp if provided, otherwise use client time
                const respirationTime = serverTimestamp || now;
                
                // Update estimated respiration interval for animation
                if (lastRespirationTime > 0) {
                    const interval = respirationTime - lastRespirationTime;
                    // Update past interval for timing calculations
                    pastRespirationInterval = interval;
                    // Smoothly update estimated interval (weighted average)
                    estimatedRespirationInterval = (estimatedRespirationInterval * 0.7) + (interval * 0.3);
                }
                lastRespirationTime = respirationTime;
                
                // Reset respiration bar to start of inhalation cycle
                respirationBarWidth = 25;
                respirationBarExpanding = true;
                
                // Store respiration time for RR calculation
                respirationTimes.push(respirationTime);
                
                // Keep only respirations from the last 60 seconds for RR calculation
                const rrCutoffTime = respirationTime - 60000;
                respirationTimes = respirationTimes.filter(time => time >= rrCutoffTime);
                
                // Calculate respiratory rate based on recent respirations
                if (respirationTimes.length >= 2) {
                    const intervals = [];
                    for (let i = 1; i < respirationTimes.length; i++) {
                        intervals.push(respirationTimes[i] - respirationTimes[i-1]);
                    }
                    const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
                    respiratoryRate = Math.round(60000 / avgInterval);
                    
                    // Update respiratory rate display if it exists
                    const rrElement = document.getElementById('respiratory-rate');
                    if (rrElement) {
                        rrElement.textContent = respiratoryRate + '/min';
                    }
                }
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
                startAnimation();
                
                // Start respiration bar animation
                if (respirationBarAnimationId) {
                    cancelAnimationFrame(respirationBarAnimationId);
                }
                animateRespirationBar();
                
                // Clear previous data when starting new simulation
                heartbeatData = [];
                heartbeatTimes = [];
                heartRate = 0;
                currentPulseStrength = 1.0;
                lastRespirationTime = 0;
                estimatedRespirationInterval = 3000;
                pastRespirationInterval = 3000;
                respirationBarWidth = 25;
                document.getElementById('heartRate').textContent = '-- BPM';
                document.getElementById('pulse-strength').textContent = '--';
                document.getElementById('pulse-strength').className = 'vital-value';
            }
            
            // Update vital signs display
            function updateVitalSigns(data) {
                // Update temperature
                if (data.temperature !== undefined) {
                    const tempElement = document.getElementById('temperature');
                    tempElement.textContent = data.temperature.toFixed(1) + '°F';
                    tempElement.className = 'vital-value' + getVitalClass(data.temperature, 95, 100);
                }
                
                // Update SpO2
                if (data.spo2 !== undefined) {
                    const spo2Element = document.getElementById('spo2');
                    spo2Element.textContent = data.spo2 + '%';
                    spo2Element.className = 'vital-value' + getVitalClass(data.spo2, 90, 100, true);
                }
                
                // Update blood pressure
                if (data.blood_pressure) {
                    const bpElement = document.getElementById('blood-pressure');
                    bpElement.textContent = data.blood_pressure.systolic + '/' + data.blood_pressure.diastolic;
                    // Check if BP is in normal range (systolic 90-140, diastolic 60-90)
                    const isNormal = data.blood_pressure.systolic >= 90 && data.blood_pressure.systolic <= 140 &&
                                   data.blood_pressure.diastolic >= 60 && data.blood_pressure.diastolic <= 90;
                    bpElement.className = 'vital-value' + (isNormal ? '' : '.warning');
                }
                
                // Update ECG rhythm
                if (data.ecg_rhythm) {
                    const rhythmElement = document.getElementById('ecg-rhythm');
                    rhythmElement.textContent = data.ecg_rhythm;
                    rhythmElement.className = 'vital-value' + getRhythmClass(data.ecg_rhythm);
                }
            }
            
            // Get CSS class for vital sign values based on ranges
            function getVitalClass(value, min, max, reverse = false) {
                if (reverse) {
                    // For SpO2, higher is better
                    if (value < min) return ' danger';
                    if (value < max - 5) return ' warning';
                } else {
                    // For other vitals, normal range is better
                    if (value < min || value > max) return ' danger';
                    if (value < min + 2 || value > max - 2) return ' warning';
                }
                return '';
            }
            
            // Get CSS class for ECG rhythm
            function getRhythmClass(rhythm) {
                const normalRhythms = ['normal sinus rhythm', 'sinus rhythm'];
                const warningRhythms = ['sinus tachycardia', 'sinus bradycardia'];
                const dangerRhythms = ['irregular rhythm', 'asystole', 'flatline', 'bradycardia', 'severe bradycardia'];
                
                if (normalRhythms.includes(rhythm.toLowerCase())) return '';
                if (warningRhythms.includes(rhythm.toLowerCase())) return ' warning';
                if (dangerRhythms.includes(rhythm.toLowerCase())) return ' danger';
                return '';
            }
            
            // Stop scenario
            function stopScenario() {
                scenarioRunning = false;
                document.getElementById('statusText').textContent = 'No Simulation';
                document.getElementById('status').classList.remove('connected');
                document.getElementById('heartRate').textContent = '-- BPM';
                
                // Reset vital signs
                document.getElementById('temperature').textContent = '--°F';
                document.getElementById('spo2').textContent = '--%';
                document.getElementById('respiratory-rate').textContent = '--/min';
                document.getElementById('blood-pressure').textContent = '--/--';
                document.getElementById('ecg-rhythm').textContent = '--';
                
                // Reset classes
                document.getElementById('temperature').className = 'vital-value';
                document.getElementById('spo2').className = 'vital-value';
                document.getElementById('respiratory-rate').className = 'vital-value';
                document.getElementById('blood-pressure').className = 'vital-value';
                document.getElementById('ecg-rhythm').className = 'vital-value';
                
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
            
            // Stop scenario
            function stopScenario() {
                scenarioRunning = false;
                document.getElementById('statusText').textContent = 'Simulation Stopped';
                document.getElementById('status').classList.remove('connected');
                
                // Reset vital signs
                document.getElementById('heartRate').textContent = '-- BPM';
                document.getElementById('temperature').textContent = '--°F';
                document.getElementById('spo2').textContent = '--%';
                document.getElementById('respiratory-rate').textContent = '--/min';
                document.getElementById('blood-pressure').textContent = '--/--';
                document.getElementById('ecg-rhythm').textContent = '--';
                
                // Reset classes
                document.getElementById('temperature').className = 'vital-value';
                document.getElementById('spo2').className = 'vital-value';
                document.getElementById('respiratory-rate').className = 'vital-value';
                document.getElementById('blood-pressure').className = 'vital-value';
                document.getElementById('ecg-rhythm').className = 'vital-value';
                
                // Stop animations
                if (animationId) {
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }
                if (respirationBarAnimationId) {
                    cancelAnimationFrame(respirationBarAnimationId);
                    respirationBarAnimationId = null;
                }
                
                // Reset respiration bar
                const respirationBar = document.getElementById('respirationBar');
                if (respirationBar) {
                    respirationBar.style.width = '25%';
                }
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
                console.log('🔌 Attempting to connect to WebSocket:', wsUrl);
                
                websocket = new WebSocket(wsUrl);
                
                websocket.onopen = function(event) {
                    console.log('✅ WebSocket connected successfully');
                    isConnected = true;
                    document.getElementById('status').classList.add('connected');
                    document.getElementById('statusText').textContent = 'Connected';
                };
                
                websocket.onmessage = function(event) {
                    console.log('📨 WebSocket message received:', event.data);
                    try {
                        const data = JSON.parse(event.data);
                        console.log('📊 Parsed message:', data.event_type, data);
                        
                        if (data.event_type === 'scenario_started') {
                            console.log('🚀 Scenario started:', data.scenario);
                            startScenario();
                        } else if (data.event_type === 'heartbeat') {
                            console.log('💓 Heartbeat received:', data.timestamp, 'pulse_strength:', data.pulse_strength);
                            const pulseStrength = data.pulse_strength || 1.0;  // Default to 1.0 if not provided
                            addHeartbeat(data.timestamp, pulseStrength);
                        } else if (data.event_type === 'respiration') {
                            console.log('🫁 Respiration received:', data.timestamp, 'past interval:', pastRespirationInterval.toFixed(0) + 'ms');
                            addRespiration(data.timestamp);
                        } else if (data.event_type === 'vital_signs') {
                            console.log('📊 Vital signs received:', data);
                            updateVitalSigns(data);
                        } else if (data.event_type === 'scenario_stopped' || data.event_type === 'scenario_complete') {
                            console.log('🛑 Scenario stopped/completed');
                            stopScenario();
                        }
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };
                
                websocket.onclose = function(event) {
                    console.log('❌ WebSocket connection closed:', event.code, event.reason);
                    isConnected = false;
                    document.getElementById('status').classList.remove('connected');
                    document.getElementById('statusText').textContent = 'Disconnected';
                    
                    // Try to reconnect after 3 seconds
                    setTimeout(connectWebSocket, 3000);
                };
                
                websocket.onerror = function(error) {
                    console.log('❌ WebSocket connection error:', error);
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