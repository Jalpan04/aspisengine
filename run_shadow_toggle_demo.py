import json
import os
import subprocess
import sys

def main():
    print("Building Test 2: Shadow Toggle Demo...")
    
    scene_data = {
        "metadata": {"name": "Shadow Toggle Demo", "version": 1},
        "settings": {
            "background_color": [10, 10, 10, 255],
            "ambient_light": [25, 25, 25, 255]
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
            # Obstacle left
            {
                "id": "left_block",
                "name": "Left Block (Casts Shadow)",
                "components": {
                    "Transform": {"position": [280.0, 300.0], "scale": [0.6, 1.5], "rotation": 0.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [255, 100, 100, 255], "layer": 0},
                    "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            # Obstacle right
            {
                "id": "right_block",
                "name": "Right Block (Unshadowed)",
                "components": {
                    "Transform": {"position": [520.0, 300.0], "scale": [0.6, 1.5], "rotation": 0.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [100, 255, 255, 255], "layer": 0},
                    "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            # Light 1 (Casts Shadows - Left)
            {
                "id": "shadow_light",
                "name": "Shadow Light",
                "components": {
                    "Transform": {"position": [160.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
                    "LightSource": {
                        "color": [255, 220, 100, 255],
                        "intensity": 1.0,
                        "radius": 250.0,
                        "type": "point",
                        "cast_shadows": True
                    },
                    "Script": {
                        "script_path": "scripts/VerticalHover.py",
                        "properties": {
                            "start_x": 160.0,
                            "start_y": 300.0,
                            "range_y": 150.0,
                            "speed": 1.5
                        }
                    }
                }
            },
            # Light 2 (No Shadows - Right)
            {
                "id": "no_shadow_light",
                "name": "No Shadow Light",
                "components": {
                    "Transform": {"position": [640.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
                    "LightSource": {
                        "color": [100, 255, 100, 255],
                        "intensity": 1.0,
                        "radius": 250.0,
                        "type": "point",
                        "cast_shadows": False
                    },
                    "Script": {
                        "script_path": "scripts/VerticalHover.py",
                        "properties": {
                            "start_x": 640.0,
                            "start_y": 300.0,
                            "range_y": 150.0,
                            "speed": 1.5
                        }
                    }
                }
            }
        ]
    }
    
    scene_path = "stress_test/scenes/19_shadow_toggle.scene.json"
    os.makedirs(os.path.dirname(scene_path), exist_ok=True)
    with open(scene_path, "w") as f:
        json.dump(scene_data, f, indent=2)
        
    print(f"Scene written to: {scene_path}")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "main.py", "--run-scene", scene_path]
    subprocess.Popen(cmd, env=env)
    print("Test 2 launched successfully!")

if __name__ == "__main__":
    main()
