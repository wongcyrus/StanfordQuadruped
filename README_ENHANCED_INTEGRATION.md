# Enhanced Dog Action Integration

This directory contains an enhanced network-based integration for controlling Stanford Quadruped Mini Pupper robots remotely. It provides a robust HTTP API that replaces the original UDP-based communication with better error handling, action queuing, and status monitoring.

## 🚀 Quick Start

### For Robot (Mini Pupper) Setup

1. **Deploy to robot automatically:**
   ```bash
   python deploy_enhanced_dog_action.py --robot-ip 10.0.0.10
   ```

2. **Or manually copy files and setup:**
   ```bash
   # Copy files to robot
   scp network_action_server.py ubuntu@10.0.0.10:/home/ubuntu/StanfordQuadruped/
   scp setup_enhanced_network_server.py ubuntu@10.0.0.10:/home/ubuntu/
   
   # SSH to robot and setup
   ssh ubuntu@10.0.0.10
   sudo python3 setup_enhanced_network_server.py
   ```

3. **Verify the service is running:**
   ```bash
   curl http://10.0.0.10:8080/status
   ```

### For PC Client Setup

1. **Update your dog action import:**
   ```python
   # In your main.py or choreography script
   from actions.enhanced_dog_action import DogAction
   
   # Or keep using the existing import (auto-detects enhanced version)
   from actions.dog_action import DogAction
   ```

2. **Configure for network communication:**
   ```python
   dog_action = DogAction(
       action_name_to_time=action_times,
       action_name_to_repeat_time=repeat_times,
       dog_id="dog_1",
       robot_ip="10.0.0.10",  # Robot's network IP
       robot_port=8080,       # API port, not UDP port
   )
   ```

## 📁 Files Overview

### Robot Side Files
- **`network_action_server.py`** - HTTP API server that runs on the robot
- **`setup_enhanced_network_server.py`** - Setup script for robot installation
- **`start_network_server.sh`** - Generated start script for manual operation

### PC Client Side Files
- **`enhanced_dog_action.py`** - Enhanced dog action implementation with network support
- **`dog_action.py`** - Updated to auto-detect and use enhanced version when available
- **`deploy_enhanced_dog_action.py`** - Deployment script for easy setup

### Documentation
- **`ENHANCED_DOG_ACTION_INTEGRATION.md`** - Detailed integration documentation
- **`README.md`** - This file

## 🔧 Key Features

### Enhanced Network Communication
- ✅ **RESTful HTTP API** instead of direct UDP manipulation
- ✅ **Reliable error handling** with proper status codes
- ✅ **Connection health monitoring** with automatic reconnection
- ✅ **Action parameter optimization** based on duration and context

### Better Action Management
- ✅ **Action queuing** for sequential execution
- ✅ **Real-time status monitoring** of robot state
- ✅ **Emergency stop** functionality
- ✅ **Action name mapping** for compatibility with existing choreography

### Improved Reliability
- ✅ **Connection timeout management**
- ✅ **Graceful degradation** when robot is unreachable
- ✅ **Detailed logging** for debugging
- ✅ **Status feedback** for better monitoring

### Backwards Compatibility
- ✅ **Drop-in replacement** for existing DogAction class
- ✅ **Same interface** for existing choreography scripts
- ✅ **Automatic parameter conversion** from legacy settings

## 🌐 Network Architecture

```
┌─────────────────────────────────┐    HTTP API     ┌──────────────────────────────────┐
│ PC (Robot Group Action Planner) │ ◄─────────────► │ Mini Pupper Robot                │
│                                 │  (Port 8080)    │                                  │
│ • enhanced_dog_action.py        │                 │ • network_action_server.py       │
│ • Choreography scripts          │                 │ • Stanford Quadruped Control     │
│ • Action planning               │                 │ • Hardware interface             │
└─────────────────────────────────┘                 └──────────────────────────────────┘
```

### Communication Flow
1. **PC Client** sends HTTP POST request with action details
2. **Network Action Server** receives and validates the request
3. **Action Queue** manages sequential execution of actions
4. **UDP Bridge** converts HTTP commands to Stanford Quadruped UDP format
5. **Robot Control** executes the physical movements
6. **Status Updates** are sent back to the PC client

## 📡 API Quick Reference

### Base URL
```
http://10.0.0.10:8080
```

### Essential Endpoints

**Get Status:**
```bash
curl http://10.0.0.10:8080/status
```

**Execute Action:**
```bash
curl -X POST http://10.0.0.10:8080/execute \
     -H "Content-Type: application/json" \
     -d '{"action": "forward", "duration": 3.0}'
```

**Emergency Stop:**
```bash
curl -X POST http://10.0.0.10:8080/stop
```

**List Available Actions:**
```bash
curl http://10.0.0.10:8080/actions
```

## 🎭 Action Mapping

The enhanced system automatically maps common action names to robot commands:

| Choreography Action | Robot Command | Description |
|-------------------|---------------|-------------|
| `walk_forward` | `forward` | Move forward |
| `walk_backward` | `backward` | Move backward |
| `turn_left` | `turn_left` | Rotate counter-clockwise |
| `turn_right` | `turn_right` | Rotate clockwise |
| `stand_up` | `activate` | Activate and stand |
| `start_dance` | `dance` | Enable dance mode |
| `jump` | `hop` | Jump/hop movement |

## 🔨 Installation Options

### Option 1: Automated Deployment (Recommended)

Use the deployment script for easy setup:

