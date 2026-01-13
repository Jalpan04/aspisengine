
import json
import os
import sys
import uuid

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def create_scene(name):
    return {
        "metadata": {"name": name},
        "objects": [],
        "prefabs": {},
        "settings": {"background_color": [20, 20, 30, 255]}
    }

def create_obj(name, pos, scale=(1,1), rot=0, parent=None):
    obj = {
        "id": str(uuid.uuid4()),
        "name": name,
        "active": True,
        "components": {
            "Transform": {
                "position": list(pos),
                "rotation": rot,
                "scale": list(scale)
            }
        },
        "children": []
    }
    if parent:
        obj["parent"] = parent
    return obj

def add_camera(scene, x=400, y=300):
    cam = create_obj("Main Camera", [x, y])
    cam["components"]["Camera"] = {"is_main": True}
    scene["objects"].append(cam)

def add_script(obj, script_path, properties=None):
    obj["components"]["Script"] = {"script_path": script_path}
    if properties:
        obj["components"]["Script"]["properties"] = properties

def add_renderer(obj, color):
    obj["components"]["SpriteRenderer"] = {
        "sprite_path": "",
        "tint": color
    }

def add_box_collider(obj, w, h):
    obj["components"]["BoxCollider"] = {"size": [w, h]}

def add_rigidbody(obj, body_type="dynamic", mass=1.0):
    obj["components"]["RigidBody"] = {"body_type": body_type, "mass": mass}


