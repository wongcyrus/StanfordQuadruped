"""
Utility functions for the dog robot control system.

This module provides common utility functions used across the dog robot
control system, including parameter validation, conversion functions,
and helper methods.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable

from config import (
    MIN_SPEED, MAX_SPEED, MIN_DURATION, MAX_DURATION,
    CONSUMER_SLEEP_INTERVAL, THREAD_JOIN_TIMEOUT
)

logger = logging.getLogger(__name__)


class ParameterValidator:
    """Utility class for parameter validation and conversion."""
    
    @staticmethod
    def validate_speed(speed: float) -> float:
        """Validate and clamp speed parameter."""
        if not isinstance(speed, (int, float)):
            raise ValueError(f"Speed must be a number, got {type(speed)}")
        return max(MIN_SPEED, min(MAX_SPEED, float(speed)))
    
    @staticmethod
    def validate_duration(duration: float) -> float:
        """Validate and clamp duration parameter."""
        if not isinstance(duration, (int, float)):
            raise ValueError(f"Duration must be a number, got {type(duration)}")
        return max(MIN_DURATION, min(MAX_DURATION, float(duration)))
    
    @staticmethod
    def validate_axis_value(value: float) -> float:
        """Validate and clamp axis values to [-1.0, 1.0] range."""
        if not isinstance(value, (int, float)):
            raise ValueError(f"Axis value must be a number, got {type(value)}")
        return max(-1.0, min(1.0, float(value)))
    
    @staticmethod
    def validate_button_value(value: int) -> int:
        """Validate button values to be 0 or 1."""
        if not isinstance(value, (int, bool)):
            raise ValueError(f"Button value must be int or bool, got {type(value)}")
        return 1 if value else 0


class ThreadManager:
    """Utility class for managing threads safely."""
    
    @staticmethod
    def safe_thread_join(thread: threading.Thread, timeout: float = THREAD_JOIN_TIMEOUT) -> bool:
        """
        Safely join a thread with timeout.
        
        Args:
            thread: Thread to join
            timeout: Timeout in seconds
            
        Returns:
            True if thread joined successfully, False if timeout
        """
        if not thread.is_alive():
            return True
            
        thread.join(timeout=timeout)
        if thread.is_alive():
            logger.warning(f"Thread {thread.name} did not shut down within {timeout}s")
            return False
        return True
    
    @staticmethod
    def interruptible_sleep(duration: float, stop_event: threading.Event) -> bool:
        """
        Sleep for duration with ability to be interrupted by stop_event.
        
        Args:
            duration: Sleep duration in seconds
            stop_event: Event to check for interruption
            
        Returns:
            True if completed full duration, False if interrupted
        """
        elapsed = 0.0
        while elapsed < duration:
            if stop_event.is_set():
                return False
            sleep_time = min(CONSUMER_SLEEP_INTERVAL, duration - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
        return True


class ActionValidator:
    """Utility class for validating action parameters."""
    
    @staticmethod
    def validate_action_parameters(action_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and process action parameters.
        
        Args:
            action_name: Name of the action
            parameters: Raw parameters dictionary
            
        Returns:
            Validated and processed parameters
        """
        if not parameters:
            return {}
            
        validated = {}
        validator = ParameterValidator()
        
        # Validate common parameters
        if 'speed' in parameters:
            validated['speed'] = validator.validate_speed(parameters['speed'])
            
        if 'duration' in parameters:
            validated['duration'] = validator.validate_duration(parameters['duration'])
            
        if 'distance' in parameters:
            distance = parameters['distance']
            if not isinstance(distance, (int, float)):
                raise ValueError(f"Distance must be a number, got {type(distance)}")
            validated['distance'] = abs(float(distance))
            
        if 'angle' in parameters:
            angle = parameters['angle']
            if not isinstance(angle, (int, float)):
                raise ValueError(f"Angle must be a number, got {type(angle)}")
            validated['angle'] = abs(float(angle))
        
        # Validate custom movement parameters
        axis_params = ['lx', 'ly', 'rx', 'ry', 'dpadx', 'dpady']
        for param in axis_params:
            if param in parameters:
                validated[param] = validator.validate_axis_value(parameters[param])
        
        # Copy other parameters as-is
        for key, value in parameters.items():
            if key not in validated:
                validated[key] = value
                
        return validated


