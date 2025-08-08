"""
Configuration module for dog robot control system.

This module centralizes all configuration constants, default values,
and settings used throughout the dog robot control system.
"""

from typing import Any, Dict

# Network Configuration
DEFAULT_ROBOT_IP = "127.255.255.255"
DEFAULT_ROBOT_PORT = 8830
DEFAULT_MESSAGE_RATE = 20
UDP_TIMEOUT = 0.2
CONNECTION_TIMEOUT = 5
NETWORK_SERVER_HOST = "127.0.0.1"  # Local network_action_server host
NETWORK_SERVER_PORT = 8080  # Local network_action_server port

# Movement Parameters
DEFAULT_SPEED = 0.5
MIN_SPEED = 0.1
MAX_SPEED = 1.0
MIN_DURATION = 0.1
MAX_DURATION = 10.0
DEFAULT_HOP_DURATION = 1.0

# Action Configuration
DEFAULT_ACTION_SLEEP_TIME = 2.0
STOP_ACTION_SLEEP_TIME = 0.5
HOP_ACTION_SLEEP_TIME = 1.5
STATUS_ACTION_SLEEP_TIME = 1.0

# Thread Configuration
CONSUMER_SLEEP_INTERVAL = 0.1
ACTION_PAUSE_INTERVAL = 0.5
THREAD_JOIN_TIMEOUT = 5.0

# Parameter Conversion
DISTANCE_TO_DURATION_SCALE = 50.0  # pixels per second
ANGLE_TO_DURATION_SCALE = 90.0  # degrees per second

# UDP Command Template
BASE_COMMAND_TEMPLATE: Dict[str, Any] = {
    "lx": 0.0,  # Left stick X axis (-1.0 to 1.0)
    "ly": 0.0,  # Left stick Y axis (-1.0 to 1.0)
    "rx": 0.0,  # Right stick X axis (-1.0 to 1.0)
    "ry": 0.0,  # Right stick Y axis (-1.0 to 1.0)
    "x": 0,  # X button (0 or 1)
    "square": 0,  # Square button (0 or 1)
    "circle": 0,  # Circle button (0 or 1)
    "triangle": 0,  # Triangle button (0 or 1)
    "dpadx": 0,  # D-pad X axis (-1.0 to 1.0)
    "dpady": 0,  # D-pad Y axis (-1.0 to 1.0)
    "L1": 0,  # L1 button (0 or 1) - Activation toggle
    "R1": 0,  # R1 button (0 or 1) - Walking mode toggle
    "L2": 0,  # L2 button (0 or 1)
    "R2": 0,  # R2 button (0 or 1)
    "message_rate": DEFAULT_MESSAGE_RATE,
}


# Action Type Definitions
class ActionType:
    MOVEMENT = "movement"
    ROTATION = "rotation"
    POSTURE = "posture"
    STATUS = "status"
    CONTROL = "control"
    SPECIAL = "special"
    IDLE = "idle"


# Control Mappings
CONTROL_MAPPINGS = {
    # Movement controls
    "forward": {"axis": "ly", "value": 1.0},
    "backward": {"axis": "ly", "value": -1.0},
    "left": {"axis": "lx", "value": -1.0},
    "right": {"axis": "lx", "value": 1.0},
    # Rotation controls
    "rotate_left": {"axis": "dpadx", "value": 1.0},
    "rotate_right": {"axis": "dpadx", "value": -1.0},
    # Posture controls
    "stand_up": {"axis": "dpady", "value": 1.0},
    "lay_down": {"axis": "dpady", "value": -1.0},
    # Button controls
    "hop": {"button": "x", "value": 1},
    "activate": {"button": "L1", "value": 1},
    "walk_mode": {"button": "R1", "value": 1},
    "dance_mode": {"button": "circle", "value": 1},
}

# Logging Configuration
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_LEVEL = "INFO"

# Error Messages
ERROR_MESSAGES = {
    "controller_init_failed": "Failed to initialize dog controller",
    "action_not_found": "Action '{}' not found. Available actions: {}",
    "invalid_speed": "Speed must be between {} and {}",
    "invalid_duration": "Duration must be between {} and {}",
    "udp_send_failed": "Failed to send UDP command",
    "thread_shutdown_failed": "Consumer thread did not shut down gracefully",
}


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max bounds."""
    return max(min_val, min(max_val, value))


def validate_speed(speed: float) -> float:
    """Validate and clamp speed parameter."""
    return clamp_value(speed, MIN_SPEED, MAX_SPEED)


def validate_duration(duration: float) -> float:
    """Validate and clamp duration parameter."""
    return clamp_value(duration, MIN_DURATION, MAX_DURATION)


def distance_to_duration(distance: float) -> float:
    """Convert distance to duration."""
    return clamp_value(
        abs(distance) / DISTANCE_TO_DURATION_SCALE, MIN_DURATION, MAX_DURATION
    )


def angle_to_duration(angle: float) -> float:
    """Convert angle to duration."""
    return clamp_value(abs(angle) / ANGLE_TO_DURATION_SCALE, MIN_DURATION, MAX_DURATION)