# --- Test 9: Object Cycling ---
def gen_09():
    scene = create_scene("09 Object Cycling")
    add_camera(scene)
    
    manager = create_obj("CycleManager", [0, 0])
    add_script(manager, "stress_test/scripts/ObjectCycler.py")
    scene["objects"].append(manager)
    
    with open("stress_test/scenes/09_object_cycling.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# --- Test 10: Physics Stacking ---
def gen_10():
    scene = create_scene("10 Physics Stacking")
    add_camera(scene, 400, 400)
    
    # Floor
    floor = create_obj("Floor", [400, 750], scale=[10, 1]) # 1000x100
    add_renderer(floor, [50, 50, 50, 255])
    add_box_collider(floor, 100, 100)
    add_rigidbody(floor, "static")
    scene["objects"].append(floor)
    
    # Stack
    for i in range(25):
        box = create_obj(f"Box_{i}", [400, 680 - (i * 55)], scale=[0.5, 0.5]) # 50x50
        add_renderer(box, [255, 100 + (i*5), 0, 255])
        add_box_collider(box, 100, 100) # Size 100 * 0.5 = 50
        add_rigidbody(box, "dynamic", mass=5.0) # Heavy
        scene["objects"].append(box)

    with open("stress_test/scenes/10_physics_stacking.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# --- Test 11: Deep Hierarchy ---
def gen_11():
    scene = create_scene("11 Deep Hierarchy")
    add_camera(scene)
    
    # Root
    root = create_obj("Root", [400, 300]) # Center
    add_renderer(root, [255, 255, 255, 255])
    add_script(root, "stress_test/scripts/Rotator.py") # Spin the whole chain
    scene["objects"].append(root)
    
    parent_id = root["id"]
    
    # Chain
    for i in range(15):
        # Offset child by 20px right
        child = create_obj(f"Link_{i}", [20, 0], scale=[0.9, 0.9])
        child["parent"] = parent_id
        add_renderer(child, [255 - (i*10), 0, i*15, 255])
        # add_script(child, "stress_test/scripts/Rotator.py") # Spin each link too? Chaos. Yes.
        
        scene["objects"].append(child)
        parent_id = child["id"]

    with open("stress_test/scenes/11_deep_hierarchy.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# --- Test 12: Broken Assets ---
def gen_12():
    scene = create_scene("12 Broken Assets")
    add_camera(scene)
    
    # Missing Sprite
    missing_sprite = create_obj("MissingSprite", [200, 300])
    miss_sr = {"sprite_path": "non_existent.png", "tint": [255, 255, 255, 255]}
    missing_sprite["components"]["SpriteRenderer"] = miss_sr
    scene["objects"].append(missing_sprite)
    
    # Broken Script
    broken_script = create_obj("BrokenScriptObj", [600, 300])
    add_renderer(broken_script, [0, 255, 0, 255])
    add_script(broken_script, "stress_test/scripts/NonExistent.py")
    scene["objects"].append(broken_script)

    with open("stress_test/scenes/12_broken_assets.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# --- Test 13: Scene Ping Pong ---
def gen_13():
    # Scene A
    scene_a = create_scene("13 Ping Pong A")
    add_camera(scene_a)
    obj_a = create_obj("ManagerA", [300, 300])
    add_renderer(obj_a, [255, 0, 0, 255])
    # Load B after 1 sec
    add_script(obj_a, "stress_test/scripts/SceneSwitcher.py", {"next_scene": "stress_test/scenes/13_scene_ping_pong_b.scene.json"})
    scene_a["objects"].append(obj_a)
    with open("stress_test/scenes/13_scene_ping_pong_a.scene.json", "w") as f:
        json.dump(scene_a, f, indent=2)

    # Scene B
    scene_b = create_scene("13 Ping Pong B")
    add_camera(scene_b)
    obj_b = create_obj("ManagerB", [500, 300])
    add_renderer(obj_b, [0, 0, 255, 255])
    # Load A after 1 sec
    add_script(obj_b, "stress_test/scripts/SceneSwitcher.py", {"next_scene": "stress_test/scenes/13_scene_ping_pong_a.scene.json"})
    scene_b["objects"].append(obj_b)
    with open("stress_test/scenes/13_scene_ping_pong_b.scene.json", "w") as f:
        json.dump(scene_b, f, indent=2)


# --- Test 14: Text Thrashing ---
def gen_14():
    scene = create_scene("14 Text Thrashing")
    add_camera(scene)
    
    thrasher = create_obj("TextThrasher", [400, 300])
    thrasher["components"]["TextRenderer"] = {
        "text": "Init",
        "font_size": 40,
        "color": [255, 255, 255]
    }
    add_script(thrasher, "stress_test/scripts/TextThrasher.py")
    scene["objects"].append(thrasher)
    
    with open("stress_test/scenes/14_text_thrashing.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# --- Test 15: Fast Physics ---
def gen_15():
    scene = create_scene("15 Fast Physics")
    add_camera(scene)
    
    # Wall
    wall = create_obj("Wall", [600, 300], scale=[0.5, 10]) # 50x1000
    add_renderer(wall, [200, 200, 200, 255])
    add_box_collider(wall, 100, 100) # 50x1000
    add_rigidbody(wall, "static")
    scene["objects"].append(wall)
    
    # Bullet
    bullet = create_obj("Bullet", [0, 300], scale=[0.2, 0.2]) # 20x20
    add_renderer(bullet, [255, 0, 0, 255])
    obj_col = {"radius": 100, "offset": [0,0]} # Wait, circle radius 100 * 0.2 = 20. Correct.
    bullet["components"]["CircleCollider"] = obj_col
    
    # Velocity 5000 means it crosses 800px in 0.16s (10 frames). 
    # Actually 5000 px/s => 83 px/frame at 60fps.
    # Wall is 50px wide. 83px jump might skip it.
    bullet["components"]["RigidBody"] = {"body_type": "dynamic", "mass": 0.1, "velocity": [5000, 0]}
    
    scene["objects"].append(bullet)

    with open("stress_test/scenes/15_fast_physics.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# --- Test 16: Data Poisoning ---
def gen_16():
    scene = create_scene("16 Data Poisoning")
    add_camera(scene)
    
    poison = create_obj("PoisonPill", [400, 300])
    add_renderer(poison, [0, 255, 0, 255])
    add_script(poison, "stress_test/scripts/PoisonScript.py")
    scene["objects"].append(poison)

    with open("stress_test/scenes/16_data_poisoning.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

if __name__ == "__main__":
    if not os.path.exists("stress_test/scenes"):
        os.makedirs("stress_test/scenes")
        
    gen_09()
    gen_10()
    gen_11()
    gen_12()
    gen_13()
    gen_14()
    gen_15()
    gen_16()
    print("Generated Advanced Tests 9-16.")
