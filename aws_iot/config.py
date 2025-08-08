"""
Configuration module for dog robot control system.

This module centralizes all configuration constants, default values,
and settings used throughout the dog robot control system.
"""

# Network Configuration
NETWORK_SERVER_HOST = "127.0.0.1"  # Local network_action_server host
NETWORK_SERVER_PORT = 8080  # Local network_action_server port

# Movement Parameters
MIN_SPEED = 0.1
MAX_SPEED = 1.0
MIN_DURATION = 0.1
MAX_DURATION = 10.0

# Action Configuration
DEFAULT_ACTION_SLEEP_TIME = 2.0
STOP_ACTION_SLEEP_TIME = 0.5

# Thread Configuration
CONSUMER_SLEEP_INTERVAL = 0.1
THREAD_JOIN_TIMEOUT = 5.0


# Action Type Definitions
class ActionType:
    MOVEMENT = "movement"
    ROTATION = "rotation"
    POSTURE = "posture"
    STATUS = "status"
    CONTROL = "control"
    SPECIAL = "special"
    IDLE = "idle"