class CommandBuilder:
    """Utility class for building UDP commands."""
    
    def __init__(self, base_command: Dict[str, Any]):
        """
        Initialize command builder.
        
        Args:
            base_command: Base command template
        """
        self.base_command = base_command.copy()
    
    def build_command(self, **overrides) -> Dict[str, Any]:
        """
        Build a command with specified overrides.
        
        Args:
            **overrides: Parameters to override in base command
            
        Returns:
            Complete command dictionary
        """
        command = self.base_command.copy()
        command.update(overrides)
        return command
    
    def build_movement_command(
        self, 
        lx: float = 0.0, 
        ly: float = 0.0, 
        dpadx: float = 0.0, 
        dpady: float = 0.0
    ) -> Dict[str, Any]:
        """
        Build a movement command.
        
        Args:
            lx: Left stick X axis
            ly: Left stick Y axis
            dpadx: D-pad X axis
            dpady: D-pad Y axis
            
        Returns:
            Movement command dictionary
        """
        validator = ParameterValidator()
        return self.build_command(
            lx=validator.validate_axis_value(lx),
            ly=validator.validate_axis_value(ly),
            dpadx=validator.validate_axis_value(dpadx),
            dpady=validator.validate_axis_value(dpady)
        )
    
    def build_button_command(self, button: str, pressed: bool = True) -> Dict[str, Any]:
        """
        Build a button command.
        
        Args:
            button: Button name
            pressed: Whether button is pressed
            
        Returns:
            Button command dictionary
        """
        validator = ParameterValidator()
        return self.build_command(**{button: validator.validate_button_value(pressed)})


class StatisticsTracker:
    """Utility class for tracking execution statistics."""
    
    def __init__(self):
        """Initialize statistics tracker."""
        self.stats = {
            "total_actions": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "last_action_time": None,
            "action_history": []
        }
        self._lock = threading.Lock()
    
    def record_action_start(self, action_name: str) -> None:
        """Record the start of an action."""
        with self._lock:
            self.stats["total_actions"] += 1
            self.stats["last_action_time"] = time.time()
            self.stats["action_history"].append({
                "action": action_name,
                "start_time": time.time(),
                "status": "started"
            })
    
    def record_action_success(self, action_name: str) -> None:
        """Record successful action completion."""
        with self._lock:
            self.stats["successful_actions"] += 1
            # Update last entry in history
            if self.stats["action_history"]:
                last_action = self.stats["action_history"][-1]
                if last_action["action"] == action_name:
                    last_action["status"] = "success"
                    last_action["end_time"] = time.time()
    
    def record_action_failure(self, action_name: str, error: str = None) -> None:
        """Record failed action."""
        with self._lock:
            self.stats["failed_actions"] += 1
            # Update last entry in history
            if self.stats["action_history"]:
                last_action = self.stats["action_history"][-1]
                if last_action["action"] == action_name:
                    last_action["status"] = "failed"
                    last_action["end_time"] = time.time()
                    if error:
                        last_action["error"] = error
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics."""
        with self._lock:
            stats = self.stats.copy()
            if stats["total_actions"] > 0:
                stats["success_rate"] = (stats["successful_actions"] / stats["total_actions"]) * 100
            else:
                stats["success_rate"] = 0.0
            return stats
    
    def reset_statistics(self) -> None:
        """Reset all statistics."""
        with self._lock:
            self.stats = {
                "total_actions": 0,
                "successful_actions": 0,
                "failed_actions": 0,
                "last_action_time": None,
                "action_history": []
            }


def setup_logging(level: str = "INFO", format_string: str = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level
        format_string: Custom format string
    """
    if format_string is None:
        format_string = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[logging.StreamHandler()]
    )


def retry_on_exception(
    func: Callable, 
    max_retries: int = 3, 
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry a function on exception.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Delay between retries
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries failed
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception