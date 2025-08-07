#!/bin/bash

# Movement sequence: forward -> backward -> forward -> backward
# Each command waits 3 seconds before executing the next

echo "Starting movement sequence..."

echo "1. Moving forward..."
curl -X POST -H "Content-Type: application/json" \
     -d '{"action": "move_forward", "duration": 3.0}' \
     http://localhost:8081/execute

echo "Waiting 3 seconds..."
sleep 3

echo "2. Moving backward..."
curl -X POST -H "Content-Type: application/json" \
     -d '{"action": "move_left", "duration": 3.0}' \
     http://localhost:8081/execute

echo "Waiting 3 seconds..."
sleep 3

echo "3. Moving forward..."
curl -X POST -H "Content-Type: application/json" \
     -d '{"action": "move_forward", "duration": 3.0}' \
     http://localhost:8081/execute

echo "Waiting 3 seconds..."
sleep 3

echo "4. Moving backward..."
curl -X POST -H "Content-Type: application/json" \
     -d '{"action": "move_right", "duration": 3.0}' \
     http://localhost:8081/execute

echo "Movement sequence completed!"
