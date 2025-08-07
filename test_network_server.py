#!/usr/bin/env python3
"""
Test script for network_action_server.py to verify it works correctly
"""

import sys
import time

def test_import():
    """Test if the network action server can be imported"""
    try:
        import network_action_server
        print("✓ Successfully imported network_action_server")
        return True
    except Exception as e:
        print(f"✗ Failed to import network_action_server: {e}")
        return False

def test_action_controller():
    """Test if the DogActionController can be instantiated"""
    try:
        from network_action_server import DogActionController
        controller = DogActionController(udp_port=8831)  # Use different port for testing
        print("✓ Successfully created DogActionController")
        
        # Test getting available actions
        actions = controller.available_actions
        print(f"✓ Available actions: {actions}")
        
        # Test getting status
        status = controller.get_status()
        print(f"✓ Status: {status}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to create DogActionController: {e}")
        return False

def test_movement_execution():
    """Test if a simple movement can be executed"""
    try:
        from network_action_server import DogActionController
        controller = DogActionController(udp_port=8832)  # Use different port for testing
        controller.start()
        
        # Test executing a simple action
        success = controller.execute_action("stop", duration=1.0)
        print(f"✓ Action execution queued: {success}")
        
        # Wait a bit for execution
        time.sleep(2)
        
        # Check status
        status = controller.get_status()
        print(f"✓ Final status: {status}")
        
        controller.stop()
        return True
    except Exception as e:
        print(f"✗ Failed to test movement execution: {e}")
        return False

if __name__ == "__main__":
    print("Testing network_action_server.py...")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test 1: Import
    if not test_import():
        all_tests_passed = False
    print()
    
    # Test 2: Action Controller
    if not test_action_controller():
        all_tests_passed = False
    print()
    
    # Test 3: Movement Execution
    if not test_movement_execution():
        all_tests_passed = False
    print()
    
    if all_tests_passed:
        print("🎉 All tests passed! The network action server should work correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("=" * 50)
