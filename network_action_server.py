#!/usr/bin/env python3
"""
Enhanced Network Action Server for Stanford Quadruped Mini Pupper

This server provides a REST API for controlling the dog robot remotely.
It bridges HTTP requests to UDP commands and provides better action management.

Author: Enhanced by AI Assistant
License: Apache 2.0
"""

import json
import logging
import queue
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ActionCommand:
    """Represents an action command with metadata."""

    def __init__(
        self, action_name: str, duration: float = 3.0, parameters: Dict[str, Any] = None
    ):
        self.action_name = action_name
        self.duration = duration
        self.parameters = parameters or {}
        self.timestamp = datetime.now()
        self.status = "queued"  # queued, executing, completed, failed
        self.error_message = ""


class ActionQueue:
    """Thread-safe action queue for managing robot actions."""

    def __init__(self):
        self._queue = queue.Queue()
        self._current_action: Optional[ActionCommand] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def add_action(self, action: ActionCommand) -> None:
        """Add an action to the queue."""
        with self._lock:
            self._queue.put(action)
            logger.info(f"Added action '{action.action_name}' to queue")

    def get_next_action(self) -> Optional[ActionCommand]:
        """Get the next action from the queue."""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def set_current_action(self, action: Optional[ActionCommand]) -> None:
        """Set the currently executing action."""
        with self._lock:
            self._current_action = action

    def get_current_action(self) -> Optional[ActionCommand]:
        """Get the currently executing action."""
        with self._lock:
            return self._current_action

    def clear_queue(self) -> int:
        """Clear all queued actions and return the count."""
        count = 0
        with self._lock:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    count += 1
                except queue.Empty:
                    break
        logger.info(f"Cleared {count} actions from queue")
        return count

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status information."""
        with self._lock:
            return {
                "queue_size": self._queue.qsize(),
                "current_action": (
                    {
                        "name": (
                            self._current_action.action_name
                            if self._current_action
                            else None
                        ),
                        "status": (
                            self._current_action.status
                            if self._current_action
                            else None
                        ),
                        "duration": (
                            self._current_action.duration
                            if self._current_action
                            else None
                        ),
                    }
                    if self._current_action
                    else None
                ),
            }


class DogActionController:
    """Enhanced action controller with UDP integration."""

    def __init__(self, udp_port: int = 8830):
        self.udp_port = udp_port
        self.action_queue = ActionQueue()
        self.is_running = False
        self.robot_state = {
            "activated": False,
            "walking_enabled": False,
            "dancing_enabled": False,
            "last_action": None,
            "last_action_time": None,
        }

        # Import UDP publisher
        try:
            import UDPComms

            self.udp_publisher = UDPComms.Publisher(udp_port)
            logger.info(f"UDP publisher initialized on port {udp_port}")
        except ImportError:
            logger.error("UDPComms not available - running in simulation mode")
            self.udp_publisher = None

        # Action mapping to UDP commands
        self.action_mappings = {
            # Basic movements
            "forward": {"ly": 1.0, "lx": 0.0, "rx": 0.0, "ry": 0.0},
            "backward": {"ly": -1.0, "lx": 0.0, "rx": 0.0, "ry": 0.0},
            "left": {"ly": 0.0, "lx": -1.0, "rx": 0.0, "ry": 0.0},
            "right": {"ly": 0.0, "lx": 1.0, "rx": 0.0, "ry": 0.0},
            "turn_left": {"ly": 0.0, "lx": 0.0, "rx": -1.0, "ry": 0.0},
            "turn_right": {"ly": 0.0, "lx": 0.0, "rx": 1.0, "ry": 0.0},
            "stop": {"ly": 0.0, "lx": 0.0, "rx": 0.0, "ry": 0.0},
            # Control actions
            "activate": {"L1": 1},
            "deactivate": {"L1": 1},
            "trot": {"R1": 1},
            "hop": {"x": 1},
            "dance": {"circle": 1},
            # Posture actions
            "pitch_up": {"ly": 0.0, "lx": 0.0, "rx": 0.0, "ry": 1.0},
            "pitch_down": {"ly": 0.0, "lx": 0.0, "rx": 0.0, "ry": -1.0},
            "height_up": {"dpady": 1},
            "height_down": {"dpady": -1},
            "roll_left": {"dpadx": -1},
            "roll_right": {"dpadx": 1},
        }

        # Start action processor thread
        self.processor_thread = threading.Thread(
            target=self._action_processor, daemon=True
        )
        self.processor_thread.start()

    def start(self):
        """Start the action controller."""
        self.is_running = True
        logger.info("Dog action controller started")

    def stop(self):
        """Stop the action controller."""
        self.is_running = False
        self.action_queue.clear_queue()
        logger.info("Dog action controller stopped")

    def execute_action(
        self, action_name: str, duration: float = 3.0, parameters: Dict[str, Any] = None
    ) -> bool:
        """Queue an action for execution."""
        action = ActionCommand(action_name, duration, parameters)
        self.action_queue.add_action(action)
        return True

    def _action_processor(self):
        """Process actions from the queue."""
        while True:
            if not self.is_running:
                time.sleep(0.1)
                continue

            action = self.action_queue.get_next_action()
            if not action:
                time.sleep(0.1)
                continue

            self.action_queue.set_current_action(action)
            action.status = "executing"

            try:
                success = self._execute_single_action(action)
                action.status = "completed" if success else "failed"

                # Update robot state
                self.robot_state["last_action"] = action.action_name
                self.robot_state["last_action_time"] = datetime.now().isoformat()

            except Exception as e:
                action.status = "failed"
                action.error_message = str(e)
                logger.error(f"Error executing action '{action.action_name}': {e}")

            finally:
                self.action_queue.set_current_action(None)
                time.sleep(0.1)  # Brief pause between actions

    def _execute_single_action(self, action: ActionCommand) -> bool:
        """Execute a single action via UDP."""
        action_name = action.action_name.lower()
        duration = action.duration

        if action_name not in self.action_mappings:
            logger.warning(f"Unknown action: {action_name}")
            return False

        if not self.udp_publisher:
            logger.info(f"Simulating action: {action_name} for {duration}s")
            time.sleep(duration)
            return True

        try:
            # Send UDP command
            udp_command = self._create_udp_command(action)

            # For movement actions, send continuous commands
            if action_name in [
                "forward",
                "backward",
                "left",
                "right",
                "turn_left",
                "turn_right",
            ]:
                return self._execute_movement_action(udp_command, duration)
            else:
                # For discrete actions, send once
                return self._execute_discrete_action(udp_command, duration)

        except Exception as e:
            logger.error(f"Failed to execute UDP command: {e}")
            return False

    def _create_udp_command(self, action: ActionCommand) -> Dict[str, Any]:
        """Create UDP command from action."""
        base_command = {
            "ly": 0.0,
            "lx": 0.0,
            "rx": 0.0,
            "ry": 0.0,
            "L1": 0,
            "R1": 0,
            "x": 0,
            "circle": 0,
            "triangle": 0,
            "dpady": 0,
            "dpadx": 0,
            "message_rate": 20,
        }

        # Update with action-specific values
        action_mapping = self.action_mappings.get(action.action_name.lower(), {})
        base_command.update(action_mapping)

        # Apply parameters if provided
        if action.parameters:
            for key, value in action.parameters.items():
                if key in base_command:
                    base_command[key] = value

        return base_command

    def _execute_movement_action(
        self, command: Dict[str, Any], duration: float
    ) -> bool:
        """Execute a movement action with continuous commands."""
        logger.info(f"Executing movement action for {duration}s")

        start_time = time.time()
        message_rate = command.get("message_rate", 20)
        sleep_interval = 1.0 / message_rate

        while time.time() - start_time < duration:
            self.udp_publisher.send(command)
            time.sleep(sleep_interval)

        # Send stop command
        stop_command = command.copy()
        stop_command.update({"ly": 0.0, "lx": 0.0, "rx": 0.0, "ry": 0.0})
        self.udp_publisher.send(stop_command)

        return True

    def _execute_discrete_action(
        self, command: Dict[str, Any], duration: float
    ) -> bool:
        """Execute a discrete action (button press)."""
        logger.info(f"Executing discrete action")

        # Send command
        self.udp_publisher.send(command)

        # Wait for duration
        time.sleep(duration)

        return True

    def get_status(self) -> Dict[str, Any]:
        """Get current controller status."""
        return {
            "running": self.is_running,
            "robot_state": self.robot_state,
            "queue_status": self.action_queue.get_queue_status(),
            "available_actions": list(self.action_mappings.keys()),
        }

    def emergency_stop(self) -> bool:
        """Emergency stop - clear queue and send stop command."""
        logger.warning("Emergency stop activated")

        # Clear action queue
        cleared_count = self.action_queue.clear_queue()

        # Send stop command if UDP is available
        if self.udp_publisher:
            stop_command = {
                "ly": 0.0,
                "lx": 0.0,
                "rx": 0.0,
                "ry": 0.0,
                "L1": 0,
                "R1": 0,
                "x": 0,
                "circle": 0,
                "triangle": 0,
                "dpady": 0,
                "dpadx": 0,
                "message_rate": 20,
            }
            self.udp_publisher.send(stop_command)

        return True


class NetworkActionHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the network action server."""

    def __init__(self, action_controller: DogActionController, *args, **kwargs):
        self.action_controller = action_controller
        super().__init__(*args, **kwargs)

    def _send_json_response(self, data: Dict[str, Any], status_code: int = 200):
        """Send a JSON response."""
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode())

    def _send_error_response(self, message: str, status_code: int = 400):
        """Send an error response."""
        self._send_json_response(
            {"error": message, "timestamp": datetime.now().isoformat()}, status_code
        )

    def do_OPTIONS(self):
        """Handle preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            if path == "/status":
                status = self.action_controller.get_status()
                self._send_json_response(status)

            elif path == "/actions":
                actions = {
                    "available_actions": list(
                        self.action_controller.action_mappings.keys()
                    ),
                    "description": "Available actions for the dog robot",
                }
                self._send_json_response(actions)

            elif path == "/":
                # Serve basic API documentation
                api_docs = {
                    "name": "Stanford Quadruped Network Action Server",
                    "version": "1.0",
                    "endpoints": {
                        "GET /status": "Get robot and queue status",
                        "GET /actions": "List available actions",
                        "POST /execute": "Execute an action",
                        "POST /stop": "Emergency stop",
                        "POST /clear": "Clear action queue",
                    },
                    "example_execute": {
                        "action": "forward",
                        "duration": 3.0,
                        "parameters": {"ly": 0.8},
                    },
                }
                self._send_json_response(api_docs)

            else:
                self._send_error_response("Endpoint not found", 404)

        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self._send_error_response(f"Internal server error: {str(e)}", 500)

    def do_POST(self):
        """Handle POST requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                try:
                    request_data = json.loads(post_data.decode())
                except json.JSONDecodeError:
                    self._send_error_response("Invalid JSON in request body")
                    return
            else:
                request_data = {}

            if path == "/execute":
                action_name = request_data.get("action")
                if not action_name:
                    self._send_error_response("Missing 'action' parameter")
                    return

                duration = request_data.get("duration", 3.0)
                parameters = request_data.get("parameters", {})

                success = self.action_controller.execute_action(
                    action_name, duration, parameters
                )

                if success:
                    self._send_json_response(
                        {
                            "success": True,
                            "message": f"Action '{action_name}' queued for execution",
                            "action": action_name,
                            "duration": duration,
                            "parameters": parameters,
                        }
                    )
                else:
                    self._send_error_response(f"Failed to queue action '{action_name}'")

            elif path == "/stop":
                success = self.action_controller.emergency_stop()
                self._send_json_response(
                    {"success": success, "message": "Emergency stop executed"}
                )

            elif path == "/clear":
                cleared_count = self.action_controller.action_queue.clear_queue()
                self._send_json_response(
                    {
                        "success": True,
                        "message": f"Cleared {cleared_count} actions from queue",
                        "cleared_count": cleared_count,
                    }
                )

            else:
                self._send_error_response("Endpoint not found", 404)

        except Exception as e:
            logger.error(f"Error handling POST request: {e}")
            self._send_error_response(f"Internal server error: {str(e)}", 500)


def create_handler(action_controller: DogActionController):
    """Create a handler class with the action controller."""

    def handler(*args, **kwargs):
        NetworkActionHandler(action_controller, *args, **kwargs)

    return handler


def main():
    """Main function to start the network action server."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Stanford Quadruped Network Action Server"
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8080, help="Server port (default: 8080)"
    )
    parser.add_argument(
        "--udp-port",
        type=int,
        default=8830,
        help="UDP port for robot communication (default: 8830)",
    )
    args = parser.parse_args()

    # Create action controller
    action_controller = DogActionController(udp_port=args.udp_port)
    action_controller.start()

    # Create HTTP server
    handler = create_handler(action_controller)
    server = HTTPServer((args.host, args.port), handler)

    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"UDP communication on port {args.udp_port}")
    logger.info("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        action_controller.stop()
        server.shutdown()


if __name__ == "__main__":
    main()
