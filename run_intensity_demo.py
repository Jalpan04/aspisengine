import json
import os
import subprocess
import sys

def main():
    print("Building Test 4: Variable Intensity & Radius Demo...")
    
    scene_data = {
        "metadata": {"name": "Light Oscillation Demo", "version": 1},
        "settings": {
            "background_color": [10, 10, 10, 255],
            "ambient_light": [10, 10, 10, 255]
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
            # A ring of static obstacles surrounding the oscillator light
            {
                "id": "block_top",
                "name": "Block Top",
                "components": {
                    "Transform": {"position": [400.0, 120.0], "scale": [1.2, 0.4], "rotation": 0.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [200, 200, 200, 255], "layer": 0},
                    "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            {
                "id": "block_bottom",
                "name": "Block Bottom",
                "components": {
                    "Transform": {"position": [400.0, 480.0], "scale": [1.2, 0.4], "rotation": 0.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [200, 200, 200, 255], "layer": 0},
                    "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            {
                "id": "block_left",
                "name": "Block Left",
                "components": {
                    "Transform": {"position": [200.0, 300.0], "scale": [0.4, 1.2], "rotation": 0.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [200, 200, 200, 255], "layer": 0},
                    "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            {
                "id": "block_right",
                "name": "Block Right",
                "components": {
                    "Transform": {"position": [600.0, 300.0], "scale": [0.4, 1.2], "rotation": 0.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [200, 200, 200, 255], "layer": 0},
                    "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            },
            # Central oscillating light
            {
                "id": "oscillating_light",
                "name": "Oscillating Light",
                "components": {
                    "Transform": {"position": [400.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
                    "LightSource": {
                        "color": [255, 100, 100, 255], # Dynamic red pulse
                        "intensity": 1.0,
                        "radius": 200.0,
                        "type": "point",
                        "cast_shadows": True
                    },
                    "Script": {
                        "script_path": "scripts/LightOscillator.py"
                    }
                }
            }
        ]
    }
    
    scene_path = "stress_test/scenes/21_light_oscillation.scene.json"
    os.makedirs(os.path.dirname(scene_path), exist_ok=True)
    with open(scene_path, "w") as f:
        json.dump(scene_data, f, indent=2)
        
    print(f"Scene written to: {scene_path}")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "main.py", "--run-scene", scene_path]
    subprocess.Popen(cmd, env=env)
    print("Test 4 launched successfully!")

if __name__ == "__main__":
    main()
