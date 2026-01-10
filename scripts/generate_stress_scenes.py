
import json
import os
import sys
import uuid

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.scene_schema import Scene

def create_scene(name):
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "objects": [],
        "settings": {"background_color": [20, 20, 30, 255]}
    }

def create_obj(name, pos, scale=(1,1), rot=0, parent=None):
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "active": True,
        "components": {
            "Transform": {
                "position": pos,
                "rotation": rot,
                "scale": scale,
                "parent_id": parent
            }
        },
        "children": []
    }

def add_box_collider(obj, w, h, is_trigger=False):
    obj["components"]["BoxCollider"] = {
        "size": [w, h],
        "offset": [0, 0],
        "is_trigger": is_trigger
    }

def add_circle_collider(obj, r):
    obj["components"]["CircleCollider"] = {
        "radius": r,
        "offset": [0, 0]
    }

def add_rigidbody(obj, mass=1.0, dynamic=True, friction=0.5, restitution=0.5, velocity=[0,0]):
    obj["components"]["RigidBody"] = {
        "mass": mass if dynamic else 0,
        "drag": 0.05,
        "use_gravity": True if dynamic else False,
        "restitution": restitution,
        "friction": friction,
        "fixed_rotation": False,
        "velocity": velocity if dynamic else [0, 0]
    }

def add_renderer(obj, color, size=(50,50)):
    # Create simple colored sprite representation
    # We will use "color" property of Background for visualization?
    # No, we use SpriteRenderer with tint, but no sprite_path (draws fallback rect?)
    # Editor uses fallback rect if no sprite. Runtime might not.
    # We should add a "Background" component with "fixed: false" to act as a colored primitive?
    obj["components"]["Background"] = {
        "color": color,
        "fixed": False,
        "layer": 0
    }

def add_camera(obj, zoom=1.0):
    obj["components"]["Camera"] = {
        "width": 800,
        "height": 600,
        "zoom": zoom,
        "is_main": True
    }

