import json
import os
import subprocess
import sys

def main():
    print("Building dynamic lighting demo scene...")
    
    # 1. Define Scene settings
    scene_data = {
        "metadata": {
            "name": "Dynamic Lighting Demo",
            "version": 1
        },
        "settings": {
            "background_color": [10, 10, 15, 255],
            "ambient_light": [20, 20, 30, 255] # Dark blue-grey ambient
        },
        "prefabs": {},
        "objects": []
    }
    
    # 2. Add Main Camera (Centered at 400, 300)
    scene_data["objects"].append({
        "id": "cam",
        "name": "Main Camera",
        "components": {
            "Transform": {
                "position": [400.0, 300.0],
                "scale": [1.0, 1.0],
                "rotation": 0.0
            },
            "Camera": {
                "is_main": True,
                "zoom": 1.0,
                "width": 800.0,
                "height": 600.0
            }
        }
    })
    
    # 3. Add a grid of colorful static blocks
    colors = [
        [255, 100, 100, 255],  # Coral Red
        [100, 255, 100, 255],  # Lime Green
        [100, 100, 255, 255],  # Slate Blue
        [255, 255, 100, 255],  # Bright Yellow
        [255, 100, 255, 255],  # Magenta
        [100, 255, 255, 255]   # Cyan
    ]
    
    idx = 0
    # Create static blocks
    for x in range(200, 700, 120):
        for y in range(120, 550, 120):
            color = colors[idx % len(colors)]
            idx += 1
            scene_data["objects"].append({
                "id": f"block_{x}_{y}",
                "name": f"Block_{idx}",
                "components": {
                    "Transform": {
                        "position": [float(x), float(y)],
                        "scale": [0.6, 0.6],
                        "rotation": 15.0 * idx # Stylized rotation
                    },
                    "SpriteRenderer": {
                        "sprite_path": "", # Procedural block fallback
                        "visible": True,
                        "tint": color,
                        "layer": 0
                    },
                    "BoxCollider": {
                        "size": [100.0, 100.0],
                        "offset": [0.0, 0.0],
                        "is_trigger": False
                    }
                }
            })
            
    # 4. Add the Orbiting LightSource
    scene_data["objects"].append({
        "id": "orbiting_light",
        "name": "Orbiting Light",
        "components": {
            "Transform": {
                "position": [400.0, 300.0],
                "scale": [1.0, 1.0],
                "rotation": 0.0
            },
            "LightSource": {
                "color": [255, 220, 150, 255], # Soft warm golden light
                "intensity": 1.0,
                "radius": 220.0,
                "type": "point"
            },
            "Script": {
                "script_path": "scripts/LightOrbit.py"
            }
        }
    })
    
    # 5. Save the generated scene
    scene_dir = "stress_test/scenes"
    os.makedirs(scene_dir, exist_ok=True)
    scene_path = os.path.join(scene_dir, "17_lighting_demo.scene.json")
    
    with open(scene_path, "w") as f:
        json.dump(scene_data, f, indent=2)
        
    print(f"Demo scene JSON written successfully to: {scene_path}")
    print("Launching Aspis Game Runtime...")
    
    # 6. Spawn Runtime
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
        cmd = [sys.executable, "main.py", "--run-scene", scene_path]
        
        # Non-blocking subprocess
        subprocess.Popen(cmd, env=env)
        print("Success! The Game Runtime is now opening. Enjoy the dynamic lighting show!")
    except Exception as e:
        print(f"Error launching demo runtime: {e}")

if __name__ == "__main__":
    main()
