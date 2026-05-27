import json
import os
import subprocess
import sys

def main():
    print("Building Test 1: Multi-Color Light Blending Demo...")
    
    scene_data = {
        "metadata": {"name": "Multi-Color Blending", "version": 1},
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
            # Central static block casting shadows
            {
                "id": "center_block",
                "name": "Center Block",
                "components": {
                    "Transform": {"position": [400.0, 300.0], "scale": [1.2, 1.2], "rotation": 45.0},
                    "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [200, 200, 200, 255], "layer": 0},
                    "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
                }
            }
        ]
    }
    
    # Add three orbiting lights (Red, Green, Blue)
    colors = [
        [255, 0, 0, 255],    # Red Light
        [0, 255, 0, 255],    # Green Light
        [0, 0, 255, 255]     # Blue Light
    ]
    
    import math
    for i, color in enumerate(colors):
        offset = i * (2.0 * math.pi / 3.0)
        scene_data["objects"].append({
            "id": f"orbit_light_{i}",
            "name": f"Light_{i}",
            "components": {
                "Transform": {"position": [400.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
                "LightSource": {
                    "color": color,
                    "intensity": 1.0,
                    "radius": 240.0,
                    "type": "point",
                    "cast_shadows": True
                },
                "Script": {
                    "script_path": "scripts/MultiLightOrbit.py",
                    "properties": {
                        "angle_offset": offset,
                        "speed": 1.0,
                        "orbit_radius": 150.0
                    }
                }
            }
        })
        
    scene_path = "stress_test/scenes/18_multi_light.scene.json"
    os.makedirs(os.path.dirname(scene_path), exist_ok=True)
    with open(scene_path, "w") as f:
        json.dump(scene_data, f, indent=2)
        
    print(f"Scene written to: {scene_path}")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "main.py", "--run-scene", scene_path]
    subprocess.Popen(cmd, env=env)
    print("Test 1 launched successfully!")

if __name__ == "__main__":
    main()
