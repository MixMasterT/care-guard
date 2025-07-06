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
    // WebSocket connection
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    let heartbeatCount = 0;  // Track heartbeat count
    
    function connectWebSocket() {
        try {
            ws = new WebSocket('ws://localhost:8092');
            
            // Make WebSocket globally accessible
            window.ws = ws;
            
            ws.onopen = function(event) {
                document.getElementById('websocket-status').textContent = 'Connected';
                document.getElementById('websocket-status').className = 'connected';
                reconnectAttempts = 0;
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    if (data.event_type === 'heartbeat') {
                        heartbeatCount++;
                        triggerHeartbeat();
                    } else if (data.event_type === 'welcome') {
                        // Welcome message received
                    } else if (data.event_type === 'scenario_started') {
                        // Update Streamlit session state via a custom event
                        window.parent.postMessage({
                            type: 'scenario_started',
                            scenario: data.scenario
                        }, '*');
                    } else if (data.event_type === 'scenario_stopped') {
                        // Update Streamlit session state via a custom event
                        window.parent.postMessage({
                            type: 'scenario_stopped'
                        }, '*');
                        
                        // Also update the heart to show it's stopped
                        const heart = document.getElementById('heart-emoji');
                        heart.textContent = '🤍';
                        heart.classList.remove('heartbeat-pulse');
                        
                        // Force a page reload to update the Streamlit UI
                        setTimeout(() => {
                            window.parent.location.reload();
                        }, 500);
                    }
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };
            
            ws.onclose = function(event) {
                document.getElementById('websocket-status').textContent = 'Disconnected';
                document.getElementById('websocket-status').className = 'disconnected';
                
                // Attempt to reconnect
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    document.getElementById('websocket-status').textContent = `Reconnecting... (${reconnectAttempts}/${maxReconnectAttempts})`;
                    document.getElementById('websocket-status').className = 'connecting';
                    setTimeout(connectWebSocket, 2000);
                }
            };
            
            ws.onerror = function(error) {
                document.getElementById('websocket-status').textContent = 'Connection Error';
                document.getElementById('websocket-status').className = 'disconnected';
            };
            
        } catch (error) {
            document.getElementById('websocket-status').textContent = 'Connection Failed';
            document.getElementById('websocket-status').className = 'disconnected';
        }
    }
    
    // Function to trigger heartbeat animation
    function triggerHeartbeat() {
        const heart = document.getElementById('heart-emoji');
        
        // Force the animation to restart by removing and re-adding the class
        heart.classList.remove('heartbeat-pulse');
        heart.textContent = '❤️';
        
        // Use requestAnimationFrame to ensure the DOM update happens before adding the class
        requestAnimationFrame(() => {
            heart.classList.add('heartbeat-pulse');
        });
        
        // Remove animation class after animation completes
        setTimeout(() => {
            heart.classList.remove('heartbeat-pulse');
            heart.textContent = '🤍';
        }, 300);
    }
    
    // Make function globally available
    window.triggerHeartbeat = triggerHeartbeat;
    
    // Connect to WebSocket when page loads
    connectWebSocket();
    
    // Add beforeunload event listener to stop simulation before page unloads
    window.addEventListener('beforeunload', function(event) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            try {
                // Send stop command to server
                const stopCommand = {
                    command: 'stop_scenario'
                };
                ws.send(JSON.stringify(stopCommand));
                
                // Give a small delay for the command to be sent
                event.preventDefault();
                event.returnValue = '';
            } catch (error) {
                console.error('Error sending stop command:', error);
            }
        }
    });
    
    // Add visibilitychange event listener to handle tab switching
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden') {
            // Page hidden
        } else if (document.visibilityState === 'visible') {
            // Page visible again
        }
    });
    
    // Add a periodic check to see if WebSocket is still connected
    setInterval(function() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            // Send a heartbeat to let the server know we're still here
            try {
                const heartbeat = {
                    type: 'client_heartbeat',
                    timestamp: Date.now()
                };
                ws.send(JSON.stringify(heartbeat));
            } catch (error) {
                console.error('Error sending client heartbeat:', error);
            }
        }
    }, 5000); // Check every 5 seconds
    </script>
    """
    
    return html_code 