# 1. TOWER OF INSTABILITY (Stacking)
def gen_tower():
    scene = create_scene("Stress Test 1 - The Tower")

    # Camera
    cam = create_obj("Main Camera", [0, 0])
    add_camera(cam, zoom=0.8) # Zoom out to see stack
    scene["objects"].append(cam)
    
    # Ground
    ground = create_obj("Ground", [0, 300], scale=[20, 0.5]) # Visual: 2000x50
    add_box_collider(ground, 2000, 50)
    add_rigidbody(ground, dynamic=False, restitution=0.1) # Low bounce for stability
    add_renderer(ground, [100, 100, 100, 255])
    scene["objects"].append(ground)
    
    # Stack
    start_y = 250
    for i in range(15):
        box = create_obj(f"Box_{i}", [0, start_y - (i * 55)], scale=[0.5, 0.5]) # Visual: 50x50
        add_box_collider(box, 50, 50) # Collider: 50x50 matches Visual
        add_rigidbody(box, mass=1.0, friction=0.8) 
        add_renderer(box, [200, 50, 50 + (i*10), 255])
        scene["objects"].append(box)
    
    with open("scenes/stress_1_tower.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# 2. BOUNCY HOUSE (Restitution)
def gen_bounce():
    scene = create_scene("Stress Test 2 - Bouncy House")

    # Camera
    cam = create_obj("Main Camera", [0, -100])
    add_camera(cam, zoom=1.0)
    scene["objects"].append(cam)
    
    # Ground
    ground = create_obj("Ground", [0, 300], scale=[20, 0.5])
    add_box_collider(ground, 2000, 50)
    add_rigidbody(ground, dynamic=False, restitution=1.0) # High restitution ground
    add_renderer(ground, [100, 100, 100, 255])
    scene["objects"].append(ground)

    offsets = [-100, 0, 100]
    bounciness = [0.5, 0.9, 1.2] 
    
    for x, b in zip(offsets, bounciness):
        ball = create_obj(f"Ball_{b}", [x, -200], scale=[0.5, 0.5]) # Visual: 50 diameter? No, rect default. Circle collider is independent.
        # But renderer draws Rect unless sprite. Circle rendering? 
        # Canvas defaults to Rect if no sprite. CircleCollider drawn as Gizmo.
        # For Stress Test, rect visual is fine, but circle collider acts like ball.
        add_circle_collider(ball, 25) # Radius 25 -> Diameter 50. 
        add_rigidbody(ball, restitution=b)
        add_renderer(ball, [50, 200, 50, 255])
        scene["objects"].append(ball)

    with open("scenes/stress_2_bounce.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# 3. ACCELERATOR (Tunneling)
def gen_speed():
    scene = create_scene("Stress Test 3 - Tunneling")

    # Camera
    cam = create_obj("Main Camera", [400, 0])
    add_camera(cam, zoom=0.6)
    scene["objects"].append(cam)
    
    # Walls (Thin)
    for i in range(5):
        wall = create_obj(f"Wall_{i}", [200 + (i*100), 0], scale=[0.1, 2]) # Visual: 10x200
        add_box_collider(wall, 10, 200) # Wall 10px wide
        add_renderer(wall, [200, 200, 200, 255])
        scene["objects"].append(wall)
        
    # Bullet
    bullet = create_obj("Bullet", [-300, 0], scale=[0.2, 0.2]) # Visual 20x20
    add_circle_collider(bullet, 10) # Radius 10 -> 20 dim
    add_rigidbody(bullet, mass=0.1, velocity=[2000, 0]) 
    add_renderer(bullet, [255, 0, 0, 255])
    scene["objects"].append(bullet)

    with open("scenes/stress_3_speed.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# 4. FRICTION SLOPES
def gen_friction():
    scene = create_scene("Stress Test 4 - Friction Slopes")

    # Camera
    cam = create_obj("Main Camera", [-150, 0])
    add_camera(cam, zoom=0.8)
    scene["objects"].append(cam)
    
    frictions = [0.0, 0.5, 1.0]
    
    for i, fric in enumerate(frictions):
        y_off = i * 150 - 150
        
        # Ramp
        ramp = create_obj(f"Ramp_{fric}", [-100, y_off], rot=25, scale=[3, 0.2]) # Visual: 300 x 20
        add_box_collider(ramp, 300, 20)
        add_rigidbody(ramp, dynamic=False, friction=fric) 
        add_renderer(ramp, [100, 100, 200, 255])
        scene["objects"].append(ramp)
        
        # Slider
        slider = create_obj(f"Slider_{fric}", [-200, y_off - 100], scale=[0.3, 0.3]) # Visual 30x30
        add_box_collider(slider, 30, 30)
        add_rigidbody(slider, friction=fric)
        add_renderer(slider, [255, 255, 0, 255])
        scene["objects"].append(slider)

    with open("scenes/stress_4_friction.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

# 5. MASS MAYHEM
def gen_mass():
    scene = create_scene("Stress Test 5 - Mass Mayhem")

    # Camera
    cam = create_obj("Main Camera", [0, 0])
    add_camera(cam, zoom=0.8)
    scene["objects"].append(cam)
    
    ground = create_obj("Ground", [0, 300], scale=[20, 0.5]) # Visual 2000x50
    add_box_collider(ground, 2000, 50)
    add_rigidbody(ground, dynamic=False, restitution=0.1) # Decouple from heavy objects
    add_renderer(ground, [100, 100, 100, 255])
    scene["objects"].append(ground)
    
    # Heavy Weight
    heavy = create_obj("Heavy", [0, -300], scale=[1.5, 1.5]) # Visual 150x150
    add_box_collider(heavy, 150, 150)
    add_rigidbody(heavy, mass=100.0)
    add_renderer(heavy, [50, 50, 50, 255])
    scene["objects"].append(heavy)
    
    # Light Box in middle
    light = create_obj("Light", [0, 250], scale=[0.5, 0.5]) # Visual 50x50
    add_box_collider(light, 50, 50)
    add_rigidbody(light, mass=0.1)
    add_renderer(light, [200, 200, 255, 255])
    scene["objects"].append(light)

    with open("scenes/stress_5_mass.scene.json", "w") as f:
        json.dump(scene, f, indent=2)

if __name__ == "__main__":
    gen_tower()
    gen_bounce()
    gen_speed()
    gen_friction()
    gen_mass()
    print("Generated 5 Stress Test Scenes in scenes/")
