#
# Copyright 2024 MangDang (www.mangdang.net)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Description: Enhanced FPC(Flexible Programmable Choreography) choreography
#              Optimized for the Enhanced Network Action Server integration
#              Compatible with both local Stanford Quadruped control and remote HTTP API
#
# Enhanced Features:
#   - Improved action sequencing for better flow
#   - Enhanced movement combinations
#   - Better use of the available movement APIs
#   - Optimized timing and transitions
#   - Network-aware action management
#
# Test methods:
#   Method 1 - Controller:
#     1. Pair controller to Mini Pupper after power on
#     2. Click "L1" button to activate
#     3. Click "Circle" button to start dance
#
#   Method 2 - Command line (Enhanced):
#     python /home/ubuntu/StanfordQuadruped/run_danceActionList.py
#
#   Method 3 - Network API (New):
#     curl -X POST http://10.0.0.10:8080/execute \
#          -H "Content-Type: application/json" \
#          -d '{"action": "dance", "duration": 30.0}'
#
# Available Movement APIs:
#
# Level 1 (Simple APIs - no parameters):
#   stop() look_up() look_down() look_right() look_left()
#   look_upperleft() look_upperright() look_rightlower() look_leftlower()
#   move_forward() move_backward() move_right() move_left()
#   move_leftfront() move_rightfront() move_leftback() move_rightback()
#
# Level 2 (Advanced APIs - with parameters):
#   body_row(roll_deg, time_uni, time_acc)
#   gait_uni(v_x, v_y, time_uni, time_acc)
#   height_move(ht, time_uni, time_acc)
#   head_move(pitch_deg, yaw_deg, time_uni, time_acc)
#   foreleg_lift(leg_index, ht, time_uni, time_acc)
#   backleg_lift(leg_index, ht, time_uni, time_acc)
#   rotate(angle)
#   bowback(angle)
#
# Level 3 (Complex APIs - advanced choreography):
#   body_cycle() head_ellipse()
#

from src.MovementGroup import MovementGroups

Move = MovementGroups()

# === ENHANCED CHOREOGRAPHY SEQUENCE ===

# Opening Sequence - Greeting and Activation
print("=== Enhanced Mini Pupper Dance Choreography ===")
print("Starting greeting sequence...")

# Greeting sequence - Look around to acknowledge audience
Move.look_up()  # Look up to survey the area
Move.look_right()  # Look right
Move.look_upperright()  # Look up-right diagonal
Move.look_left()  # Look left
Move.look_upperleft()  # Look up-left diagonal
Move.look_down()  # Look down politely
Move.stop(1)  # Pause briefly

print("Greeting complete. Starting warm-up movements...")

# Warm-up sequence - Gentle movements to prepare
Move.head_move(15, 0, 1, 0.5)  # Gentle head nod
Move.body_row(5, 1, 0.5)  # Slight body tilt right
Move.body_row(-5, 1, 0.5)  # Slight body tilt left
Move.stop(0.5)

# Height adjustment demonstration
Move.height_move(0.02, 1, 0.8)  # Stand taller
Move.height_move(-0.03, 1, 0.8)  # Crouch lower
Move.height_move(0.01, 1, 0.5)  # Return to normal
Move.stop(0.5)

print("Warm-up complete. Beginning main dance sequence...")

# === MAIN DANCE SEQUENCE ===

# Movement Pattern 1 - Directional Flow
print("Pattern 1: Directional Flow")
Move.move_forward()  # Forward motion
Move.stop(0.3)
Move.move_backward()  # Backward motion
Move.stop(0.3)
Move.move_right()  # Right motion
Move.stop(0.3)
Move.move_left()  # Left motion
Move.stop(0.5)

# Movement Pattern 2 - Diagonal Dynamics
print("Pattern 2: Diagonal Dynamics")
Move.move_leftfront()  # Left-forward diagonal
Move.stop(0.3)
Move.move_rightback()  # Right-back diagonal
Move.stop(0.3)
Move.move_rightfront()  # Right-forward diagonal
Move.stop(0.3)
Move.move_leftback()  # Left-back diagonal
Move.stop(0.5)

# Movement Pattern 3 - Advanced Head Choreography
print("Pattern 3: Head Choreography")
Move.head_move(20, 30, 1.5, 0.8)  # Look up-right
Move.head_move(-15, -25, 1.2, 0.6)  # Look down-left
Move.head_move(10, 0, 1, 0.5)  # Center with slight up
Move.head_move(0, 0, 1, 0.5)  # Return to center
Move.stop(0.5)

# Movement Pattern 4 - Body Expression
print("Pattern 4: Body Expression")
Move.body_row(15, 1.5, 0.8)  # Strong right tilt
Move.body_row(-15, 1.5, 0.8)  # Strong left tilt
Move.body_row(8, 1, 0.5)  # Gentle right
Move.body_row(-8, 1, 0.5)  # Gentle left
Move.body_row(0, 1, 0.5)  # Return to center
Move.stop(0.5)