```bash
# Basic deployment
python deploy_enhanced_dog_action.py

# Custom robot IP
python deploy_enhanced_dog_action.py --robot-ip 192.168.1.100

# Skip systemd service installation
python deploy_enhanced_dog_action.py --no-service

# Update local configuration only
python deploy_enhanced_dog_action.py --local-only
```

### Option 2: Manual Installation

**On the Robot:**
```bash
# Copy files
scp network_action_server.py ubuntu@10.0.0.10:/home/ubuntu/StanfordQuadruped/
scp setup_enhanced_network_server.py ubuntu@10.0.0.10:/home/ubuntu/

# SSH and setup
ssh ubuntu@10.0.0.10
sudo python3 setup_enhanced_network_server.py

# Verify installation
sudo systemctl status quadruped-network-server
curl http://localhost:8080/status
```

**On the PC:**
```python
# Update your robot configuration
from actions.enhanced_dog_action import DogAction

dog_action = DogAction(
    action_name_to_time=your_action_times,
    robot_ip="10.0.0.10",
    robot_port=8080
)
```

## 🛠️ Troubleshooting

### Connection Issues

**Problem:** Cannot connect to robot
```bash
# Check network connectivity
ping 10.0.0.10

# Check SSH access
ssh ubuntu@10.0.0.10

# Check service status
ssh ubuntu@10.0.0.10 "sudo systemctl status quadruped-network-server"
```

**Problem:** API not responding
```bash
# Check if service is running
curl -v http://10.0.0.10:8080/status

# Check robot logs
ssh ubuntu@10.0.0.10 "sudo journalctl -u quadruped-network-server -f"

# Restart service
ssh ubuntu@10.0.0.10 "sudo systemctl restart quadruped-network-server"
```

### Action Execution Issues

**Problem:** Actions not working
```python
# Check robot status from Python
status = dog_action.get_robot_status()
print(f"Connected: {status.get('connected')}")
print(f"Available actions: {status.get('available_actions')}")

# Test emergency stop
dog_action.emergency_stop()

# Clear action queue
dog_action.clear_action_queue()
```

### Performance Issues

**Problem:** Slow response times
```python
# Adjust timeout settings
dog_action = DogAction(
    ...,
    connection_timeout=10.0,  # Increase for slow networks
    action_timeout=60.0       # Increase for long actions
)
```

**Problem:** Robot movements are jerky
```python
# Use smoother parameters
dog_action.execute_action("forward", duration=5.0, parameters={"ly": 0.6})
```

## 📈 Advanced Usage

### Custom Action Parameters
```python
# Slow, precise movement
dog_action.execute_action("forward", duration=5.0, parameters={"ly": 0.5})

# Fast, aggressive turn
dog_action.execute_action("turn_left", duration=1.0, parameters={"rx": 1.0})

# Complex sequence with status monitoring
actions = [("stand_up", 2.0), ("forward", 3.0), ("turn_left", 2.0)]
for action_name, duration in actions:
    if not dog_action._execute_single_action(action_name):
        print(f"Failed: {action_name}")
        break
    print(f"Completed: {action_name}")
```

### Integration with Existing Choreography
```python
# Use enhanced features in existing code
def enhanced_dance_routine():
    # Check robot status first
    if not dog_action.get_robot_status().get('connected'):
        print("Robot not available")
        return False
    
    # Execute dance with better error handling
    try:
        dance_actions = load_dance_from_spreadsheet()
        for action in dance_actions:
            success = dog_action._execute_single_action(action.name, action.duration)
            if not success:
                dog_action.emergency_stop()
                return False
        return True
    except Exception as e:
        print(f"Dance failed: {e}")
        dog_action.emergency_stop()
        return False
```

### Status Monitoring
```python
import time

def monitor_robot_status():
    while True:
        status = dog_action.get_robot_status()
        if status.get('connected'):
            queue_info = status.get('queue_status', {})
            current_action = queue_info.get('current_action')
            if current_action:
                print(f"Executing: {current_action.get('name')} ({current_action.get('status')})")
            else:
                print("Robot idle")
        else:
            print("Robot disconnected")
        time.sleep(1)
```

## 🔮 Future Enhancements

### Planned Features
- **WebSocket support** for real-time status streaming
- **Action recording and playback** for complex choreography
- **Multi-robot coordination** for group performances
- **Visual feedback integration** with camera feed
- **Voice command integration** via speech recognition

### Extensibility Points
The enhanced system is designed for easy extension:

- **Custom Action Types:** Add new action categories beyond movement/posture
- **Parameter Validation:** Implement action-specific parameter validation
- **Logging Integration:** Enhanced logging with structured data
- **Metrics Collection:** Performance and usage metrics
- **Security Features:** Authentication and authorization for API access

## 📞 Support

For issues and questions:

1. **Check the logs:** Both on robot (`journalctl -u quadruped-network-server`) and PC
2. **Test connectivity:** Use `curl` commands to test API endpoints
3. **Verify configuration:** Ensure IP addresses and ports are correct
4. **Review documentation:** See `ENHANCED_DOG_ACTION_INTEGRATION.md` for details

## 🎉 Success! 

If you've made it this far, you should now have:

- ✅ Enhanced network action server running on your robot
- ✅ Improved dog action integration on your PC
- ✅ Better error handling and status monitoring
- ✅ Backwards compatibility with existing choreography
- ✅ Tools for easy deployment and troubleshooting

Enjoy your enhanced robot control experience! 🤖✨
