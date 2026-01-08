
import json
import os

scene = {
    "metadata": {
        "name": "Pong Demo",
        "created_at": "2024-04-20T12:00:00.000000"
    },
    "objects": [
        {
            "id": "camera",
            "name": "Main Camera",
            "active": True,
            "components": {
                "Transform": {"position": [0, 0], "rotation": 0, "scale": [1, 1]},
                "Camera": {"width": 800, "height": 600, "zoom": 1.0, "is_main": True}
            }
        },
        {
            "id": "paddle_left",
            "name": "PaddleLeft",
            "active": True,
            "components": {
                "Transform": {"position": [-350, 0], "rotation": 0, "scale": [0.4, 2.0]},
                "SpriteRenderer": {"sprite_path": "", "layer": 1, "visible": True, "tint": [255, 50, 50, 255]},
                "BoxCollider": {"size": [20, 100], "offset": [0, 0], "is_trigger": False},
                "RigidBody": {"mass": 50.0, "drag": 5.0, "use_gravity": False, "restitution": 0.0},
                "Script": {"script_path": "scripts/PongPaddle.py"}
            }
        },
        {
            "id": "paddle_right",
            "name": "PaddleRight",
            "active": True,
            "components": {
                "Transform": {"position": [350, 0], "rotation": 0, "scale": [0.4, 2.0]},
                "SpriteRenderer": {"sprite_path": "", "layer": 1, "visible": True, "tint": [50, 50, 255, 255]},
                "BoxCollider": {"size": [20, 100], "offset": [0, 0], "is_trigger": False},
                "RigidBody": {"mass": 50.0, "drag": 5.0, "use_gravity": False, "restitution": 0.0},
                "Script": {"script_path": "scripts/PongPaddle.py"}
            }
        },
        {
            "id": "ball",
            "name": "Ball",
            "active": True,
            "components": {
                "Transform": {"position": [0, 0], "rotation": 0, "scale": [0.4, 0.4]},
                "SpriteRenderer": {"sprite_path": "", "layer": 2, "visible": True, "tint": [255, 255, 0, 255]},
                "BoxCollider": {"size": [20, 20], "offset": [0, 0], "is_trigger": False},
                "RigidBody": {"mass": 1.0, "drag": 0.0, "use_gravity": False, "restitution": 1.0, "velocity": [200, 200]},
                "Script": {"script_path": "scripts/PongBall.py"}
            }
        },
        {
            "id": "wall_top",
            "name": "WallTop",
            "active": True,
            "components": {
                "Transform": {"position": [0, -290], "rotation": 0, "scale": [16.0, 0.4]},
                "SpriteRenderer": {"sprite_path": "", "layer": 0, "visible": True, "tint": [100, 100, 100, 255]},
                "BoxCollider": {"size": [800, 20], "offset": [0, 0], "is_trigger": False},
                "RigidBody": {"mass": 0.0, "drag": 0.0, "use_gravity": False, "restitution": 1.0} 
            }
        },
        {
            "id": "wall_bottom",
            "name": "WallBottom",
            "active": True,
            "components": {
                "Transform": {"position": [0, 290], "rotation": 0, "scale": [16.0, 0.4]},
                "SpriteRenderer": {"sprite_path": "", "layer": 0, "visible": True, "tint": [100, 100, 100, 255]},
                "BoxCollider": {"size": [800, 20], "offset": [0, 0], "is_trigger": False},
                "RigidBody": {"mass": 0.0, "drag": 0.0, "use_gravity": False, "restitution": 1.0}
            }
        },
         {
            "id": "wall_left_limit",
            "name": "LimitLeft",
            "active": True,
            "components": {
                "Transform": {"position": [-410, 0], "rotation": 0, "scale": [0.4, 12.0]},
                "BoxCollider": {"size": [20, 600], "offset": [0, 0], "is_trigger": True}
             }
         },
         {
            "id": "wall_right_limit",
            "name": "LimitRight",
            "active": True,
            "components": {
                "Transform": {"position": [410, 0], "rotation": 0, "scale": [0.4, 12.0]},
                "BoxCollider": {"size": [20, 600], "offset": [0, 0], "is_trigger": True}
             }
         }
    ],
    "prefabs": {}
}

with open("scenes/Pong.scene.json", "w") as f:
    json.dump(scene, f, indent=4)
print("Created scenes/Pong.scene.json")
