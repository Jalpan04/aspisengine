import json
import os
import subprocess
import sys

def main():
    print("Building Test 3: Circle vs Box Collider Shadows Demo...")
    
    scene_data = {
        "metadata": {"name": "Circle vs Box Shadows", "version": 1},
        "settings": {
            "background_color": [10, 10, 10, 255],
            "ambient_light": [15, 15, 15, 255]
        },
        "prefabs": {},
        "objects": [
            # Main Camera
            {
                "id": "cam",
                "name": "Main Camera",
                "components": {
                    "Transform": {"position": [400.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
                    "Camera": {"is_main": True, "zoom": 1.0, "width": 800.0, "height": 600.0}
                }
            },
            # Box Collider Obstacle (Left)
            {
                "id": "box_obstacle",
                "name": "Box Obstacle",
                "components": {
                    "Transform": {"position": [240.0, 300.0], "scale": [0.8, 0.8], "rotation": 30.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [100, 255, 100, 255], "layer": 0},
                    "BoxCollider": {"size": [80.0, 80.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            # Circle Collider Obstacle (Right)
            {
                "id": "circle_obstacle",
                "name": "Circle Obstacle",
                "components": {
                    "Transform": {"position": [560.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [255, 100, 255, 255], "layer": 0},
                    "CircleCollider": {"radius": 40.0, "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            # Orbiting Light passing between obstacles
            {
                "id": "moving_light",
                "name": "Moving Light",
                "components": {
                    "Transform": {"position": [400.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
                    "LightSource": {
                        "color": [255, 255, 255, 255],
                        "intensity": 1.0,
                        "radius": 280.0,
                        "type": "point",
                        "cast_shadows": True
                    },
                    "Script": {
                        "script_path": "scripts/LightOrbit.py"
                    }
                }
            }
        ]
    }
    
    scene_path = "stress_test/scenes/20_collider_shadows.scene.json"
    os.makedirs(os.path.dirname(scene_path), exist_ok=True)
    with open(scene_path, "w") as f:
        json.dump(scene_data, f, indent=2)
        
    print(f"Scene written to: {scene_path}")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "main.py", "--run-scene", scene_path]
    subprocess.Popen(cmd, env=env)
    print("Test 3 launched successfully!")

if __name__ == "__main__":
    main()
