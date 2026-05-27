import json
import os
import subprocess
import sys

def main():
    print("Building Test 5: Complex Maze & Occlusion Stress Test Demo...")
    
    scene_data = {
        "metadata": {"name": "Maze Occlusion Stress Test", "version": 1},
        "settings": {
            "background_color": [5, 5, 8, 255],
            "ambient_light": [15, 15, 20, 255]
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
            }
        ]
    }
    
    # Define a maze of segment walls
    # List of (x, y, scale_x, scale_y, rotation)
    walls = [
        # Outer border boundaries (inner side to cast shadows)
        (400, 40, 7.5, 0.25, 0),    # Top border
        (400, 560, 7.5, 0.25, 0),   # Bottom border
        (40, 300, 0.25, 5.0, 0),    # Left border
        (760, 300, 0.25, 5.0, 0),   # Right border
        
        # Maze interior pillars / walls
        (220, 180, 0.25, 2.0, 0),   # Left corridor wall
        (220, 420, 2.0, 0.25, 0),
        (580, 180, 2.0, 0.25, 0),   # Right corridor wall
        (580, 420, 0.25, 2.0, 0),
        
        (400, 220, 1.5, 0.25, 45),  # Angled central crossbar 1
        (400, 380, 1.5, 0.25, -45), # Angled central crossbar 2
        
        (300, 300, 0.25, 1.0, 0),
        (500, 300, 0.25, 1.0, 0)
    ]
    
    for idx, (x, y, sx, sy, rot) in enumerate(walls):
        scene_data["objects"].append({
            "id": f"maze_wall_{idx}",
            "name": f"Wall_{idx}",
            "components": {
                "Transform": {
                    "position": [float(x), float(y)],
                    "scale": [float(sx), float(sy)],
                    "rotation": float(rot)
                },
                "SpriteRenderer": {"sprite_path": "", "visible": True, "tint": [120, 120, 150, 255], "layer": 0},
                "BoxCollider": {"size": [100.0, 100.0], "offset": [0.0, 0.0], "is_trigger": False}
            }
        })
        
    # Weave an orbiting light through the maze
    scene_data["objects"].append({
        "id": "maze_light",
        "name": "Maze Light",
        "components": {
            "Transform": {"position": [400.0, 300.0], "scale": [1.0, 1.0], "rotation": 0.0},
            "LightSource": {
                "color": [150, 255, 150, 255], # Soft green toxic light
                "intensity": 1.0,
                "radius": 320.0,
                "type": "point",
                "cast_shadows": True
            },
            "Script": {
                "script_path": "scripts/LightOrbit.py",
                "properties": {
                    "orbit_radius": 220.0,
                    "speed": 0.8
                }
            }
        }
    })
    
    scene_path = "stress_test/scenes/22_maze_stress.scene.json"
    os.makedirs(os.path.dirname(scene_path), exist_ok=True)
    with open(scene_path, "w") as f:
        json.dump(scene_data, f, indent=2)
        
    print(f"Scene written to: {scene_path}")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")
    cmd = [sys.executable, "main.py", "--run-scene", scene_path]
    subprocess.Popen(cmd, env=env)
    print("Test 5 launched successfully!")

if __name__ == "__main__":
    main()
