import pygame
import sys
import os
import json
import importlib.util
import inspect
import math

# Add project root to path
# Use shared path utility to locate root
try:
    from shared.paths import get_engine_root
    PROJECT_ROOT = get_engine_root()
except ImportError:
    # Fallback if shared not in path yet (e.g. running directly)
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from shared.scene_schema import Scene
from shared.scene_loader import load_scene
from runtime.api import GameObject, Script, Input, Time
from runtime.physics import PhysicsSystem

# --- Native Engine-Prebaked Scripts ---
class CameraFollow(Script):
    target_name = "Player"
    smooth_speed = 5.0
    offset_x = 0.0
    offset_y = 0.0

    def start(self):
        self.target = self.find_object(self.target_name)

    def update(self, dt):
        if not self.target:
            self.target = self.find_object(self.target_name)
            if not self.target:
                return

        cx, cy = self.game_object.position
        tx, ty = self.target.world_position
        tx += self.offset_x
        ty += self.offset_y

        dx = tx - cx
        dy = ty - cy

        if abs(dx) > 0.1 or abs(dy) > 0.1:
            self.game_object.position[0] += dx * self.smooth_speed * dt
            self.game_object.position[1] += dy * self.smooth_speed * dt


class AutoRestart(Script):
    target_name = "Knight Player"
    scene_path = "scenes/showcase_demo.scene.json"
    fall_threshold = 700.0
    restart_delay = 1.5

    def start(self):
        self._timer = 0.0
        self._restarting = False
        self._target = None

    def update(self, dt):
        if not self._target:
            self._target = self.find_object(self.target_name)
            if not self._target:
                return

        py = self._target.world_position[1]

        if not self._restarting and py > self.fall_threshold:
            self._restarting = True
            self._timer = 0.0

        if self._restarting:
            self._timer += dt
            if self._timer >= self.restart_delay:
                self.load_scene(self.scene_path)


class SideScrollPlayer(Script):
    jump_force = -420.0
    move_speed = 220.0

    def start(self):
        self.set_anim_parameter("speed", 0.0)

    def update(self, dt):
        rb = self.game_object.components.get("RigidBody")
        if not rb:
            return

        current_vel = rb.get("velocity", [0.0, 0.0])
        vx = current_vel[0]
        vy = current_vel[1]

        target_vx = 0.0
        moving = False
        if Input.get_key(pygame.K_a):
            target_vx = -self.move_speed
            moving = True
            if self.transform.scale[0] > 0:
                self.transform.scale[0] = -self.transform.scale[0]
        elif Input.get_key(pygame.K_d):
            target_vx = self.move_speed
            moving = True
            if self.transform.scale[0] < 0:
                self.transform.scale[0] = -self.transform.scale[0]

        vx = target_vx

        if (Input.get_key(pygame.K_w) or Input.get_key(pygame.K_SPACE)) and abs(vy) < 8.0:
            vy = self.jump_force

        rb["velocity"] = [vx, vy]
        self.set_anim_parameter("speed", 1.0 if moving else 0.0)


NATIVE_SCRIPTS = {
    "camerafollow": CameraFollow,
    "camera_follow": CameraFollow,
    "scripts/camera_follow.py": CameraFollow,
    "autorestart": AutoRestart,
    "auto_restart": AutoRestart,
    "scripts/autorestart.py": AutoRestart,
    "sidescrollplayer": SideScrollPlayer,
    "side_scroll_player": SideScrollPlayer,
    "scripts/sidescrollplayer.py": SideScrollPlayer,
}


# --- Radial Gradient Light Generator & Cache for high performance ---
_master_light_surface = None
_light_surface_cache = {}

def get_master_light_surface():
    global _master_light_surface
    if _master_light_surface is None:
        RES = 512
        HALF = RES // 2
        _master_light_surface = pygame.Surface((RES, RES), pygame.SRCALPHA)
        for x in range(RES):
            for y in range(RES):
                dx = x - HALF
                dy = y - HALF
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= HALF:
                    t = dist / float(HALF)
                    val = 1.0 - t * t
                    factor = val * val
                    alpha = int(255 * factor)
                    color_val = int(255 * factor)
                    _master_light_surface.set_at((x, y), (color_val, color_val, color_val, alpha))
    return _master_light_surface

