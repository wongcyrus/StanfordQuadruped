"""
Dog Robot Action Executor

Enhanced action executor for dog robots using the new API structure.
Provides queued action execution, parameter handling, and comprehensive
robot control capabilities.
"""

import logging
import queue
import threading
import time
from typing import Any, Dict, Optional
from uuid import uuid4

import requests

from config import (
    DEFAULT_ACTION_SLEEP_TIME,
    NETWORK_SERVER_HOST,
    NETWORK_SERVER_PORT,
    STOP_ACTION_SLEEP_TIME,
    ActionType,
)

logger = logging.getLogger(__name__)

# Complete action configuration matching network_action_server / MovementGroups API
actions: Dict[str, Dict[str, Any]] = {
    # === Core MovementGroups actions (direct from network_action_server) ===
    # Basic control
    "stop": {
        "sleep_time": STOP_ACTION_SLEEP_TIME,
        "name": "stop",
        "type": ActionType.CONTROL,
        "description": "Return to default standing position",
    },
    # Head/vision movements
    "look_up": {
        "sleep_time": 1.5,
        "name": "look_up",
        "type": ActionType.POSTURE,
        "description": "Look up 20 degrees",
    },
    "look_down": {
        "sleep_time": 1.5,
        "name": "look_down",
        "type": ActionType.POSTURE,
        "description": "Look down 20 degrees",
    },
    "look_left": {
        "sleep_time": 1.5,
        "name": "look_left",
        "type": ActionType.POSTURE,
        "description": "Look left 30 degrees",
    },
    "look_right": {
        "sleep_time": 1.5,
        "name": "look_right",
        "type": ActionType.POSTURE,
        "description": "Look right 30 degrees",
    },
    "look_upperleft": {
        "sleep_time": 1.5,
        "name": "look_upperleft",
        "type": ActionType.POSTURE,
        "description": "Look up 20° and left 30°",
    },
    "look_upperright": {
        "sleep_time": 1.5,
        "name": "look_upperright",
        "type": ActionType.POSTURE,
        "description": "Look up 20° and right 30°",
    },
    "look_leftlower": {
        "sleep_time": 1.5,
        "name": "look_leftlower",
        "type": ActionType.POSTURE,
        "description": "Look down 20° and left 30°",
    },
    "look_rightlower": {
        "sleep_time": 1.5,
        "name": "look_rightlower",
        "type": ActionType.POSTURE,
        "description": "Look down 20° and right 30°",
    },
    # Basic movement (Level 1 - no parameters)
    "move_forward": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_forward",
        "type": ActionType.MOVEMENT,
        "description": "Move forward at 0.15 m/s",
    },
    "move_backward": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_backward",
        "type": ActionType.MOVEMENT,
        "description": "Move backward at 0.15 m/s",
    },
    "move_left": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_left",
        "type": ActionType.MOVEMENT,
        "description": "Move left at 0.15 m/s",
    },
    "move_right": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_right",
        "type": ActionType.MOVEMENT,
        "description": "Move right at 0.15 m/s",
    },
    "move_leftfront": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_leftfront",
        "type": ActionType.MOVEMENT,
        "description": "Move diagonally left-forward",
    },
    "move_rightfront": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_rightfront",
        "type": ActionType.MOVEMENT,
        "description": "Move diagonally right-forward",
    },
    "move_leftback": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_leftback",
        "type": ActionType.MOVEMENT,
        "description": "Move diagonally left-backward",
    },
    "move_rightback": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "move_rightback",
        "type": ActionType.MOVEMENT,
        "description": "Move diagonally right-backward",
    },
    # Parameterized movements (Level 2)
    "head_move": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "head_move",
        "type": ActionType.POSTURE,
        "description": "Move head with pitch_deg, yaw_deg, time_uni, time_acc parameters",
    },
    "body_row": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "body_row",
        "type": ActionType.POSTURE,
        "description": "Tilt body with row_deg, time_uni, time_acc parameters",
    },
    "balance": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "balance",
        "type": ActionType.POSTURE,
        "description": "Balance with roll_deg, pitch_deg, time_uni, time_acc parameters",
    },
    "gait_uni": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "gait_uni",
        "type": ActionType.MOVEMENT,
        "description": "Uniform gait with v_x, v_y, time_uni, time_acc parameters",
    },
    "height_move": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "height_move",
        "type": ActionType.POSTURE,
        "description": "Change height with ht, time_uni, time_acc parameters",
    },
    "foreleg_lift": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "foreleg_lift",
        "type": ActionType.POSTURE,
        "description": "Lift foreleg with leg_index, ht, time_uni, time_acc parameters",
    },
    "backleg_lift": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "backleg_lift",
        "type": ActionType.POSTURE,
        "description": "Lift back leg with leg_index, ht, time_uni, time_acc parameters",
    },
    "rotate": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "rotate",
        "type": ActionType.ROTATION,
        "description": "Rotate by angle parameter",
    },
    "bowback": {
        "sleep_time": DEFAULT_ACTION_SLEEP_TIME,
        "name": "bowback",
        "type": ActionType.POSTURE,
        "description": "Bow head and move back with angle parameter",
    },
    # Complex movements (Level 3)
    "body_cycle": {
        "sleep_time": 8.0,  # Longer for complex movement
        "name": "body_cycle",
        "type": ActionType.SPECIAL,
        "description": "Draw circle with body center while keeping orientation",
    },
    "head_ellipse": {
        "sleep_time": 8.0,  # Longer for complex movement
        "name": "head_ellipse",
        "type": ActionType.SPECIAL,
        "description": "Draw ellipse trajectory with head movement",
    },
}

