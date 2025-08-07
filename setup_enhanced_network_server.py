#!/usr/bin/env python3
"""
Setup script for Enhanced Stanford Quadruped Network Action Server

This script sets up the enhanced network action server on the Mini Pupper robot.
Run this on the robot to enable remote action control via HTTP API.

Usage:
    python setup_enhanced_network_server.py [options]

Requirements:
    - Run on the Mini Pupper robot
    - Stanford Quadruped software installed
    - Network connectivity established
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def check_requirements():
    """Check if the required dependencies are available."""
    print("Checking requirements...")

    # Check if we're on the right system
    if not os.path.exists("/home/ubuntu/StanfordQuadruped"):
        print(
            "ERROR: Stanford Quadruped not found. This script should run on the Mini Pupper robot."
        )
        return False

    # Check Python version
    if sys.version_info < (3, 6):
        print("ERROR: Python 3.6 or newer required")
        return False

    # Check required Python modules
    required_modules = ["requests"]
    missing_modules = []

    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)

    if missing_modules:
        print(f"Installing missing modules: {', '.join(missing_modules)}")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing_modules
            )
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to install modules: {', '.join(missing_modules)}")
            return False

    print("✓ Requirements check passed")
    return True


def install_network_server(source_file=None):
    """Install the network action server."""
    stanford_dir = Path("/home/ubuntu/StanfordQuadruped")
    target_file = stanford_dir / "network_action_server.py"

    if source_file and os.path.exists(source_file):
        print(f"Copying network server from {source_file}")
        shutil.copy2(source_file, target_file)
    else:
        print("Creating network action server...")
        # If source file not provided, we assume it's already in the right place
        # or will be copied manually
        if not target_file.exists():
            print(
                "ERROR: network_action_server.py not found. Please copy it to the robot first."
            )
            return False

    # Make executable
    os.chmod(target_file, 0o755)
    print(f"✓ Network server installed to {target_file}")
    return True


def create_service_file(args):
    """Create systemd service file for the network action server."""
    service_content = f"""[Unit]
Description=Stanford Quadruped Network Action Server
After=network.target
Wants=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/StanfordQuadruped
ExecStart=/usr/bin/python3 /home/ubuntu/StanfordQuadruped/network_action_server.py \\
    --host {args.host} --port {args.port} --udp-port {args.udp_port}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""

    service_file = "/etc/systemd/system/quadruped-network-server.service"

    try:
        with open(service_file, "w") as f:
            f.write(service_content)

        print(f"✓ Service file created: {service_file}")
        return True
    except PermissionError:
        print("ERROR: Permission denied. Run with sudo to create service file.")
        return False


def setup_service(enable_service=True):
    """Setup and optionally enable the systemd service."""
    commands = [
        ["systemctl", "daemon-reload"],
    ]

    if enable_service:
        commands.extend(
            [
                ["systemctl", "enable", "quadruped-network-server.service"],
                ["systemctl", "start", "quadruped-network-server.service"],
            ]
        )

    for cmd in commands:
        try:
            subprocess.check_call(cmd)
            print(f"✓ Executed: {' '.join(cmd)}")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to execute {' '.join(cmd)}: {e}")
            return False

    return True


def create_start_script():
    """Create a convenient start script."""
    start_script_content = """#!/bin/bash
# Start script for Stanford Quadruped Network Action Server

cd /home/ubuntu/StanfordQuadruped

echo "Starting Stanford Quadruped Network Action Server..."
python3 network_action_server.py --host 0.0.0.0 --port 8080 --udp-port 8830 "$@"
"""

    start_script = "/home/ubuntu/StanfordQuadruped/start_network_server.sh"

    try:
        with open(start_script, "w") as f:
            f.write(start_script_content)

        os.chmod(start_script, 0o755)
        print(f"✓ Start script created: {start_script}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create start script: {e}")
        return False


def show_usage_info(args):
    """Show usage information."""
    print(
        f"""
═══════════════════════════════════════════════════════════════
    Stanford Quadruped Enhanced Network Server Setup Complete
═══════════════════════════════════════════════════════════════

🤖 Server Configuration:
   Host: {args.host}
   Port: {args.port}
   UDP Port: {args.udp_port}

📡 Network Access:
   The server will be accessible at: http://{args.host}:{args.port}
   
   If using the default robot IP (10.0.0.10), access from your PC:
   http://10.0.0.10:{args.port}

🔧 Manual Control:
   Start: sudo systemctl start quadruped-network-server
   Stop:  sudo systemctl stop quadruped-network-server
   Status: sudo systemctl status quadruped-network-server
   
   Or use the start script: ./start_network_server.sh

📋 API Endpoints:
   GET  /status     - Get robot status
   GET  /actions    - List available actions
   POST /execute    - Execute an action
   POST /stop       - Emergency stop
   POST /clear      - Clear action queue

💡 Example API Usage:
   curl http://10.0.0.10:{args.port}/status
   curl -X POST http://10.0.0.10:{args.port}/execute \\
        -H "Content-Type: application/json" \\
        -d '{{"action": "forward", "duration": 3.0}}'

📖 Enhanced Features:
   ✓ RESTful HTTP API for remote control
   ✓ Action queuing and status monitoring
   ✓ Better error handling and recovery
   ✓ Compatibility with existing dog actions
   ✓ Automatic action parameter optimization

🚀 Next Steps:
   1. Update your robot group action planner to use NetworkDogAction
   2. Configure your PC client to connect to {args.host}:{args.port}
   3. Test the connection with: curl http://{args.host}:{args.port}/status

═══════════════════════════════════════════════════════════════
"""
    )


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup Enhanced Stanford Quadruped Network Server"
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
    parser.add_argument(
        "--no-service", action="store_true", help="Skip systemd service creation"
    )
    parser.add_argument("--source", help="Path to network_action_server.py source file")

    args = parser.parse_args()

    print("Stanford Quadruped Enhanced Network Server Setup")
    print("=" * 50)

    # Check if running as root for service installation
    if not args.no_service and os.geteuid() != 0:
        print("WARNING: Not running as root. Service installation will be skipped.")
        print("Run with 'sudo' to install systemd service, or use --no-service flag.")
        args.no_service = True

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    # Install network server
    if not install_network_server(args.source):
        sys.exit(1)

    # Create start script
    if not create_start_script():
        print("WARNING: Failed to create start script, but continuing...")

    # Setup service if requested
    if not args.no_service:
        if not create_service_file(args):
            sys.exit(1)

        if not setup_service(enable_service=True):
            print("WARNING: Service setup failed, but network server is installed.")
            print(
                "You can start it manually with: python3 /home/ubuntu/StanfordQuadruped/network_action_server.py"
            )

    # Show usage information
    show_usage_info(args)

    print("\n🎉 Setup completed successfully!")

    if not args.no_service:
        print("\nThe network server is now running as a system service.")
        print("Check status with: sudo systemctl status quadruped-network-server")
    else:
        print("\nTo start the server manually:")
        print("cd /home/ubuntu/StanfordQuadruped && python3 network_action_server.py")


if __name__ == "__main__":
    main()
