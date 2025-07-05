def create_heartbeat_component():
    """Create a JavaScript-powered heartbeat component that connects to WebSocket."""
    html_code = """
    <div id="heartbeat-container" style="text-align: center; font-size: 4rem;">
        <div id="heart-emoji">🤍</div>
        <div id="websocket-status" style="font-size: 1rem; margin-top: 10px;">Connecting...</div>
    </div>
    
    <style>
    .heartbeat-pulse {
        animation: heartbeat 0.3s ease-in-out;
    }
    
    @keyframes heartbeat {
        0% { transform: scale(1); }
        25% { transform: scale(1.3); }
        50% { transform: scale(1.1); }
        75% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }
    
    .connected { color: green; }
    .disconnected { color: red; }
    .connecting { color: orange; }
    </style>
    
    <script>
    console.log('🔥 SCRIPT FIRED - JavaScript is executing!');
    
    // WebSocket connection
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    function connectWebSocket() {
        try {
            console.log('🔌 Attempting to connect to WebSocket at ws://localhost:8092...');
            ws = new WebSocket('ws://localhost:8092');
            
            // Make WebSocket globally accessible
            window.ws = ws;
            
            ws.onopen = function(event) {
                console.log('💙 WebSocket connected successfully!');
                console.log('💙 WebSocket readyState: ' + ws.readyState);
                document.getElementById('websocket-status').textContent = 'Connected';
                document.getElementById('websocket-status').className = 'connected';
                reconnectAttempts = 0;
            };
            
            ws.onmessage = function(event) {
                console.log('📨 WebSocket message received: ' + event.data);
                try {
                    const data = JSON.parse(event.data);
                    console.log('📋 Parsed WebSocket data: ' + JSON.stringify(data));
                    if (data.event_type === 'heartbeat') {
                        console.log('💓 Heartbeat received via WebSocket! Triggering animation...');
                        triggerHeartbeat();
                    } else if (data.event_type === 'welcome') {
                        console.log('👋 Welcome message received: ' + data.message);
                    } else if (data.event_type === 'scenario_started') {
                        console.log('🚀 Scenario started: ' + data.scenario);
                        // Update Streamlit session state via a custom event
                        window.parent.postMessage({
                            type: 'scenario_started',
                            scenario: data.scenario
                        }, '*');
                    } else if (data.event_type === 'scenario_stopped') {
                        console.log('🛑 Scenario stopped: ' + data.message);
                        // Update Streamlit session state via a custom event
                        window.parent.postMessage({
                            type: 'scenario_stopped'
                        }, '*');
                        
                        // Also update the heart to show it's stopped
                        const heart = document.getElementById('heart-emoji');
                        heart.textContent = '🤍';
                        heart.classList.remove('heartbeat-pulse');
                        
                        // Force a page reload to update the Streamlit UI -- FIND A WAY TO REMOVE THIS IN THE FUTURE
                        setTimeout(() => {
                            window.parent.location.reload();
                        }, 500); // Small delay to ensure the message is processed
                    } else {
                        console.log('📨 Other event type received: ' + data.event_type);
                    }
                } catch (e) {
                    console.log('❌ Error parsing WebSocket message: ' + e);
                    console.log('❌ Raw message was: ' + event.data);
                }
            };
            
            ws.onclose = function(event) {
                console.log('🔌 WebSocket disconnected. Code: ' + event.code + ', Reason: ' + event.reason);
                document.getElementById('websocket-status').textContent = 'Disconnected';
                document.getElementById('websocket-status').className = 'disconnected';
                
                // Attempt to reconnect
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    console.log(`🔄 Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
                    document.getElementById('websocket-status').textContent = `Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`;
                    document.getElementById('websocket-status').className = 'connecting';
                    setTimeout(connectWebSocket, 2000);
                }
            };
            
            ws.onerror = function(error) {
                console.log('❌ WebSocket error occurred: ' + error);
                console.log('❌ WebSocket readyState: ' + ws.readyState);
                document.getElementById('websocket-status').textContent = 'Connection Error';
                document.getElementById('websocket-status').className = 'disconnected';
            };
            
        } catch (error) {
            console.log('❌ Failed to create WebSocket connection: ' + error);
            document.getElementById('websocket-status').textContent = 'Connection Failed';
            document.getElementById('websocket-status').className = 'disconnected';
        }
    }
    
    // Function to trigger heartbeat animation
    function triggerHeartbeat() {
        const heart = document.getElementById('heart-emoji');
        heart.textContent = '❤️';
        heart.classList.add('heartbeat-pulse');
        
        // Remove animation class after animation completes
        setTimeout(() => {
            heart.classList.remove('heartbeat-pulse');
            heart.textContent = '🤍';
        }, 300);
        
        console.log('💓 Heartbeat animation triggered!');
    }
    
    // Make function globally available
    window.triggerHeartbeat = triggerHeartbeat;
    
    // Connect to WebSocket when page loads
    console.log('💙 Heartbeat component loaded, connecting to WebSocket...');
    console.log('💙 Component HTML loaded, attempting connection...');
    console.log('💙 DOM ready, starting WebSocket connection...');
    
    // Test if JavaScript is working immediately
    console.log('⏰ JavaScript test: Component is working!');
    if (document.getElementById('websocket-status')) {
        document.getElementById('websocket-status').textContent = 'JavaScript loaded';
        console.log('✅ DOM element found and updated');
    } else {
        console.log('❌ DOM element not found');
    }
    
    connectWebSocket();
    
    // Add a periodic check to see if WebSocket is still connected
    setInterval(function() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            console.log('💓 WebSocket still connected - readyState: ' + ws.readyState);
        } else {
            console.log('❌ WebSocket not connected - readyState: ' + (ws ? ws.readyState : 'null'));
        }
    }, 5000); // Check every 5 seconds
    </script>
    """
    
    return html_code 