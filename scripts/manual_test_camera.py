
import json
import os
import sys
import pygame

# Helper to generate scene
def create_test_scene(filename):
    scene = {
        "metadata": {"name": "CameraTest"},
        "objects": [
            {
                "id": "cam",
                "name": "MainCamera",
                "components": {
                    "Transform": {"position": [0, 0], "rotation": 0, "scale": [1, 1]},
                    "Camera": {"width": 600, "height": 600, "zoom": 1.0, "is_main": True}
                }
            },
            {
                "id": "ref_box",
                "name": "ReferenceBox_200x200",
                "components": {
                    "Transform": {"position": [0, 0], "rotation": 0, "scale": [1, 1]},
                    "SpriteRenderer": {"color": [255, 0, 0, 255], "layer": 0},
                    # No image, will fallback to color rect if simplified or verify rendering logic
                    "BoxCollider": {"size": [200, 200]} # For size reference
                }
            }
        ]
    }
    
    with open(filename, "w") as f:
        json.dump(scene, f, indent=2)
    print(f"Created {filename}")

def run_test():
    scene_path = os.path.abspath("scenes/manual_camera_test.scene.json")
    create_test_scene(scene_path)
    
    print("-" * 50)
    print("CAMERA MANUAL TEST CHECKLIST")
    print("-" * 50)
    print("1. A Game Window should open.")
    print("2. The Window Inner Size should be EXACTLY 600x600 pixels.")
    print("   (Use a screenshot tool or screen ruler to verify).")
    print("3. You should see a WHITE/GRAY background.")
    print("4. There is a Reference Object (Red Box) centered.")
    print("   (Wait, SpriteRenderer might need a path or fallback. If no sprite, logic defaults to white box or similar.)")
    print("   If defaults used: You might just see a 600x600 window.")
    print("-" * 50)
    
    # Launch Game Loop
    print(f"Launching: {sys.executable} runtime/game_loop.py {scene_path}")
    
    import subprocess
    subprocess.run([sys.executable, "runtime/game_loop.py", scene_path])

if __name__ == "__main__":
    run_test()