# Idle action state
idle_action: Dict[str, Any] = {"name": None, "sleep_time": 0, "type": ActionType.IDLE}


class DogActionExecutor:
    """
    Enhanced action executor for dog robots with improved API integration.

    This class manages a queue of actions to be executed on the dog robot,
    using only the local network_action_server HTTP API.
    """

    def __init__(
        self,
        robot_name: str,
        simulator_endpoint: str = "",
        session_key: str = "",
        network_server_base: Optional[str] = None,
    ) -> None:
        """
        Initialize the DogActionExecutor.

        Args:
            robot_name: Name/ID of the robot
            simulator_endpoint: Optional simulator endpoint for dual control
            session_key: Optional session key for simulator
            robot_ip: IP address of the physical robot
            robot_port: UDP port for robot communication
        """
        self.robot_name = robot_name
        self.simulator_endpoint = simulator_endpoint
        self.session_key = session_key
        self.logger = logging.getLogger(__name__)
        # Legacy variable retained for backward compatibility (no effect now)
        self._walking_mode_enabled = False

        # Always use network HTTP now
        self.use_network_http = True
        if network_server_base:
            self.network_server_base = network_server_base.rstrip("/")
        else:
            self.network_server_base = (
                f"http://{NETWORK_SERVER_HOST}:{NETWORK_SERVER_PORT}"
            )
        self.logger.info(
            f"DogActionExecutor operating in HTTP-only mode -> {self.network_server_base}"
        )

        # Queue and threading setup
        self.action_queue: queue.Queue = queue.Queue()
        self.current_action: Dict[str, Any] = idle_action.copy()
        self.is_running: bool = False
        self._immediate_stop_event = threading.Event()
        self.queue_lock = threading.Lock()
        self._stop_event = threading.Event()

        # Action execution statistics
        self.execution_stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "last_action_time": None,
        }

        # Start consumer thread
        self.consumer_thread = threading.Thread(target=self._consumer, daemon=True)
        self.consumer_thread.start()

        self.logger.info(f"DogActionExecutor initialized for robot: {robot_name}")

    def _execute_dog_action(
        self, action_name: str, parameters: Dict[str, Any] = None
    ) -> bool:
        """Execute an action using the network_action_server HTTP API.

        Args:
            action_name: Name of the action to execute
            parameters: Optional parameters for the action

        Returns:
            True if action executed successfully, False otherwise
        """
        return self._execute_via_network_server(action_name, parameters or {})

    # ------------------------------------------------------------------
    # Network Action Server HTTP integration
    # ------------------------------------------------------------------
    def _map_action_to_network(
        self, action_name: str, parameters: Optional[Dict[str, Any]]
    ) -> tuple[str, float, Dict[str, Any]]:
        """Map local executor action to network_action_server semantics.

        Returns a tuple of (network_action, duration, network_parameters).
        Duration may be 0 if not time-based.
        """
        params = parameters or {}
        duration = params.get(
            "duration", actions.get(action_name, {}).get("sleep_time", 2.0)
        )

        # Direct mapping - all actions correspond to MovementGroups methods
        network_action = action_name

        network_params: Dict[str, Any] = {}
        # Build parameters based on action type

        # Rotation actions
        if network_action == "rotate":
            angle = (parameters or {}).get("angle")
            if angle is None:
                # Derive a nominal angle from duration * 30 deg/s
                angle = duration * 30.0
            network_params = {"angle": angle}

        # Height/hop movements
        elif network_action == "height_move":
            ht = (parameters or {}).get("ht", 0.02)
            network_params = {
                "ht": ht,
                "time_uni": min(duration, 2.0),
                "time_acc": min(duration * 0.3, 1.0),
            }

        # Bowback movement
        elif network_action == "bowback":
            angle = (parameters or {}).get("angle", 15)
            network_params = {"angle": angle}

        # Head movements with parameters
        elif network_action == "head_move":
            pitch_deg = (parameters or {}).get("pitch_deg", 0)
            yaw_deg = (parameters or {}).get("yaw_deg", 0)
            time_uni = (parameters or {}).get("time_uni", duration)
            time_acc = (parameters or {}).get("time_acc", min(duration * 0.3, 1.0))
            network_params = {
                "pitch_deg": pitch_deg,
                "yaw_deg": yaw_deg,
                "time_uni": time_uni,
                "time_acc": time_acc,
            }

        # Body row/tilt movements
        elif network_action == "body_row":
            row_deg = (parameters or {}).get("row_deg", 0)
            time_uni = (parameters or {}).get("time_uni", duration)
            time_acc = (parameters or {}).get("time_acc", min(duration * 0.3, 1.0))
            network_params = {
                "row_deg": row_deg,
                "time_uni": time_uni,
                "time_acc": time_acc,
            }

        # Balance movements
        elif network_action == "balance":
            roll_deg = (parameters or {}).get("roll_deg", 0)
            pitch_deg = (parameters or {}).get("pitch_deg", 0)
            time_uni = (parameters or {}).get("time_uni", duration)
            time_acc = (parameters or {}).get("time_acc", min(duration * 0.3, 1.0))
            network_params = {
                "roll_deg": roll_deg,
                "pitch_deg": pitch_deg,
                "time_uni": time_uni,
                "time_acc": time_acc,
            }

        # Gait movements with velocity parameters
        elif network_action == "gait_uni":
            v_x = (parameters or {}).get("v_x", 0)
            v_y = (parameters or {}).get("v_y", 0)
            time_uni = (parameters or {}).get("time_uni", duration)
            time_acc = (parameters or {}).get("time_acc", min(duration * 0.3, 1.0))
            network_params = {
                "v_x": v_x,
                "v_y": v_y,
                "time_uni": time_uni,
                "time_acc": time_acc,
            }

        # Leg lift movements
        elif network_action in ["foreleg_lift", "backleg_lift"]:
            leg_index = (parameters or {}).get("leg_index", "left")
            ht = (parameters or {}).get("ht", 0.01)
            time_uni = (parameters or {}).get("time_uni", duration)
            time_acc = (parameters or {}).get("time_acc", min(duration * 0.3, 1.0))
            network_params = {
                "leg_index": leg_index,
                "ht": ht,
                "time_uni": time_uni,
                "time_acc": time_acc,
            }

        # Stop action with time parameter
        elif network_action == "stop":
            network_params = {"time": duration}

        # All other actions (look_*, move_*, body_cycle, head_ellipse) - no parameters needed
        # They use their built-in defaults

        return network_action, duration, network_params

    def _execute_via_network_server(
        self, action_name: str, parameters: Optional[Dict[str, Any]]
    ) -> bool:
        """Execute an action by calling the local network_action_server HTTP API.
        Returns True if the HTTP request succeeded (action queued), False otherwise.
        """
        try:
            network_action, duration, network_params = self._map_action_to_network(
                action_name, parameters
            )
            payload = {
                "action": network_action,
                "duration": float(duration),
                "parameters": network_params,
            }
            url = f"{self.network_server_base}/execute"
            self.logger.debug(
                f"HTTP executing via network server: {url} payload={payload}"
            )
            resp = requests.post(url, json=payload, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    self.logger.info(
                        f"Queued network server action '{network_action}' (mapped from '{action_name}')"
                    )
                    return True
                else:
                    self.logger.warning(
                        f"Network server responded without success: {data}"
                    )
            else:
                self.logger.warning(
                    f"Network server HTTP {resp.status_code}: {resp.text}"
                )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP request error for action '{action_name}': {e}")
            return False
        except (ValueError, TypeError) as e:
            self.logger.error(f"Parameter error in network server execution: {e}")
            return False
        except RuntimeError as e:
            self.logger.error(f"Runtime error in network server execution: {e}")
            return False

    # Deliberately allow unexpected exceptions to propagate for visibility (no broad catch)

    def _stop_dog_action(self) -> bool:
        """Issue an immediate stop via the network_action_server."""
        try:
            resp = requests.post(f"{self.network_server_base}/stop", timeout=2.0)
            if resp.status_code == 200:
                self.logger.info("Network server stop issued successfully")
                return True
            self.logger.warning(
                f"Failed to stop via network server: {resp.status_code} {resp.text}"
            )
            return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Stop request error: {e}")
            return False

    def _execute_action(self, action_item: Dict[str, Any]) -> None:
        """
        Execute a single action from the queue.

        Args:
            action_item: Dictionary containing action details and parameters
        """
        action_name = action_item["name"]
        action_config = actions[action_name]

        # Update current action status
        self.current_action = {
            "name": action_config["name"],
            "sleep_time": action_config["sleep_time"],
            "type": action_config["type"],
            "start_time": time.time(),
        }

        success = False
        try:
            # Update statistics
            self.execution_stats["total_actions"] += 1
            self.execution_stats["last_action_time"] = time.time()

            # Get parameters from action item
            parameters = action_item.get("parameters", {})

            # Execute the action using dog controller
            success = self._execute_dog_action(action_name, parameters)

            # Also send to simulator if configured
            if self.simulator_endpoint and success:
                self._send_to_simulator(action_name)

            if success:
                self.execution_stats["successful_actions"] += 1
            else:
                self.execution_stats["failed_actions"] += 1

            # Wait for action completion with interrupt capability
            sleep_time = action_config["sleep_time"]

            # Override sleep time if duration is specified in parameters
            if "duration" in parameters:
                sleep_time = parameters["duration"]

            elapsed = 0.0
            while elapsed < sleep_time:
                if self._immediate_stop_event.is_set():
                    self.logger.info(f"Stopping action execution for {action_name}")
                    self._immediate_stop_event.clear()
                    self._stop_dog_action()
                    break
                time.sleep(0.1)
                elapsed += 0.1

        except (ValueError, TypeError) as e:
            self.logger.error(f"Parameter error executing action {action_name}: {e}")
        except RuntimeError as e:
            self.logger.error(f"Runtime error executing action {action_name}: {e}")
        # Omit broad catch to satisfy strict linting
        finally:
            # Clean up
            self._remove_action_by_id(action_item["id"])
            self.current_action = idle_action.copy()

            # Log execution result
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(f"Action {action_name} completed: {status}")

    def _remove_action_by_id(self, action_id: str) -> None:
        """Remove an action from the queue by its ID."""
        with self.queue_lock:
            temp_list = list(self.action_queue.queue)
            filtered = [item for item in temp_list if item["id"] != action_id]
            self._replace_queue(filtered)

    def _replace_queue(self, items: list) -> None:
        """Replace the current queue with a new list of items."""
        self.action_queue.queue.clear()
        for item in items:
            self.action_queue.put(item)

    def _consumer(self) -> None:
        """
        Continuously consume actions from the queue and execute them.

        This method runs in a separate thread and processes actions sequentially.
        """
        self.logger.info("Action consumer thread started")

        # Align to 5-second boundary for consistent timing
        time.sleep(5 - time.time() % 5)

        while not self._stop_event.is_set():
            try:
                # Check for immediate stop
                if self._immediate_stop_event.is_set():
                    self.logger.info(
                        "Immediate stop triggered, clearing queue and setting to idle"
                    )
                    self.clear_action_queue()
                    self.current_action = idle_action.copy()
                    self.is_running = False
                    self._immediate_stop_event.clear()
                    time.sleep(0.5)
                    continue

                # Align to 1-second boundary for consistent timing
                time.sleep(1 - time.time() % 1)

                # Try to get an action from the queue
                try:
                    action_item = self.action_queue.get(timeout=1)
                    self.is_running = True
                    self._execute_action(action_item)
                    time.sleep(0.5)  # Brief pause between actions
                except queue.Empty:
                    self.is_running = False
                    time.sleep(0.5)

            except (ValueError, TypeError) as e:
                self.logger.error(f"Parameter error in consumer thread: {e}")
                self.is_running = False
                time.sleep(1)
            except RuntimeError as e:
                self.logger.error(f"Runtime error in consumer thread: {e}")
                self.is_running = False
                time.sleep(1)
            # Broad exceptions intentionally not caught to allow visibility

        self.logger.info("Action consumer thread stopped")

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.

        Returns:
            Dictionary containing execution statistics
        """
        stats = self.execution_stats.copy()
        if stats["total_actions"] > 0:
            stats["success_rate"] = (
                stats["successful_actions"] / stats["total_actions"]
            ) * 100
        else:
            stats["success_rate"] = 0.0
        return stats

    def get_available_actions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available actions with their configurations.

        Returns:
            Dictionary of available actions and their configurations
        """
        return actions.copy()

    def add_action_to_queue(
        self, action_name: str, parameters: Dict[str, Any] = None
    ) -> str:
        """
        Add a new action to the queue.

        Args:
            action_name: Name of the action to execute
            parameters: Optional parameters for the action

        Returns:
            Action ID for tracking purposes
        """
        action_id = str(uuid4())

        # Handle special stop action
        if action_name == "stop":
            self.stop()
            return action_id

        # Validate action name
        if action_name not in actions:
            available_actions = list(actions.keys())
            self.logger.error(
                f"Action '{action_name}' not found. Available actions: {available_actions}"
            )
            raise ValueError(f"Unknown action: {action_name}")

        # Validate and process parameters
        processed_parameters = self._process_parameters(action_name, parameters or {})

        with self.queue_lock:
            action_item = {
                "id": action_id,
                "name": action_name,
                "parameters": processed_parameters,
                "timestamp": time.time(),
                "type": actions[action_name]["type"],
            }

            self.action_queue.put(action_item)

        self.logger.info(f"Action '{action_name}' added to queue with ID: {action_id}")
        return action_id

    def _process_parameters(
        self, action_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and validate parameters for an action.

        Args:
            action_name: Name of the action
            parameters: Raw parameters

        Returns:
            Processed and validated parameters
        """
        processed = parameters.copy()
        action_config = actions[action_name]

        # Set default speed if not provided
        if "speed" not in processed and "default_speed" in action_config:
            processed["speed"] = action_config["default_speed"]

        # Validate speed parameter
        if "speed" in processed:
            processed["speed"] = max(0.1, min(1.0, float(processed["speed"])))

        # Validate duration parameter
        if "duration" in processed:
            processed["duration"] = max(0.1, float(processed["duration"]))

        # Handle distance parameter for movement actions
        if "distance" in processed and action_config["type"] == "movement":
            distance = abs(float(processed["distance"]))
            processed["distance"] = distance
            # Convert distance to duration if not specified
            if "duration" not in processed:
                processed["duration"] = min(5.0, max(0.5, distance / 50.0))

        # Handle angle parameter for rotation actions
        if "angle" in processed and action_config["type"] == "rotation":
            angle = abs(float(processed["angle"]))
            processed["angle"] = angle
            # Convert angle to duration if not specified
            if "duration" not in processed:
                processed["duration"] = min(5.0, max(0.5, angle / 90.0))

        return processed

    def remove_action_from_queue(self, action_id: str) -> None:
        """Remove an action from the queue by its ID."""
        self._remove_action_by_id(action_id)

    def clear_action_queue(self) -> None:
        """Clear all actions from the queue."""
        with self.queue_lock:
            self.action_queue.queue.clear()

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of the action queue.

        Returns:
            Dictionary containing queue status information
        """
        with self.queue_lock:
            queue_items = list(self.action_queue.queue)

        return {
            "queue": queue_items,
            "queue_size": len(queue_items),
            "current_action": self.current_action,
            "is_running": self.is_running,
            "robot_status": self._fetch_network_status(),
            "execution_stats": self.get_execution_stats(),
        }

    def stop(self) -> None:
        """
        Stop all actions immediately and clear the queue.

        This method triggers an immediate stop of the current action
        and clears all pending actions from the queue while preserving walking mode.
        """
        self.logger.info(
            "Immediate stop requested: clearing queue and interrupting current action"
        )
        self._immediate_stop_event.set()
        self.clear_action_queue()

        # Issue network server stop
        self._stop_dog_action()

    def _fetch_network_status(self) -> Optional[Dict[str, Any]]:
        """Fetch status from network_action_server /status endpoint."""
        try:
            resp = requests.get(f"{self.network_server_base}/status", timeout=2.0)
            if resp.status_code == 200:
                return resp.json()
            return {"error": f"status_http_{resp.status_code}"}
        except requests.exceptions.RequestException:
            return {"error": "status_request_failed"}

    def shutdown(self) -> None:
        """
        Gracefully shutdown the action executor.

        This method stops the consumer thread and cleans up resources.
        """
        self.logger.info("Shutting down action executor...")

        # Stop the consumer thread
        self._stop_event.set()

        # Clear any remaining actions
        self.clear_action_queue()

        # Stop current action
        self.stop()

        # Wait for consumer thread to finish
        if self.consumer_thread.is_alive():
            self.consumer_thread.join(timeout=5)
            if self.consumer_thread.is_alive():
                self.logger.warning("Consumer thread did not shut down gracefully")

        self.logger.info("Action executor shutdown complete")

    def pause_execution(self) -> None:
        """Pause action execution without clearing the queue."""
        self._immediate_stop_event.set()
        self.logger.info("Action execution paused")

    def resume_execution(self) -> None:
        """Resume action execution."""
        self._immediate_stop_event.clear()
        self.logger.info("Action execution resumed")

    def _send_to_simulator(
        self,
        action_name: str,
        parameters: Dict[str, Any] = None,
        log_success_msg: str = None,
        log_error_msg: str = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send an action command to the robot simulator (optional dual control).

        Args:
            action_name: The name of the action to execute
            parameters: Optional action parameters
            log_success_msg: Message to log on successful API call
            log_error_msg: Message to log on failed API call

        Returns:
            Optional response data from the simulator API call
        """
        if not self.simulator_endpoint:
            return None

        if log_success_msg is None:
            log_success_msg = (
                f"Simulator action {action_name} for robot {self.robot_name} successful"
            )
        if log_error_msg is None:
            log_error_msg = f"Error sending action {action_name} to simulator for robot {self.robot_name}"

        # Construct the URL
        url = f"{self.simulator_endpoint}/run_action/{self.robot_name}"
        if self.session_key:
            url += f"?session_key={self.session_key}"

        # Prepare the payload
        payload = {"action": action_name}
        if parameters:
            payload["parameters"] = parameters

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=3.0,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            resp_json = response.json()
            self.logger.info(
                f"{self.robot_name} - {log_success_msg}. Response: {resp_json}"
            )
            return resp_json
        except requests.exceptions.RequestException as e:
            self.logger.error(f"{log_error_msg}: {e}")
            return None


# Legacy compatibility - alias for backward compatibility
ActionExecutor = DogActionExecutor