def get_light_source_surface(radius, color, intensity):
    radius = max(1, min(2000, int(radius)))
    color_tuple = tuple(color[:3])
    # Quantize intensity to 2 decimal places to limit cache size
    # and avoid scaling lag on dynamic lights while keeping transitions silky smooth
    q_intensity = max(0.0, round(float(intensity), 2))
    key = (radius, color_tuple, q_intensity)
    
    if key not in _light_surface_cache:
        master = get_master_light_surface()
        size = int(radius * 2)
        scaled = pygame.transform.smoothscale(master, (size, size))
        
        # 1. Create a fully tinted light base (full RGB strength)
        tinted = pygame.Surface((size, size), pygame.SRCALPHA)
        tinted.fill(color_tuple + (255,))
        
        # 2. Multiply with the radial gradient to apply shape
        tinted.blit(scaled, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # 3. Apply intensity (allows values > 1.0 to expand core, and values < 1.0 to dim it)
        if q_intensity != 1.0:
            boosted = pygame.Surface((size, size), pygame.SRCALPHA)
            full_passes = int(q_intensity)
            fraction = q_intensity - full_passes
            
            # Add full intensity layers
            for _ in range(full_passes):
                boosted.blit(tinted, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                
            # Add fractional intensity layer if needed
            if fraction > 0.0:
                frac_surf = tinted.copy()
                f_val = int(255 * fraction)
                frac_surf.fill((f_val, f_val, f_val, f_val), special_flags=pygame.BLEND_RGBA_MULT)
                boosted.blit(frac_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                
            tinted = boosted
            
        _light_surface_cache[key] = tinted
        
    return _light_surface_cache[key]


# --- 2D Dynamic Shadow Casting & Raycast Visibility Polygons ---
def get_ray_intersection(p, d, a, b):
    # p is start of ray (px, py)
    # d is direction vector (dx, dy)
    # a, b are endpoints of segment
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = d
    
    denominator = dy * (bx - ax) - dx * (by - ay)
    if abs(denominator) < 1e-6:
        return None # Parallel
        
    t = ((ay - py) * (bx - ax) - (ax - px) * (by - ay)) / denominator
    u = (dx * (ay - py) - dy * (ax - px)) / denominator
    
    if t >= 0 and 0.0 <= u <= 1.0:
        return t
    return None

def extract_segments(objects, light_pos, light_radius, ignore_obj=None):
    segments = []
    
    lx, ly = light_pos
    r = light_radius + 50 # Buffer
    
    # Large boundary box around the light coordinates to bound all rays
    segments.append(((lx - r, ly - r), (lx + r, ly - r)))
    segments.append(((lx + r, ly - r), (lx + r, ly + r)))
    segments.append(((lx + r, ly + r), (lx - r, ly + r)))
    segments.append(((lx - r, ly + r), (lx - r, ly - r)))
    
    for go in objects:
        if go == ignore_obj:
            continue
            
        # Spatial culling (broad phase distance check) using world position
        wpos = go.world_position
        dist = math.sqrt((wpos[0] - lx)**2 + (wpos[1] - ly)**2)
        if dist > light_radius + 300:
            continue
            
        pos = wpos
        rot = go.world_rotation
        scale = go.world_scale
        
        # 1. BoxCollider
        box = go.components.get("BoxCollider")
        if box:
            size = box.get("size", [50.0, 50.0])
            offset = box.get("offset", [0.0, 0.0])
            
            width = size[0] * abs(scale[0])
            height = size[1] * abs(scale[1])
            ox = offset[0] * scale[0]
            oy = offset[1] * scale[1]
            
            l, r_side = ox - width/2, ox + width/2
            t, b = oy - height/2, oy + height/2
            
            local_verts = [(l, t), (r_side, t), (r_side, b), (l, b)]
            world_verts = []
            
            for lx_i, ly_i in local_verts:
                rad = math.radians(rot)
                rx = lx_i * math.cos(rad) - ly_i * math.sin(rad)
                ry = lx_i * math.sin(rad) + ly_i * math.cos(rad)
                world_verts.append((pos[0] + rx, pos[1] + ry))
                
            for i in range(4):
                segments.append((world_verts[i], world_verts[(i + 1) % 4]))
                
        # 2. CircleCollider (approximated as regular octagon)
        circle = go.components.get("CircleCollider")
        if circle:
            radius = circle.get("radius", 25.0)
            offset = circle.get("offset", [0.0, 0.0])
            
            max_scale = max(abs(scale[0]), abs(scale[1]))
            final_radius = radius * max_scale
            ox = offset[0] * scale[0]
            oy = offset[1] * scale[1]
            
            world_verts = []
            for angle_deg in range(0, 360, 45):
                angle_rad = math.radians(angle_deg)
                lx_i = ox + final_radius * math.cos(angle_rad)
                ly_i = oy + final_radius * math.sin(angle_rad)
                
                rad = math.radians(rot)
                rx = lx_i * math.cos(rad) - ly_i * math.sin(rad)
                ry = lx_i * math.sin(rad) + ly_i * math.cos(rad)
                world_verts.append((pos[0] + rx, pos[1] + ry))
                
            for i in range(8):
                segments.append((world_verts[i], world_verts[(i + 1) % 8]))
                
    return segments

def compute_visibility_polygon(light_pos, radius, segments):
    px, py = light_pos
    
    vertices = set()
    for a, b in segments:
        vertices.add(a)
        vertices.add(b)
        
    angles = set()
    for vx, vy in vertices:
        angle = math.atan2(vy - py, vx - px)
        angles.add(angle)
        angles.add(angle - 0.0001)
        angles.add(angle + 0.0001)
        
    for angle_deg in range(0, 360, 90):
        angles.add(math.radians(angle_deg))
        
    intersection_points = []
    
    for angle in angles:
        dx = math.cos(angle)
        dy = math.sin(angle)
        
        closest_t = radius # Default to radius boundary
        
        for a, b in segments:
            t = get_ray_intersection(light_pos, (dx, dy), a, b)
            if t is not None and t < closest_t:
                closest_t = t
                
        ix = px + closest_t * dx
        iy = py + closest_t * dy
        intersection_points.append((ix, iy))
        
    # Sort clockwise
    intersection_points.sort(key=lambda pt: math.atan2(pt[1] - py, pt[0] - px))
    return intersection_points

class GameRuntime:
    def __init__(self, scene_path, width=800, height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Aspis Engine Runtime")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.scene_path = scene_path
        self.active_scripts = [] # List of instantiated Script objects
        self.sprites = {} # path -> surface
        self.objects = [] # List of runtime GameObject instances
        
        self.physics = PhysicsSystem()
        
        # Lifecycle Queues
        self.instantiate_queue = [] # List of (prefab, pos, rot)
        self.destroy_queue = [] # List of GameObjects
        self.next_scene_path = None
        
        # Audio
        pygame.mixer.init()
        
        # Joysticks / Gamepads
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joyst in self.joysticks:
            joyst.init()
        
        self.load_level()
        self.start_scripts()

    def _inject_api(self, script_instance):
        """Injects runtime methods into the script instance."""
        def inst(prefab, pos, rot=0):
            return self._perform_instantiate(prefab, pos, rot)
        
        def dest(obj):
            self.destroy_queue.append(obj)
            
        def load(name):
            # Assume name is path relative to PROJECT_ROOT or simple name?
            # Let's assume full path or relative to project
            self.next_scene_path = os.path.join(PROJECT_ROOT, name)
            
        def play_snd(path):
            full_path = os.path.join(PROJECT_ROOT, path)
            if os.path.exists(full_path):
                pygame.mixer.Sound(full_path).play()
        
        def find_obj(name):
            for obj in self.objects:
                if obj.name == name:
                    return obj
            return None

        def find_objs_with_tag(tag):
            matches = []
            for obj in self.objects:
                if obj.tag == tag:
                    matches.append(obj)
            return matches

        def play_anim(name):
            anim_data = script_instance.game_object.components.get("Animator")
            if anim_data:
                anim_data["current_state"] = name
                anim_data["_current_frame_index"] = 0
                anim_data["_elapsed_time"] = 0.0
        
        def set_param(p_name, val):
            anim_data = script_instance.game_object.components.get("Animator")
            if anim_data and "_parameters" in anim_data:
                anim_data["_parameters"][p_name] = val
                
        def get_param(p_name):
            anim_data = script_instance.game_object.components.get("Animator")
            if anim_data and "_parameters" in anim_data:
                return anim_data["_parameters"].get(p_name)
            return None
        
        script_instance.instantiate = inst
        script_instance.destroy = dest
        script_instance.load_scene = load
        script_instance.play_sound = play_snd
        script_instance.find_object = find_obj
        script_instance.find_objects_with_tag = find_objs_with_tag
        script_instance.play_animation = play_anim
        script_instance.set_anim_parameter = set_param
        script_instance.get_anim_parameter = get_param




    def run(self):
        FIXED_DT = 1.0 / 120.0 # 120 Hz fixed logic update (Sub-stepping)
        accumulator = 0.0
        
        while self.running:
            # 1. Frame time measurement
            frame_time = self.clock.tick(60) / 1000.0
            if frame_time > 0.25: frame_time = 0.25 # Prevent spiral of death
            
            self.handle_events()
            
            # 2. Accumulate time
            accumulator += frame_time
            
            # 3. Fixed Update Loop (Physics + Scripts)
            while accumulator >= FIXED_DT:
                Time.dt = FIXED_DT
                
                # Physics Step
                events = self.physics.update(FIXED_DT, self.objects)
                self.dispatch_collision_events(events)
                
                # Scripts Step (Fixed Update)
                self.update_scripts(FIXED_DT)
                
                # Animators Step (Update states and frame indices)
                self.update_animators(FIXED_DT)
                
                # Processing Queued Lifecycle Events
                self.process_lifecycle_events()
                
                accumulator -= FIXED_DT
            
            # 4. Rendering (Variable rate)
            # Future: Interpolate (alpha = accumulator / FIXED_DT)
            self.draw()
        
        pygame.quit()
        sys.exit()

    def process_lifecycle_events(self):
        # 1. Instantiate
        while self.instantiate_queue:
            prefab_path, pos, rot = self.instantiate_queue.pop(0)
            self._perform_instantiate(prefab_path, pos, rot)
            
        # 2. Destroy
        if self.destroy_queue:
            # Rebuild lists excluding destroyed objects
            # Logic: Remove from objects list, active_scripts list, and physics bodies
            
            ids_to_destroy = set(obj.id for obj in self.destroy_queue)
            print(f"DEBUG: Processing destruction for {len(ids_to_destroy)} objects.")
            
            # Recursive destroy logic? For now, flat.
            # Actually, we need to handle children too if we support hierarchy destroy.
            # Let's assume user passes root.
            
            # Remove from Objects List
            self.objects = [obj for obj in self.objects if obj.id not in ids_to_destroy]
            
            # Remove Scripts
            self.active_scripts = [s for s in self.active_scripts if s.game_object.id not in ids_to_destroy]
            
            # Remove Physics
            for obj_id in ids_to_destroy:
                if obj_id in self.physics.bodies:
                    body = self.physics.bodies[obj_id]
                    self.physics.space.remove(body, *body.shapes)
                    del self.physics.bodies[obj_id]
            
            self.destroy_queue.clear()

        # 3. Scene Load
        if self.next_scene_path:
            self.scene_path = self.next_scene_path
            self.next_scene_path = None
            # Reset everything
            self.active_scripts.clear()
            self.objects.clear()
            self.physics = PhysicsSystem() # Reset physics world
            self.sprites.clear()
            self.load_level()
            self.start_scripts()

    def _perform_instantiate(self, prefab_path, pos, rot):
        full_path = os.path.join(PROJECT_ROOT, prefab_path)
        if not os.path.exists(full_path):
            print(f"Error: Prefab not found {prefab_path}")
            return None
            
        try:
            with open(full_path, 'r') as f:
                data = json.load(f)
            
            # Assign new ID
            import uuid
            data["id"] = str(uuid.uuid4())
            
            # Override Transform
            if "components" not in data: data["components"] = {}
            if "Transform" not in data["components"]: data["components"]["Transform"] = {}
            
            data["components"]["Transform"]["position"] = list(pos)
            data["components"]["Transform"]["rotation"] = rot
            
            # Create GameObject (Parsing logic reused? Should extract 'create_game_object' from load_level...)
            # For MVP, duping the creation logic quickly
            comps = data["components"]
            transform = comps["Transform"]
            scale = transform.get("scale", [1, 1])
            
            go = GameObject(data["id"], data.get("name", "Clone"), list(pos), rot, scale, tag=data.get("tag", ""))
            
            # Components
            for comp_name, comp_data in comps.items():
                if comp_name != "Transform":
                    if isinstance(comp_data, dict):
                        go.components[comp_name] = comp_data.copy()
                    else:
                        go.components[comp_name] = comp_data
            
            self.objects.append(go)
            
            # Load Assets
            if "SpriteRenderer" in comps:
                path = comps["SpriteRenderer"].get("sprite_path")
                if path:
                    fp = os.path.join(PROJECT_ROOT, path)
                    if fp not in self.sprites and os.path.exists(fp):
                        self.sprites[fp] = pygame.image.load(fp).convert_alpha()

            # Init Script
            if "Script" in comps:
                self.load_script(comps["Script"].get("script_path"), go)
                # Verify start() is called for new scripts? 
                # Yes, we need to call start() on just this new script.
                # Find the last added script
                if self.active_scripts and self.active_scripts[-1].game_object == go:
                    try:
                        self.active_scripts[-1].start()
                        # Inject methods
                        self._inject_api(self.active_scripts[-1])
                    except Exception as e:
                        print(f"Error starting instantiated script: {e}")
            
            return go
            
        except Exception as e:
            print(f"Error instantiating {prefab_path}: {e}")
            return None

    def dispatch_collision_events(self, events):
        for obj, other in events:
            # Find script attached to obj
            # Iterate backwards or copy list if we might remove scripts? 
            # Dispatch happens? scripts don't usually self-destruct in collision but catch errors anyway
            for script in self.active_scripts[:]: # Copy list for safety
                if script.game_object == obj:
                    try:
                        script.on_collision_enter(other)
                    except Exception as e:
                        print(f"CRASH: Script '{type(script).__name__}' on '{obj.name}' failed in on_collision_enter: {e}")
                        self._disable_crashing_script(script)

    def update_scripts(self, dt):
        # We iterate a copy because we might remove scripts if they crash
        for script in self.active_scripts[:]:
            try:
                script.update(dt)
            except Exception as e:
                print(f"CRASH: Script '{type(script).__name__}' on '{script.game_object.name}' failed in update: {e}")
                self._disable_crashing_script(script)

    def _disable_crashing_script(self, script):
        """Safely removes a crashing script to keep the engine stable."""
        if script in self.active_scripts:
            self.active_scripts.remove(script)
            print(f"SANDBOX: Disabled script '{type(script).__name__}' on '{script.game_object.name}' due to error.")

    def update_animators(self, dt):
        for go in self.objects:
            anim_data = go.components.get("Animator")
            if not anim_data:
                continue
            
            # 1. Update State Transitions based on current parameters
            current_state = anim_data.get("current_state", "")
            animations = anim_data.get("animations", {})
            transitions = anim_data.get("transitions", [])
            parameters = anim_data.get("_parameters", {})
            
            state_changed = False
            for trans in transitions:
                if trans.get("from_state") != current_state:
                    continue
                
                # Evaluate conditions
                conditions = trans.get("conditions", [])
                conditions_met = True
                
                for cond in conditions:
                    p_name = cond.get("parameter")
                    p_op = cond.get("operator", "equals")
                    target_val = cond.get("value")
                    
                    if p_name not in parameters:
                        conditions_met = False
                        break
                    
                    current_val = parameters[p_name]
                    
                    # Evaluate based on operator
                    if p_op == "greater":
                        if not (isinstance(current_val, (int, float)) and isinstance(target_val, (int, float)) and current_val > target_val):
                            conditions_met = False
                    elif p_op == "less":
                        if not (isinstance(current_val, (int, float)) and isinstance(target_val, (int, float)) and current_val < target_val):
                            conditions_met = False
                    elif p_op == "equals":
                        if current_val != target_val:
                            conditions_met = False
                    elif p_op == "not_equals":
                        if current_val == target_val:
                            conditions_met = False
                    elif p_op == "true":
                        if current_val is not True:
                            conditions_met = False
                    elif p_op == "false":
                        if current_val is not False:
                            conditions_met = False
                    elif p_op == "fired":
                        # Triggers: if True, then condition met
                        if not current_val:
                            conditions_met = False
                    else:
                        conditions_met = False
                
                if conditions_met:
                    # Reset trigger parameters
                    for cond in conditions:
                        p_name = cond.get("parameter")
                        design_param = anim_data.get("parameters", {}).get(p_name, {})
                        if design_param.get("type") == "trigger":
                            parameters[p_name] = False
                    
                    # Transition to new state
                    anim_data["current_state"] = trans.get("to_state")
                    anim_data["_current_frame_index"] = 0
                    anim_data["_elapsed_time"] = 0.0
                    state_changed = True
                    break
            
            # 2. Update frame advancement for the active animation
            current_state = anim_data.get("current_state", "")
            if not current_state or current_state not in animations:
                continue
                
            anim_info = animations[current_state]
            frames = anim_info.get("frames", [0])
            if not frames:
                continue
                
            fps = anim_info.get("frame_rate", 10.0)
            if fps <= 0.0:
                continue
                
            sec_per_frame = 1.0 / fps
            anim_data["_elapsed_time"] += dt
            
            if anim_data["_elapsed_time"] >= sec_per_frame:
                steps = int(anim_data["_elapsed_time"] / sec_per_frame)
                anim_data["_elapsed_time"] -= steps * sec_per_frame
                
                new_idx = anim_data["_current_frame_index"] + steps
                loop = anim_info.get("loop", True)
                
                if new_idx >= len(frames):
                    if loop:
                        anim_data["_current_frame_index"] = new_idx % len(frames)
                    else:
                        anim_data["_current_frame_index"] = len(frames) - 1
                else:
                    anim_data["_current_frame_index"] = new_idx

    def load_script(self, script_path, game_object):
        """Dynamically load a script file and instantiate its Script class."""
        try:
            # Check native prebaked scripts first
            norm_key = script_path.replace("\\", "/").lower()
            cls = None
            for key, native_cls in NATIVE_SCRIPTS.items():
                if key.lower() == norm_key or os.path.splitext(os.path.basename(key))[0].lower() == os.path.splitext(os.path.basename(script_path))[0].lower():
                    cls = native_cls
                    break
            
            if cls:
                instance = cls()
                instance.game_object = game_object
                instance.transform = game_object # Alias for convenience
                
                # Inject properties from Inspector
                if "Script" in game_object.components:
                    props = game_object.components["Script"].get("properties", {})
                    for key, value in props.items():
                        setattr(instance, key, value)
                        
                self.active_scripts.append(instance)
                
                # Call Awake() immediately
                if hasattr(instance, "awake"):
                    try:
                        instance.awake()
                    except Exception as e:
                        print(f"Error in Awake() of {cls.__name__}: {e}")
                
                print(f"Attached native script {cls.__name__} to {game_object.name}")
                return

            full_path = os.path.join(PROJECT_ROOT, script_path)
            if not os.path.exists(full_path):
                print(f"Script file not found: {full_path}")
                return

            module_name = os.path.splitext(os.path.basename(script_path))[0]
            spec = importlib.util.spec_from_file_location(module_name, full_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find class inheriting from Script
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Script) and obj is not Script:
                    # Instantiate
                    instance = obj()
                    instance.game_object = game_object
                    instance.transform = game_object # Alias for convenience
                    
                    # Inject properties from Inspector
                    if "Script" in game_object.components:
                        props = game_object.components["Script"].get("properties", {})
                        for key, value in props.items():
                            setattr(instance, key, value)
                            
                    self.active_scripts.append(instance)
                    
                    # Call Awake() immediately
                    if hasattr(instance, "awake"):
                        try:
                            instance.awake()
                        except Exception as e:
                            print(f"Error in Awake() of {name}: {e}")

                    print(f"Attached script {name} to {game_object.name}")
                    return

        except Exception as e:
            print(f"Error loading script {script_path}: {e}")

    def load_level(self):
        try:
            print(f"Loading scene: {self.scene_path}")
            data = load_scene(self.scene_path)
            self.scene_settings = data.get("settings", {})
            
            # Sort objects for rendering order
            raw_objects = data.get("objects", [])
            
            # 0. Load and merge prefabs
            for obj_data in raw_objects:
                prefab_path = obj_data.get("prefab")
                if prefab_path:
                    full_prefab_path = os.path.join(PROJECT_ROOT, prefab_path)
                    if os.path.exists(full_prefab_path):
                        try:
                            with open(full_prefab_path, 'r') as pf:
                                prefab_data = json.load(pf)
                            prefab_comps = prefab_data.get("components", {})
                            if "components" not in obj_data:
                                obj_data["components"] = {}
                            
                            # Deep copy/merge prefab components into object components
                            for comp_name, comp_val in prefab_comps.items():
                                if comp_name not in obj_data["components"]:
                                    obj_data["components"][comp_name] = json.loads(json.dumps(comp_val))
                                else:
                                    # Override specific fields in existing component
                                    for prop_name, prop_val in comp_val.items():
                                        if prop_name not in obj_data["components"][comp_name]:
                                            obj_data["components"][comp_name][prop_name] = prop_val
                        except Exception as pe:
                            print(f"Error loading prefab {prefab_path}: {pe}")
                            
            raw_objects.sort(key=lambda o: 
                o.get("components", {}).get("SpriteRenderer", {}).get("layer", 0))
            
            for obj_data in raw_objects:
                if not obj_data.get("active", True):
                    continue
                
                # Create Runtime GameObject
                comps = obj_data.get("components", {})
                transform = comps.get("Transform", {})
                
                pos = transform.get("position", [0, 0])
                rot = transform.get("rotation", 0)
                scale = transform.get("scale", [1, 1])
                
                go = GameObject(
                    obj_data["id"], 
                    obj_data["name"], 
                    pos, rot, scale,
                    tag=obj_data.get("tag", "")
                )
                
                # Load Sprite
                if "SpriteRenderer" in comps:
                    sprite_data = comps["SpriteRenderer"]
                    go.components["SpriteRenderer"] = sprite_data
                    
                    if sprite_data.get("visible", True):
                        path = sprite_data.get("sprite_path")
                        if path:
                            full_path = os.path.join(PROJECT_ROOT, path)
                            if full_path not in self.sprites:
                                if os.path.exists(full_path):
                                    self.sprites[full_path] = pygame.image.load(full_path).convert_alpha()
                                else:
                                    print(f"Warning: Sprite not found: {full_path}")
                                    self.sprites[full_path] = None
                
                # Load Background
                if "Background" in comps:
                    bg_data = comps["Background"]
                    go.components["Background"] = bg_data
                    # Load Sprite if needed
                    path = bg_data.get("sprite_path")
                    if path:
                        full_path = os.path.join(PROJECT_ROOT, path)
                        if full_path not in self.sprites:
                             if os.path.exists(full_path):
                                 self.sprites[full_path] = pygame.image.load(full_path).convert_alpha()
                             else:
                                 # print(f"Warning: Background Sprite not found: {full_path}")
                                 pass 

                # Load Script
                if "Script" in comps:
                    go.components["Script"] = comps["Script"] # Store for access
                    script_path = comps["Script"].get("script_path")
                    if script_path:
                        self.load_script(script_path, go)

                # Load Physics Components
                if "RigidBody" in comps:
                    go.components["RigidBody"] = comps["RigidBody"]
                
                if "BoxCollider" in comps:
                    go.components["BoxCollider"] = comps["BoxCollider"]
                
                if "CircleCollider" in comps:
                    go.components["CircleCollider"] = comps["CircleCollider"]
                
                if "Camera" in comps:
                    go.components["Camera"] = comps["Camera"]
                
                if "TextRenderer" in comps:
                    go.components["TextRenderer"] = comps["TextRenderer"]

                if "LightSource" in comps:
                    go.components["LightSource"] = comps["LightSource"]

                if "Animator" in comps:
                    anim_data = comps["Animator"]
                    go.components["Animator"] = anim_data
                    
                    # Initialize runtime variables in component dictionary
                    anim_data["_current_frame_index"] = 0
                    anim_data["_elapsed_time"] = 0.0
                    anim_data["_parameters"] = {}
                    
                    # Pre-populate parameters from design values
                    design_params = anim_data.get("parameters", {})
                    for p_name, p_info in design_params.items():
                        anim_data["_parameters"][p_name] = p_info.get("value")
                    
                    # Load sheet
                    sheet_path = anim_data.get("sprite_sheet")
                    if sheet_path:
                        full_path = os.path.join(PROJECT_ROOT, sheet_path)
                        if full_path not in self.sprites:
                            if os.path.exists(full_path):
                                self.sprites[full_path] = pygame.image.load(full_path).convert_alpha()
                            else:
                                print(f"Warning: Sprite Sheet not found: {full_path}")
                                self.sprites[full_path] = None

                self.objects.append(go)

            # 2nd Pass: Link Hierarchy
            obj_map = {obj.id: obj for obj in self.objects}
            for obj_data in raw_objects:
                obj_id = obj_data["id"]
                parent_id = obj_data.get("parent")
                
                if obj_id in obj_map and parent_id and parent_id in obj_map:
                    child = obj_map[obj_id]
                    parent = obj_map[parent_id]
                    
                    child.parent = parent
                    parent.children.append(child)
                            
        except Exception as e:
            print(f"Failed to load scene: {e}")
            self.running = False
            raise e

    def start_scripts(self):
        for script in self.active_scripts:
            # Inject Runtime API
            self._inject_api(script)
            
            try:
                script.start()
                
                # Re-inject properties to override defaults set in start()
                # This ensures Inspector values take precedence
                if hasattr(script, "game_object") and "Script" in script.game_object.components:
                    props = script.game_object.components["Script"].get("properties", {})
                    for key, value in props.items():
                         setattr(script, key, value)
            except Exception as e:
                print(f"Error in Start() of {script}: {e}")



    def handle_events(self):
        # 1. Save previous frame key state for edge detection
        if hasattr(Input, "_keys") and Input._keys:
            Input._previous_keys = list(Input._keys)
        else:
            Input._previous_keys = [False] * 512

        # Save previous frame mouse state
        Input._previous_mouse_buttons = tuple(Input._mouse_buttons) if hasattr(Input, "_mouse_buttons") else (False, False, False)

        # Save previous frame gamepad buttons state
        Input._previous_gamepad_buttons = dict(Input._gamepad_buttons)

        # 2. Process Pygame Event Queue
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        
        # 3. Update current Input states
        keys = pygame.key.get_pressed()
        Input._keys = [bool(keys[i]) for i in range(min(512, len(keys)))]

        Input._mouse_buttons = pygame.mouse.get_pressed()
        Input._mouse_position = pygame.mouse.get_pos()

        # Poll gamepads / joysticks
        if hasattr(self, "joysticks"):
            for i, joyst in enumerate(self.joysticks):
                try:
                    num_buttons = joyst.get_numbuttons()
                    for b in range(num_buttons):
                        Input._gamepad_buttons[(i, b)] = bool(joyst.get_button(b))
                    
                    num_axes = joyst.get_numaxes()
                    for a in range(num_axes):
                        Input._gamepad_axes[(i, a)] = float(joyst.get_axis(a))
                except pygame.error:
                    pass


    def draw(self):
        # 1. Find Main Camera
        camera_obj = None
        camera_comp = None
        for go in self.objects:
            cam = go.components.get("Camera")
            if cam and cam.get("is_main", True):
                camera_obj = go
                camera_comp = cam
                break
        
        # Default settings if no camera
        screen_w, screen_h = 800, 600
        cam_x, cam_y = 0.0, 0.0

        # Scene Settings (Background)
        bg_color = (20, 20, 20)
        if hasattr(self, "scene_settings"):
            bg_color = tuple(self.scene_settings.get("background_color", [20, 20, 20])[:3])
            
        if camera_comp:
            screen_w = int(camera_comp.get("width", 800))
            screen_h = int(camera_comp.get("height", 600))
            cam_x, cam_y = camera_obj.world_position[0], camera_obj.world_position[1]
        
        # Resize window if needed
        current_w, current_h = self.screen.get_size()
        if current_w != screen_w or current_h != screen_h:
            self.screen = pygame.display.set_mode((screen_w, screen_h))
            
        # Collect active light sources
        light_sources = []
        for go in self.objects:
            light = go.components.get("LightSource")
            if light:
                light_sources.append((go, light))
                
        has_lighting = len(light_sources) > 0 or (hasattr(self, "scene_settings") and "ambient_light" in self.scene_settings)
        
        # Surfaces
        world_surface = pygame.Surface((screen_w, screen_h))
        world_surface.fill(bg_color)
        
        fg_surface = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        fg_surface.fill((0, 0, 0, 0))
        
        ambient_color = [30, 30, 30, 255]
        if hasattr(self, "scene_settings"):
            ambient_color = self.scene_settings.get("ambient_light", [30, 30, 30, 255])
        
        center_x = screen_w / 2
        center_y = screen_h / 2
        
        def get_layer(obj):
            bg = obj.components.get("Background")
            if bg: return bg.get("layer", 1) - 1000
            sr = obj.components.get("SpriteRenderer")
            if sr: return sr.get("layer", 1)
            tr = obj.components.get("TextRenderer")
            if tr: return tr.get("layer", 1)
            return 1
            
        sorted_objects = sorted(self.objects, key=get_layer)
        
        bg_objects = []
        fg_objects = []
        for go in sorted_objects:
            if get_layer(go) < 0 or "Background" in go.components:
                bg_objects.append(go)
            else:
                fg_objects.append(go)

        # -----------------------------------------------------
        # PHASE A: Draw Background (Floor)
        # -----------------------------------------------------
        for go in bg_objects:
            pos = go.world_position
            rot = go.world_rotation 
            scale = go.world_scale
            
            bg_data = go.components.get("Background")
            if bg_data:
                path = bg_data.get("sprite_path")
                color = bg_data.get("color", [255, 255, 255, 255])
                is_fixed = bg_data.get("fixed", True)

                target_rect = None
                img = None

                if is_fixed:
                    target_rect = pygame.Rect(0, 0, screen_w, screen_h)
                else:
                    base_w, base_h = 100, 100 
                    if path and path in self.sprites:
                        base_w, base_h = self.sprites[path].get_size()
                    w = base_w * scale[0]
                    h = base_h * scale[1]
                    screen_x = (pos[0] - cam_x) + center_x
                    screen_y = (pos[1] - cam_y) + center_y
                    target_rect = pygame.Rect(0, 0, int(w), int(h))
                    target_rect.center = (screen_x, screen_y)

                if path and path in self.sprites:
                    img = self.sprites[path]
                    if img.get_size() != target_rect.size:
                        img = pygame.transform.scale(img, target_rect.size)
                    if not is_fixed and rot != 0:
                         img = pygame.transform.rotate(img, -rot)
                         new_rect = img.get_rect(center=target_rect.center)
                         target_rect = new_rect
                    if color[:3] != [255, 255, 255]:
                        img = img.copy()
                        img.fill(color[:3], special_flags=pygame.BLEND_MULT)
                    world_surface.blit(img, target_rect)
                else:
                     if is_fixed:
                         world_surface.fill(color[:3])
                     else:
                         surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
                         surf.fill(color)
                         if rot != 0:
                             surf = pygame.transform.rotate(surf, -rot)
                             target_rect = surf.get_rect(center=target_rect.center)
                         world_surface.blit(surf, target_rect)
        
        # -----------------------------------------------------
        # PHASE B: Draw Foreground Objects to fg_surface
        # -----------------------------------------------------
        for go in fg_objects:
            pos = go.world_position
            rot = go.world_rotation 
            scale = go.world_scale
            
            screen_x = (pos[0] - cam_x) + center_x
            screen_y = (pos[1] - cam_y) + center_y

            sprite_data = go.components.get("SpriteRenderer")
            anim_data = go.components.get("Animator")
            
            if (sprite_data and sprite_data.get("visible", True)) or anim_data:
                img = None
                
                # Check for Animator override first
                if anim_data:
                    sheet_path = anim_data.get("sprite_sheet")
                    full_sheet_path = os.path.join(PROJECT_ROOT, sheet_path) if sheet_path else None
                    
                    if full_sheet_path and full_sheet_path in self.sprites:
                        sheet_img = self.sprites[full_sheet_path]
                        if sheet_img:
                            fw = anim_data.get("frame_width", 32)
                            fh = anim_data.get("frame_height", 32)
                            
                            current_state = anim_data.get("current_state", "")
                            animations = anim_data.get("animations", {})
                            
                            frames = [0]
                            if current_state in animations:
                                frames = animations[current_state].get("frames", [0])
                            
                            frame_idx = anim_data.get("_current_frame_index", 0)
                            if frame_idx >= len(frames):
                                frame_idx = 0
                            
                            frame_val = frames[frame_idx] if frames else 0
                            
                            cols = sheet_img.get_width() // fw if fw > 0 else 1
                            cols = max(1, cols)
                            
                            row = frame_val // cols
                            col = frame_val % cols
                            
                            src_rect = pygame.Rect(col * fw, row * fh, fw, fh)
                            src_rect = src_rect.clip(sheet_img.get_rect())
                            if src_rect.width > 0 and src_rect.height > 0:
                                img = sheet_img.subsurface(src_rect)
                
                # Fallback to SpriteRenderer static sprite if no Animator image was loaded
                if not img and sprite_data and sprite_data.get("visible", True):
                    path = sprite_data.get("sprite_path")
                    if not path and "LightSource" in go.components:
                        continue
                        
                    if not path:
                        if "CircleCollider" in go.components:
                            circ = go.components["CircleCollider"]
                            r_px = int(circ.get("radius", 25.0))
                            diam = max(1, r_px * 2)
                            img = pygame.Surface((diam, diam), pygame.SRCALPHA)
                            pygame.draw.circle(img, (255, 255, 255), (r_px, r_px), r_px)
                        elif "BoxCollider" in go.components:
                            box = go.components["BoxCollider"]
                            bsize = box.get("size", [100.0, 100.0])
                            bw = max(1, int(bsize[0]))
                            bh = max(1, int(bsize[1]))
                            img = pygame.Surface((bw, bh), pygame.SRCALPHA)
                            img.fill((255, 255, 255))
                        else:
                            img = pygame.Surface((100, 100), pygame.SRCALPHA)
                            img.fill((255, 255, 255))
                    else:
                        full_sprite_path = os.path.join(PROJECT_ROOT, path)
                        if full_sprite_path in self.sprites:
                            img = self.sprites[full_sprite_path]
                
                if img:
                    scale_x, scale_y = scale[0], scale[1]
                    tint = [255, 255, 255, 255]
                    if sprite_data:
                        tint = sprite_data.get("tint", [255, 255, 255, 255])
                    
                    if tint != [255, 255, 255, 255]:
                        img = img.copy()
                        if tint[:3] != [255, 255, 255]:
                            img.fill((tint[0], tint[1], tint[2], 255), special_flags=pygame.BLEND_RGBA_MULT)
                        if len(tint) > 3 and tint[3] != 255:
                            img.set_alpha(tint[3])
                    
                    # Horizontal flip only - negative X scale flips the sprite
                    # Vertical axis is never flipped by scale; doing so would
                    # invert the sprite. Instead, only flip on X.
                    flip_x = scale_x < 0
                    scale_x = abs(scale_x)
                    scale_y = abs(scale_y)  # Always positive to avoid vertical inversion
                    if flip_x:
                        img = pygame.transform.flip(img, True, False)
                    
                    target_w = max(1, int(img.get_width() * scale_x))
                    target_h = max(1, int(img.get_height() * scale_y))
                    
                    if 0 < target_w < 10000 and 0 < target_h < 10000:
                        try:
                            img = pygame.transform.scale(img, (target_w, target_h))
                            if rot != 0:
                                img = pygame.transform.rotate(img, -rot)
                            rect = img.get_rect(center=(screen_x, screen_y))
                            fg_surface.blit(img, rect)
                        except:
                            pass
            
            text_data = go.components.get("TextRenderer")
            if text_data:
                text_content = text_data.get("text", "Text")
                font_size = int(text_data.get("font_size", 24))
                color = tuple(text_data.get("color", [255, 255, 255])[:3])
                
                if font_size > 0:
                    if not hasattr(self, "_font_cache"): self._font_cache = {}
                    if font_size not in self._font_cache:
                        self._font_cache[font_size] = pygame.font.SysFont("Arial", font_size)
                    
                    font = self._font_cache[font_size]
                    surf = font.render(text_content, True, color)
                    rect = surf.get_rect(center=(screen_x, screen_y))
                    fg_surface.blit(surf, rect)

        # -----------------------------------------------------
        # PHASE C: Calculate Lighting and Apply
        # -----------------------------------------------------
        if has_lighting:
            bg_light_map = pygame.Surface((screen_w, screen_h))
            bg_light_map.fill(tuple(ambient_color[:3]))
            
            fg_light_map = pygame.Surface((screen_w, screen_h))
            fg_light_map.fill(tuple(ambient_color[:3]))
            
            for go, light in light_sources:
                color = light.get("color", [255, 255, 255, 255])
                if len(color) < 4: color = list(color) + [255]
                intensity = light.get("intensity", 1.0)
                radius = light.get("radius", 200.0)
                cast_shadows = light.get("cast_shadows", True)
                
                pos = go.world_position
                
                # --- CAMERA OFF-SCREEN SPATIAL CULLING ---
                # Check if the light's bounding volume intersects the camera's viewport bounds.
                # If completely off-screen, skip heavy raycasting and blit operations completely.
                cam_half_w = screen_w / 2
                cam_half_h = screen_h / 2
                view_min_x = cam_x - cam_half_w
                view_max_x = cam_x + cam_half_w
                view_min_y = cam_y - cam_half_h
                view_max_y = cam_y + cam_half_h
                
                if (pos[0] + radius < view_min_x or pos[0] - radius > view_max_x or
                    pos[1] + radius < view_min_y or pos[1] - radius > view_max_y):
                    continue
                
                light_surf = get_light_source_surface(radius, color, intensity)
                
                type_str = light.get("type", "point").lower()
                if type_str in ["spot", "cone"]:
                    # Create a conical mask matching the object's heading
                    size = int(radius * 2)
                    mask = pygame.Surface((size, size), pygame.SRCALPHA)
                    mask.fill((0, 0, 0, 0))
                    
                    center = (radius, radius)
                    poly_points = [center]
                    
                    cone_angle = 60.0 # 60 degree field of view for the spot light
                    half_cone = cone_angle / 2.0
                    heading = go.world_rotation
                    
                    steps = 16
                    for step in range(steps + 1):
                        theta = heading - half_cone + (step * (cone_angle / steps))
                        rad = math.radians(theta)
                        px = radius + radius * math.cos(rad) * 1.5
                        py = radius + radius * math.sin(rad) * 1.5
                        poly_points.append((px, py))
                        
                    pygame.draw.polygon(mask, (255, 255, 255, 255), poly_points)
                    
                    light_surf = light_surf.copy()
                    light_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                
                screen_x = (pos[0] - cam_x) + center_x
                screen_y = (pos[1] - cam_y) + center_y
                light_rect = light_surf.get_rect(center=(int(screen_x), int(screen_y)))
                
                # Foreground objects receive pure lighting gradients (No shadows)
                fg_light_map.blit(light_surf, light_rect, special_flags=pygame.BLEND_RGBA_ADD)
                
                # Background floor receives lighting WITH shadows
                if cast_shadows:
                    segments = extract_segments(self.objects, pos, radius, ignore_obj=go)
                    world_poly = compute_visibility_polygon(pos, radius, segments)
                    
                    local_poly = []
                    for wx, wy in world_poly:
                        lx = (wx - pos[0]) + radius
                        ly = (wy - pos[1]) + radius
                        local_poly.append((lx, ly))
                        
                    if len(local_poly) >= 3:
                        shadowed_light = light_surf.copy()
                        size = int(radius * 2)
                        mask_surf = pygame.Surface((size, size), pygame.SRCALPHA)
                        mask_surf.fill((0, 0, 0, 0))
                        
                        pygame.draw.polygon(mask_surf, (255, 255, 255, 255), local_poly)
                        
                        blur_radius = max(3, int(radius * 0.06))
                        try:
                            # Use box_blur (much faster than gaussian_blur), apply 2 passes for pseudo-gaussian smoothness
                            mask_surf = pygame.transform.box_blur(mask_surf, blur_radius)
                            mask_surf = pygame.transform.box_blur(mask_surf, blur_radius)
                        except AttributeError:
                            # Fallback for older pygame
                            small_mask = pygame.transform.smoothscale(mask_surf, (size // 4, size // 4))
                            mask_surf = pygame.transform.smoothscale(small_mask, (size, size))
                        
                        shadowed_light.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        bg_light_map.blit(shadowed_light, light_rect, special_flags=pygame.BLEND_RGBA_ADD)
                else:
                    bg_light_map.blit(light_surf, light_rect, special_flags=pygame.BLEND_RGBA_ADD)
                
            # Apply background lighting multiplicatively (preserves floor colors, shades smoothly)
            world_surface.blit(bg_light_map, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            
            # Apply foreground lighting multiplicatively (preserves sprite colors, shades smoothly)
            fg_surface.blit(fg_light_map, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # -----------------------------------------------------
        # PHASE D: Output
        # -----------------------------------------------------
        world_surface.blit(fg_surface, (0, 0))
        self.screen.blit(world_surface, (0, 0))
        pygame.display.flip()

def run(scene_path):
    """Entry point for the Game Runtime"""
    # DPI Awareness for Windows
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
    
    try:
        runtime = GameRuntime(scene_path)
        runtime.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nCRITICAL ERROR: Runtime crashed - {e}")
        input("Press Enter to close window...")

if __name__ == "__main__":
    # DPI Awareness for Windows
    if len(sys.argv) > 1:
        run(sys.argv[1])
    else:
        # Default for testing
        print("No scene provided. Please provide a scene path or run from main.py.")
        input("Press Enter to close...")
