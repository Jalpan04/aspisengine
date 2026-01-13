# Stress Test Verification Guide

Here are the 8 tests to perform. Run each command in your terminal.

## 1. Physics Basics
**Command:** `python main.py --run-scene stress_test/scenes/01_physics_basics.scene.json`
**Question:** Do the boxes fall and land on the floor?
- **Yes:** The boxes fall under gravity, hit the floor, and stop or slide realistically.
- **No:** The boxes stay floating in the air or fall through the floor.

## 2. Interaction
**Command:** `python main.py --run-scene stress_test/scenes/02_interaction.scene.json`
**Question:** Does the character move when you press WASD/Arrow Keys?
- **Yes:** The logo moves in the corresponding direction while keys are held.
- **No:** The logo remains stationary regardless of input.

## 3. Camera Zoom
**Command:** `python main.py --run-scene stress_test/scenes/03_camera_zoom.scene.json`
**Question:** Is the central logo significantly larger (zoomed in) compared to the corner references?
- **Yes:** The central logo appears 2x larger than normal.
- **No:** All logos appear the same size (zoom failed).

## 4. Collider Shapes
**Command:** `python main.py --run-scene stress_test/scenes/04_collider_shapes.scene.json`
**Question:** Does the ball roll down the slope?
- **Yes:** The circular object rolls down the inclined rectangular object.
- **No:** The ball falls through the slope or gets stuck in the air.

## 5. Stress Performance
**Command:** `python main.py --run-scene stress_test/scenes/05_stress_performance.scene.json`
**Question:** Does the game continue to run effectively as objects pile up?
- **Yes:** Objects keep spawning and stacking, frame rate stays reasonable.
- **No:** The game freezes completely or crashes after a few seconds.

## 6. Hierarchy
**Command:** `python main.py --run-scene stress_test/scenes/06_hierarchy_transform.scene.json`
**Question:** Does the "Earth" (blue tint) orbit around the "Sun" (yellow tint)?
- **Yes:** The smaller blue object rotates *around* the larger yellow object as the yellow object spins.
- **No:** The blue object stays in one spot while the yellow object spins in place.

## 7. Lifecycle Events
**Command:** `python main.py --run-scene stress_test/scenes/07_lifecycle_events.scene.json`
**Question:** Do you see "Start called" in the console?
- **Yes:** `[Logger Object] Start called.` appears in the terminal output.
- **No:** No output appears in the console.

## 8. Crash Handling
**Command:** `python main.py --run-scene stress_test/scenes/08_crash_handling.scene.json`
**Question:** Does the application window STAY OPEN despite the errors?
- **Yes:** The window remains open (likely red background), and the console shows "division by zero" errors.
- **No:** The application window closes immediately.