# Movement Pattern 5 - Gait Variations
print("Pattern 5: Gait Variations")
Move.gait_uni(0.2, 0, 2, 0.8)  # Slow forward
Move.gait_uni(0, 0.15, 2, 0.8)  # Slow sideways right
Move.gait_uni(-0.2, 0, 2, 0.8)  # Slow backward
Move.gait_uni(0, -0.15, 2, 0.8)  # Slow sideways left
Move.stop(0.8)

# Movement Pattern 6 - Combined Speed and Direction
print("Pattern 6: Speed Variations")
Move.gait_uni(0.3, 0.1, 1.5, 0.5)  # Fast forward-right
Move.gait_uni(-0.25, 0.2, 1.5, 0.5)  # Medium back-right
Move.gait_uni(0.1, -0.3, 1.5, 0.5)  # Fast left-forward
Move.stop(0.8)

# Movement Pattern 7 - Leg Articulation
print("Pattern 7: Leg Articulation")
Move.foreleg_lift("right", 0.03, 1.5, 0.8)  # Right front leg up
Move.foreleg_lift("left", 0.03, 1.5, 0.8)  # Left front leg up
Move.backleg_lift("right", 0.03, 1.5, 0.8)  # Right back leg up
Move.backleg_lift("left", 0.03, 1.5, 0.8)  # Left back leg up
Move.stop(0.8)

# Movement Pattern 8 - Height Dynamics
print("Pattern 8: Height Dynamics")
Move.height_move(0.03, 1.2, 0.8)  # Rise up
Move.height_move(-0.02, 0.8, 0.5)  # Drop down
Move.height_move(0.025, 1, 0.6)  # Rise again
Move.height_move(-0.015, 1, 0.6)  # Gentle drop
Move.height_move(0, 1, 0.5)  # Return to normal
Move.stop(0.8)

# Movement Pattern 9 - Rotational Elements
print("Pattern 9: Rotational Elements")
Move.rotate(45)  # Quarter turn right
Move.stop(0.5)
Move.rotate(-90)  # Half turn left (net -45 from start)
Move.stop(0.5)
Move.rotate(45)  # Quarter turn right (back to start)
Move.stop(0.8)

# Movement Pattern 10 - Advanced Combinations
print("Pattern 10: Advanced Combinations")
# Simultaneous head and body movement
Move.head_move(15, 20, 2, 1)  # Head up-right
Move.body_row(10, 2, 1)  # Body tilt right (concurrent)
Move.stop(0.5)

Move.head_move(-10, -30, 2, 1)  # Head down-left
Move.body_row(-12, 2, 1)  # Body tilt left (concurrent)
Move.stop(0.8)

# Complex gait with attitude
Move.gait_uni(0.2, 0.1, 2, 0.8)  # Forward-right movement
Move.head_move(0, 0, 1, 0.5)  # Return head to center
Move.body_row(0, 1, 0.5)  # Return body to center
Move.stop(0.8)

# === ADVANCED CHOREOGRAPHY PATTERNS ===

print("Advanced Patterns: Complex Choreography")

# Advanced Pattern 1 - Body Cycle (Level 3)
print("Advanced Pattern 1: Body Cycle")
Move.body_cycle()  # Complex circular body movement
Move.stop(1)

# Advanced Pattern 2 - Bow and Move
print("Advanced Pattern 2: Bow Sequence")
Move.bowback(20)  # Bow with backward movement
Move.stop(1)

# Advanced Pattern 3 - Head Ellipse (Level 3)
print("Advanced Pattern 3: Head Ellipse")
Move.head_ellipse()  # Complex elliptical head movement
Move.stop(1)

# === FINALE SEQUENCE ===

print("Finale: Grand Closing")

# Grand finale - Combination of best elements
Move.height_move(0.035, 1.5, 1)  # Rise to maximum height
Move.head_move(25, 0, 2, 1)  # Look up proudly
Move.body_row(0, 1, 0.5)  # Ensure body is centered
Move.stop(2)  # Hold the pose

# Graceful descent and bow
Move.height_move(-0.02, 2, 1.5)  # Gentle descent
Move.head_move(-15, 0, 1.5, 1)  # Bow head
Move.stop(1.5)  # Hold bow

# Return to neutral for completion
Move.head_move(0, 0, 1, 0.8)  # Return head to center
Move.height_move(0, 1, 0.8)  # Return to normal height
Move.stop(2)  # Final pause

# === ENHANCED ENDING SEQUENCE ===

print("Ending: Acknowledgment Sequence")

# Final acknowledgment - Look around to thank audience
Move.look_left()  # Thank left side
Move.stop(0.5)
Move.look_right()  # Thank right side
Move.stop(0.5)
Move.look_up()  # Look up with pride
Move.stop(0.5)
Move.look_down()  # Modest final bow
Move.stop(1)

# Final position
Move.stop(3)  # Extended final pose

print("=== Enhanced Choreography Complete ===")
print("Total dance duration: ~90-120 seconds")
print("Movements utilized: All 3 levels (Basic, Advanced, Complex)")
print("Network API compatible: Yes")
print("Enhanced features: Improved flow, better transitions, audience engagement")

# Export the movement library for the execution engine
MovementLib = Move.MovementLib
