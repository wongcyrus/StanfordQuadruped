#!/usr/bin/env python3
"""
Enhanced Network Action Server for Stanford Quadruped Mini Pupper

This server provides a REST API for controlling the dog robot remotely.
It integrates with MovementGroups to provide high-level movement functions.

Author: Enhanced by AI Assistant
License: Apache 2.0
"""

import json
import logging
import queue
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import numpy as np

# Add src directory to path for MovementGroup import
sys.path.append("./src")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import MovementGroups and robot control components
try:
    from pupper.Kinematics import four_legs_inverse_kinematics
    from src.Command import Command
    from src.Controller import Controller
    from src.MovementGroup import MovementGroups
    from src.MovementScheme import MovementScheme
    from src.State import State

    logger.info("MovementGroups and robot control components imported successfully")
except ImportError as e:
    logger.error(f"Failed to import robot control components: {e}")
    MovementGroups = None

# Import hardware interface
try:
    from MangDang.mini_pupper.Config import Configuration
    from MangDang.mini_pupper.display import Display
    from MangDang.mini_pupper.HardwareInterface import HardwareInterface

    logger.info("Hardware interface imported successfully")
except ImportError as e:
    logger.error(f"Failed to import hardware interface: {e}")
    HardwareInterface = None
    Configuration = None
    Display = None


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
    """Enhanced action controller with MovementGroups integration."""

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

        # Initialize MovementGroups
        if MovementGroups:
            self.movement_groups = MovementGroups()
            logger.info("MovementGroups initialized successfully")
        else:
            self.movement_groups = None
            logger.error("MovementGroups not available - running in limited mode")

        # Initialize robot hardware components
        self.controller = None
        self.hardware_interface = None
        self.state = None
        self.config = None
        self._init_robot_hardware()

        # Import UDP publisher if available
        try:
            import UDPComms

            self.udp_publisher = UDPComms.Publisher(udp_port)
            logger.info(f"UDP publisher initialized on port {udp_port}")
        except ImportError:
            logger.error("UDPComms not available - running in simulation mode")
            self.udp_publisher = None

        # Available actions from MovementGroups
        self.available_actions = self._get_available_actions()

        # Start action processor thread
        self.processor_thread = threading.Thread(
            target=self._action_processor, daemon=True
        )
        self.processor_thread.start()

    def _init_robot_hardware(self):
        """Initialize robot hardware components."""
        try:
            if Configuration and HardwareInterface:
                self.config = Configuration()
                self.hardware_interface = HardwareInterface()
                self.controller = Controller(self.config, four_legs_inverse_kinematics)
                self.state = State()
                if Display:
                    self.display = Display()
                else:
                    self.display = None
                logger.info("Robot hardware initialized successfully")
            else:
                logger.warning(
                    "Hardware interface not available - running in simulation mode"
                )
        except Exception as e:
            logger.error(f"Failed to initialize robot hardware: {e}")
            self.controller = None
            self.hardware_interface = None
            self.state = None
            self.config = None
            self.display = None

    def _get_available_actions(self) -> list:
        """Get list of available actions from MovementGroups."""
        if not self.movement_groups:
            return []

        # Get all public methods from MovementGroups (excluding private and built-in methods)
        actions = []
        for attr_name in dir(self.movement_groups):
            if not attr_name.startswith("_") and callable(
                getattr(self.movement_groups, attr_name)
            ):
                # Exclude utility methods
                if attr_name not in ["cap_limit"]:
                    actions.append(attr_name)

        return sorted(actions)

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
        """Execute a single action using MovementGroups and robot controller."""
        action_name = action.action_name.lower()
        duration = action.duration
        parameters = action.parameters or {}

        if not self.movement_groups:
            logger.warning("MovementGroups not available")
            return False

        if action_name not in self.available_actions:
            logger.warning(f"Unknown action: {action_name}")
            return False

        if not self.controller or not self.hardware_interface or not self.state:
            logger.warning(
                "Robot hardware not available - executing in simulation mode"
            )
            return self._execute_simulation_mode(action)

        try:
            # Get the movement function
            movement_func = getattr(self.movement_groups, action_name)

            # Clear any previous movements
            self.movement_groups.MovementLib = []

            # Execute the movement function with parameters
            if action_name == "stop":
                # Stop function takes time parameter
                movement_func(time=duration)
            elif action_name in [
                "head_move",
                "look_up",
                "look_down",
                "look_left",
                "look_right",
            ]:
                # Head move takes pitch_deg, yaw_deg, time_uni, time_acc
                pitch_deg = parameters.get("pitch_deg", 0)
                yaw_deg = parameters.get("yaw_deg", 0)
                time_uni = parameters.get("time_uni", duration)
                time_acc = parameters.get("time_acc", 1.0)
                if action_name == "head_move":
                    movement_func(
                        pitch_deg=pitch_deg,
                        yaw_deg=yaw_deg,
                        time_uni=time_uni,
                        time_acc=time_acc,
                    )
                else:
                    movement_func()
            elif action_name in ["body_row"]:
                # Body row takes row_deg, time_uni, time_acc
                row_deg = parameters.get("row_deg", 0)
                time_uni = parameters.get("time_uni", duration)
                time_acc = parameters.get("time_acc", 1.0)
                movement_func(row_deg=row_deg, time_uni=time_uni, time_acc=time_acc)
            elif action_name in ["gait_uni"]:
                # Gait uni takes v_x, v_y, time_uni, time_acc
                v_x = parameters.get("v_x", 0)
                v_y = parameters.get("v_y", 0)
                time_uni = parameters.get("time_uni", duration)
                time_acc = parameters.get("time_acc", 1.0)
                movement_func(v_x=v_x, v_y=v_y, time_uni=time_uni, time_acc=time_acc)
            elif action_name in ["height_move"]:
                # Height move takes ht, time_uni, time_acc
                ht = parameters.get("ht", 0)
                time_uni = parameters.get("time_uni", duration)
                time_acc = parameters.get("time_acc", 1.0)
                movement_func(ht=ht, time_uni=time_uni, time_acc=time_acc)
            elif action_name in ["foreleg_lift", "backleg_lift"]:
                # Leg lift takes leg_index, ht, time_uni, time_acc
                leg_index = parameters.get("leg_index", "left")
                ht = parameters.get("ht", 0.01)
                time_uni = parameters.get("time_uni", duration)
                time_acc = parameters.get("time_acc", 1.0)
                movement_func(
                    leg_index=leg_index, ht=ht, time_uni=time_uni, time_acc=time_acc
                )
            elif action_name in ["rotate"]:
                # Rotate takes angle
                angle = parameters.get("angle", 1)
                movement_func(angle=angle)
            elif action_name in ["bowback"]:
                # Bowback takes angle
                angle = parameters.get("angle", 20)
                movement_func(angle=angle)
            else:
                # Simple movements with no parameters
                movement_func()

            # Now execute the movements through the robot controller
            if self.movement_groups.MovementLib:
                self._execute_movement_lib(self.movement_groups.MovementLib)

            logger.info(f"Executed MovementGroup action: {action_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to execute MovementGroup action '{action_name}': {e}")
            return False

    def _execute_simulation_mode(self, action: ActionCommand) -> bool:
        """Execute action in simulation mode (without hardware)."""
        try:
            # Get the movement function
            movement_func = getattr(self.movement_groups, action.action_name.lower())

            # Clear any previous movements
            self.movement_groups.MovementLib = []

            # Execute the movement function
            movement_func()

            logger.info(
                f"Executed MovementGroup action in simulation mode: {action.action_name}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to execute action in simulation mode: {e}")
            return False

    def _execute_movement_lib(self, movement_lib: list):
        """Execute a list of movements through the robot controller."""
        if not movement_lib:
            return

        try:
            # Create movement scheme controller
            movement_ctl = MovementScheme(movement_lib)
            command = Command()
            # Set pseudo_dance_event to True like in run_danceActionList.py
            command.pseudo_dance_event = True

            # Set up timing loop similar to run_danceActionList.py
            lib_length = len(movement_lib)
            last_loop = time.time()

            while True:
                now = time.time()

                # Maintain the control loop timing - same as run_danceActionList.py
                if now - last_loop < self.config.dt:
                    continue
                last_loop = time.time()

                # Set default orientation (no IMU)
                self.state.quat_orientation = np.array([1, 0, 0, 0])

                # Run movement scheme
                movement_ctl.runMovementScheme()

                # Get movement commands - same as run_danceActionList.py
                command.legslocation = movement_ctl.getMovemenLegsLocation()
                command.horizontal_velocity = movement_ctl.getMovemenSpeed()
                command.roll = movement_ctl.attitude_now[0]
                command.pitch = movement_ctl.attitude_now[1]
                command.yaw = movement_ctl.attitude_now[2]
                command.yaw_rate = movement_ctl.getMovemenTurn()

                # Run controller
                self.controller.run(self.state, command, self.display)

                # Update hardware
                self.hardware_interface.set_actuator_postions(self.state.joint_angles)

                # Check if movement is complete - same as run_danceActionList.py
                if (
                    movement_ctl.movement_now_number >= lib_length - 1
                    and movement_ctl.tick >= movement_ctl.now_ticks
                ):
                    logger.info("Movement sequence execution completed")
                    break

            logger.info("Movement sequence execution completed")

        except Exception as e:
            logger.error(f"Failed to execute movement sequence: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get current controller status."""
        return {
            "running": self.is_running,
            "robot_state": self.robot_state,
            "queue_status": self.action_queue.get_queue_status(),
            "available_actions": self.available_actions,
        }

    def emergency_stop(self) -> bool:
        """Emergency stop - clear queue and send stop command."""
        logger.warning("Emergency stop activated")

        # Clear action queue
        self.action_queue.clear_queue()

        # Execute stop movement if MovementGroups and hardware are available
        if self.movement_groups and self.controller and self.hardware_interface:
            try:
                # Clear movement library and add stop command
                self.movement_groups.MovementLib = []
                self.movement_groups.stop(time=0.1)

                # Execute the stop movement immediately
                if self.movement_groups.MovementLib:
                    self._execute_movement_lib(self.movement_groups.MovementLib)

                logger.info("Emergency stop movement executed")
            except Exception as e:
                logger.error(f"Failed to execute emergency stop movement: {e}")
        elif self.movement_groups:
            try:
                # Simulation mode - just call the function
                self.movement_groups.MovementLib = []
                self.movement_groups.stop(time=0.1)
                logger.info("Emergency stop executed in simulation mode")
            except Exception as e:
                logger.error(
                    f"Failed to execute emergency stop in simulation mode: {e}"
                )

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
                    "available_actions": self.action_controller.available_actions,
                    "description": "Available actions for the dog robot (MovementGroups)",
                }
                self._send_json_response(actions)

            elif path == "/":
                # Serve basic API documentation
                api_docs = {
                    "name": "Stanford Quadruped Network Action Server",
                    "version": "2.0",
                    "endpoints": {
                        "GET /status": "Get robot and queue status",
                        "GET /actions": "List available actions",
                        "POST /execute": "Execute an action",
                        "POST /stop": "Emergency stop",
                        "POST /clear": "Clear action queue",
                    },
                    "example_execute": {
                        "action": "move_forward",
                        "duration": 3.0,
                        "parameters": {},
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
