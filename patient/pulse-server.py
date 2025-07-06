import socket
import json
import time
import threading
import os
import asyncio
import websockets
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HeartbeatServer:
    def __init__(self, host='localhost', port=5000, websocket_port=8092):
        self.host = host
        self.port = port
        self.websocket_port = websocket_port
        self.server_socket = None
        self.clients = []
        self.clients_lock = threading.Lock()
        self.websocket_clients = set()
        self.websocket_lock = threading.Lock()
        self.websocket_message_queue = None  # Will be initialized in async context
        self.websocket_loop = None  # Will store the WebSocket event loop
        self.running = False
        self.current_scenario = None
        self.scenario_thread = None
        self.scenario_running = False  # Flag to track if scenario should continue running
        
        # Path to heartbeat data files
        self.data_dir = Path(__file__).parent / "biometric/pulse/demo_stream_source"
        
    def load_heartbeat_data(self, scenario: str) -> List[int]:
        """Load heartbeat timing data from JSON file."""
        file_path = self.data_dir / f"{scenario}.json"
        
        if not file_path.exists():
            logger.error(f"Heartbeat data file not found: {file_path}")
            return []
            
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} heartbeat events from {scenario}")
            return data
        except Exception as e:
            logger.error(f"Error loading heartbeat data: {e}")
            return []
    
    def broadcast_event(self, event_data: Dict):
        """Send heartbeat event to all connected clients."""
        message = json.dumps(event_data) + '\n'
        message_bytes = message.encode('utf-8')
        
        with self.clients_lock:
            # Remove disconnected clients
            self.clients = [client for client in self.clients if self.is_client_connected(client)]
            
            # Send to remaining clients
            print(f"📡 Broadcasting to {len(self.clients)} TCP clients: {event_data}")
            for client in self.clients:
                try:
                    client.send(message_bytes)
                    print(f"✅ Successfully sent to TCP client")
                except Exception as e:
                    logger.warning(f"Failed to send to TCP client: {e}")
                    print(f"❌ Failed to send to TCP client: {e}")
                    # Client will be removed on next broadcast
        
        # Also send to WebSocket clients
        print(f"🌐 Attempting to broadcast to WebSocket clients...")
        try:
            self.broadcast_websocket_event(event_data)
        except Exception as e:
            print(f"❌ Error broadcasting to WebSocket clients: {e}")
            import traceback
            traceback.print_exc()
    
    def broadcast_websocket_event(self, event_data: Dict):
        """Broadcast a message directly to all WebSocket clients."""
        message = json.dumps(event_data)
        
        if self.websocket_loop:
            try:
                # Create a task to broadcast to all clients
                async def broadcast_to_all():
                    disconnected_clients = set()
                    for websocket in self.websocket_clients:
                        try:
                            await websocket.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.add(websocket)
                        except Exception as e:
                            logger.warning(f"Error sending to client {websocket.remote_address}: {e}")
                            disconnected_clients.add(websocket)
                    
                    # Remove disconnected clients
                    if disconnected_clients:
                        with self.websocket_lock:
                            self.websocket_clients -= disconnected_clients
                
                # Schedule the broadcast task
                asyncio.run_coroutine_threadsafe(broadcast_to_all(), self.websocket_loop)
            except Exception as e:
                logger.error(f"Failed to schedule broadcast: {e}")
        else:
            logger.error("WebSocket loop not initialized")
    
    def is_client_connected(self, client_socket) -> bool:
        """Check if client socket is still connected."""
        try:
            # Try to send a small amount of data to test connection
            client_socket.send(b'')
            return True
        except:
            return False
    
    def run_scenario(self, scenario: str):
        """Run a heartbeat scenario and stream events."""
        logger.info(f"Starting heartbeat scenario: {scenario}")
        
        # Set the scenario running flag
        self.scenario_running = True
        
        # Load heartbeat data (these are absolute offsets from start in milliseconds)
        heartbeat_offsets = self.load_heartbeat_data(scenario)
        if not heartbeat_offsets:
            logger.error(f"No heartbeat data found for scenario: {scenario}")
            self.scenario_running = False
            return
        
        # Record the scenario start time
        scenario_start_time = time.time() * 1000  # Convert to milliseconds
        event_count = 0
        previous_offset = 0  # Initialize previous offset to 0
        
        # Process each heartbeat offset
        for i, offset_ms in enumerate(heartbeat_offsets):
            # Check if scenario should continue running
            if not self.running or not self.scenario_running:
                logger.info(f"Scenario {scenario} stopped early")
                break
            
            # Calculate wait time as difference between current and previous offset
            wait_time = offset_ms - previous_offset
            
            # Wait for the calculated interval
            if wait_time > 0:
                time.sleep(wait_time / 1000.0)  # Convert milliseconds to seconds
                
                # Check again after sleep in case scenario was stopped during sleep
                if not self.scenario_running:
                    logger.info(f"Scenario {scenario} stopped during sleep")
                    break
            
            # Send heartbeat event
            current_time = time.time() * 1000
            event_data = {
                "timestamp": int(current_time),
                "scenario": scenario,
                "event_type": "heartbeat",
                "event_number": event_count,
                "interval_ms": wait_time,
                "elapsed_ms": int(current_time - scenario_start_time)
            }
            
            self.broadcast_event(event_data)
            event_count += 1
            
            logger.debug(f"Sent heartbeat event {event_count}: {event_data}")
            
            # Update previous offset for next iteration
            previous_offset = offset_ms
        
        # Reset the scenario running flag
        self.scenario_running = False
        
        # Send scenario completion event only if it completed naturally
        if self.running and event_count > 0:
            completion_event = {
                "timestamp": int(time.time() * 1000),
                "scenario": scenario,
                "event_type": "scenario_complete",
                "total_events": event_count,
                "total_duration_ms": int(time.time() * 1000 - scenario_start_time)
            }
            self.broadcast_event(completion_event)
            logger.info(f"Completed heartbeat scenario: {scenario}")
        else:
            logger.info(f"Scenario {scenario} was stopped")
    
    def handle_client(self, client_socket, client_address):
        """Handle individual client connection."""
        logger.info(f"New client connected: {client_address}")
        
        with self.clients_lock:
            self.clients.append(client_socket)
        
        try:
            # Send welcome message
            welcome = {
                "timestamp": int(time.time() * 1000),
                "event_type": "welcome",
                "message": "Connected to heartbeat server"
            }
            client_socket.send((json.dumps(welcome) + '\n').encode('utf-8'))
            
            # Keep connection alive
            while self.running:
                try:
                    # Wait for client message (could be commands)
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Parse client message
                    message = data.decode('utf-8').strip()
                    if message:
                        logger.debug(f"Received from client: {message}")
                        try:
                            command_data = json.loads(message)
                            if command_data.get('command') == 'start_scenario':
                                scenario = command_data.get('scenario')
                                if scenario:
                                    self.start_scenario(scenario)
                            elif command_data.get('command') == 'stop_scenario':
                                self.stop_scenario()
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON from client: {message}")
                        
                except Exception as e:
                    logger.debug(f"Client connection error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error handling client {client_address}: {e}")
        finally:
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()
            logger.info(f"Client disconnected: {client_address}")
    
    def start_server(self):
        """Start the heartbeat server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"Heartbeat server started on {self.host}:{self.port}")
            logger.info(f"WebSocket server will start on {self.host}:{self.websocket_port}")
            
            # Start WebSocket server in a separate thread
            websocket_thread = threading.Thread(target=self.start_websocket_server)
            websocket_thread.daemon = True
            websocket_thread.start()
            
            # Accept client connections
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting client: {e}")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.stop_server()
    
    def start_websocket_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.host}:{self.websocket_port}")
        
        async def websocket_handler(websocket):
            """Handle WebSocket connections."""
            logger.info(f"New WebSocket client connected from {websocket.remote_address}")
            
            with self.websocket_lock:
                self.websocket_clients.add(websocket)
            
            try:
                # Send welcome message
                welcome = {
                    "timestamp": int(time.time() * 1000),
                    "event_type": "welcome",
                    "message": "Connected to heartbeat WebSocket server"
                }
                await websocket.send(json.dumps(welcome))
                
                # If a scenario is currently running, send the current state to the new client
                if self.current_scenario and self.scenario_running:
                    current_scenario_event = {
                        "timestamp": int(time.time() * 1000),
                        "event_type": "scenario_started",
                        "scenario": self.current_scenario,
                        "message": f"Current scenario: {self.current_scenario}"
                    }
                    await websocket.send(json.dumps(current_scenario_event))
                
                # Handle incoming messages from client
                async for message in websocket:
                    logger.debug(f"Received WebSocket message: {message}")
                    try:
                        command_data = json.loads(message)
                        if command_data.get('command') == 'start_scenario':
                            scenario = command_data.get('scenario')
                            if scenario:
                                self.start_scenario(scenario)
                        elif command_data.get('command') == 'stop_scenario':
                            self.stop_scenario()
                        elif command_data.get('type') == 'client_heartbeat':
                            # Client heartbeat - just log it to show client is alive
                            logger.debug(f"Client heartbeat received from {websocket.remote_address}")
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON from WebSocket client: {message}")
                
            except websockets.exceptions.ConnectionClosed:
                logger.info("WebSocket client disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            finally:
                with self.websocket_lock:
                    if websocket in self.websocket_clients:
                        self.websocket_clients.remove(websocket)
                        
                        # If no clients are connected and a scenario is running, stop it
                        if len(self.websocket_clients) == 0 and self.scenario_running:
                            logger.info(f"No clients connected, stopping orphaned scenario: {self.current_scenario}")
                            self.stop_scenario()
        
        # Create and run event loop for WebSocket server
        async def run_websocket_server():
            # Start the WebSocket server
            async with websockets.serve(websocket_handler, self.host, self.websocket_port) as server:
                logger.info("WebSocket server started successfully")
                await asyncio.Future()  # Run forever
        
        # Run the WebSocket server in its own event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.websocket_loop = loop  # Store the loop reference
        try:
            loop.run_until_complete(run_websocket_server())
        except KeyboardInterrupt:
            pass
        finally:
            loop.close()
    
    def start_scenario(self, scenario: str):
        """Start a heartbeat scenario in a separate thread."""
        # Always stop any current scenario first
        if self.scenario_thread and self.scenario_thread.is_alive():
            logger.info(f"Stopping current scenario ({self.current_scenario}) to start new one ({scenario})")
            self.stop_scenario()
            # Give a moment for the thread to stop
            time.sleep(0.1)
        
        self.current_scenario = scenario
        self.scenario_thread = threading.Thread(target=self.run_scenario, args=(scenario,))
        self.scenario_thread.daemon = True
        self.scenario_thread.start()
        logger.info(f"Started scenario thread for: {scenario}")
        
        # Small delay to ensure WebSocket connections are ready
        time.sleep(0.2)
        
        # Send scenario_started message to WebSocket clients
        scenario_event = {
            "timestamp": int(time.time() * 1000),
            "event_type": "scenario_started",
            "scenario": scenario,
            "message": f"Started {scenario} scenario"
        }
        
        # Use direct broadcast to all WebSocket clients
        self.broadcast_websocket_event(scenario_event)
        
        # Also send via TCP for compatibility
        self.broadcast_event(scenario_event)
    
    def stop_scenario(self):
        """Stop the current heartbeat scenario."""
        if self.current_scenario:
            logger.info(f"Stopping current scenario: {self.current_scenario}")
            self.current_scenario = None
            
            # Set the flag to stop the scenario thread
            self.scenario_running = False
            
            # Send stop notification to WebSocket clients
            stop_event = {
                "timestamp": int(time.time() * 1000),
                "event_type": "scenario_stopped",
                "message": "Scenario stopped"
            }
            print(f"🛑 Sending stop notification to WebSocket clients: {stop_event}")
            self.broadcast_websocket_event(stop_event)
        else:
            logger.info("No scenario currently running")
    
    def stop_server(self):
        """Stop the heartbeat server."""
        self.running = False
        
        # Close all client connections
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("Heartbeat server stopped")

def main():
    """Main function to run the heartbeat server."""
    server = HeartbeatServer()
    
    try:
        # Start server in a separate thread
        server_thread = threading.Thread(target=server.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        logger.info("Heartbeat server is running. Available scenarios: normal, irregular, cardiac-arrest")
        logger.info("Use Ctrl+C to stop the server")
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.stop_server()

if __name__ == "__main__":
    main() 