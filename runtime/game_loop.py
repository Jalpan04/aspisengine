import pygame
import sys
import os
import json
import importlib.util
import inspect
import math

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(PROJECT_ROOT)

from shared.scene_schema import Scene
from shared.scene_loader import load_scene
from runtime.api import GameObject, Script, Input, Time

from runtime.physics import PhysicsSystem

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
        
        self.load_level()
        self.start_scripts()

    def _inject_api(self, script_instance):
        """Injects runtime methods into the script instance."""
        def inst(prefab, pos, rot=0):
            self.instantiate_queue.append((prefab, pos, rot))
        
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
        
        script_instance.instantiate = inst
        script_instance.destroy = dest
        script_instance.load_scene = load
        script_instance.play_sound = play_snd
        script_instance.find_object = find_obj




    def run(self):
        FIXED_DT = 1.0 / 60.0 # 60 Hz fixed logic update
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
            
            go = GameObject(data["id"], data.get("name", "Clone"), list(pos), rot, scale)
            
            # Components
            if "SpriteRenderer" in comps: go.components["SpriteRenderer"] = comps["SpriteRenderer"].copy()
            if "Script" in comps: go.components["Script"] = comps["Script"].copy()
            if "RigidBody" in comps: go.components["RigidBody"] = comps["RigidBody"].copy()
            if "BoxCollider" in comps: go.components["BoxCollider"] = comps["BoxCollider"].copy()
            if "CircleCollider" in comps: go.components["CircleCollider"] = comps["CircleCollider"].copy()
            
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

    def load_script(self, script_path, game_object):
        """Dynamically load a script file and instantiate its Script class."""
        try:
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
                    pos, rot, scale
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
        # Reset per-frame input
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
        
        # Update Input state
        keys = pygame.key.get_pressed()
        Input._keys = keys

    def update_scripts(self, dt):
        for script in self.active_scripts:
            try:
                script.update(dt)
            except Exception as e:
                print(f"Error in Update() of {script}: {e}")

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
        zoom = 1.0
        
        # Scene Settings (Background)
        bg_color = (20, 20, 20)
        # We need access to scene settings. The load_scene function returns a dict, but we parsed it into objects.
        # Ideally, we should store the scene_data or settings on the class.
        # Hack: Parse it from scene file again or store it in load_level?
        # Better: GameRuntime should have self.scene_settings
        if hasattr(self, "scene_settings"):
            bg_color = tuple(self.scene_settings.get("background_color", [20, 20, 20])[:3])
            
        if camera_comp:
            screen_w = int(camera_comp.get("width", 800))
            screen_h = int(camera_comp.get("height", 600))
            zoom = float(camera_comp.get("zoom", 1.0))
            if zoom <= 0.001: zoom = 1.0 # Safety check
            cam_x, cam_y = camera_obj.world_position[0], camera_obj.world_position[1]
        
        # Resize window if needed
        current_w, current_h = self.screen.get_size()
        if current_w != screen_w or current_h != screen_h:
            self.screen = pygame.display.set_mode((screen_w, screen_h))
            
        self.screen.fill(bg_color) 
        
        # World -> Screen: (WorldPos - CamPos) * Zoom + ScreenCenter
        center_x = screen_w / 2
        center_y = screen_h / 2
        
        # Sort objects by Layer (Z-Index)
        def get_layer(obj):
            bg = obj.components.get("Background")
            if bg: return bg.get("layer", -100)
            sr = obj.components.get("SpriteRenderer")
            if sr: return sr.get("layer", 0)
            tr = obj.components.get("TextRenderer")
            if tr: return tr.get("layer", 100) # Text defaults to top (100) to overlay sprites
            return 0
            
        sorted_objects = sorted(self.objects, key=get_layer)
        
        for go in sorted_objects:
            # Common Transform Calculation
            pos = go.world_position
            rot = go.world_rotation 
            scale = go.world_scale

            # Screen X = (ObjX - CamX) * Zoom + CenterX
            screen_x = (pos[0] - cam_x) * zoom + center_x
            screen_y = (pos[1] - cam_y) * zoom + center_y
            
            # --- 0. Background Component ---
            bg_data = go.components.get("Background")
            if bg_data:
                path = bg_data.get("sprite_path")
                color = bg_data.get("color", [255, 255, 255, 255])
                is_fixed = bg_data.get("fixed", True)

                target_rect = None
                img = None

                if is_fixed:
                    # fixed mode: Fill the screen
                    # render at (0, 0) with size (screen_w, screen_h)
                    target_rect = pygame.Rect(0, 0, screen_w, screen_h)
                else:
                    # World Space (Standard) - Use Transform
                    # Scale based on 100x100 base size if no sprite, or sprite size
                    draw_zoom = zoom
                    base_w, base_h = 100, 100 # Default size
                    
                    if path and path in self.sprites:
                        base_w, base_h = self.sprites[path].get_size()
                    
                    w = base_w * scale[0] * draw_zoom
                    h = base_h * scale[1] * draw_zoom
                    
                    screen_x = (pos[0] - cam_x) * zoom + center_x
                    screen_y = (pos[1] - cam_y) * zoom + center_y
                    
                    target_rect = pygame.Rect(0, 0, int(w), int(h))
                    target_rect.center = (screen_x, screen_y)

                # Fetch Image or Create Surface
                if path and path in self.sprites:
                    img = self.sprites[path]
                    # Scale image to target rect
                    if img.get_size() != target_rect.size:
                        img = pygame.transform.scale(img, target_rect.size)
                    
                    # Apply Rotation (only if not fixed? or allow rotating full screen bg?)
                    # Usually fixed background implies no rotation, but let's respect Transform if meaningful.
                    # For "Full Screen", rotation usually implies "Screen Shake" or similar, which applies to camera.
                    # If fixed, we probably shouldn't rotate unless local rotation is set.
                    # But rotating a full-screen quad reveals corners.
                    # Let's SKIP rotation for Fixed Backgrounds to ensure coverage.
                    if not is_fixed and rot != 0:
                         img = pygame.transform.rotate(img, -rot)
                         # Rotation changes bounds, re-center
                         new_rect = img.get_rect(center=target_rect.center)
                         target_rect = new_rect

                    # Tint
                    if color[:3] != [255, 255, 255]:
                        img = img.copy()
                        img.fill(color[:3], special_flags=pygame.BLEND_MULT)
                        
                    self.screen.blit(img, target_rect)
                    
                else:
                     # Color Fill
                     if is_fixed:
                         # Direct fill for performance
                         self.screen.fill(color[:3]) # Supports alpha? Fill usually ignores alpha on main surf?
                         # Main screen has no alpha. RGB only.
                         # If we want transparent background over... nothing? 
                         # Just fill.
                     else:
                         surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
                         surf.fill(color)
                         if rot != 0:
                             surf = pygame.transform.rotate(surf, -rot)
                             target_rect = surf.get_rect(center=target_rect.center)
                         self.screen.blit(surf, target_rect)
            
            # --- 1. Draw Sprite (if exists and visible) ---
            sprite_data = go.components.get("SpriteRenderer")
            if sprite_data and sprite_data.get("visible", True):
                path = sprite_data.get("sprite_path")
                img = None
                
                if not path:
                     # Fallback to procedural shape
                    if "CircleCollider" in go.components:
                        radius = 25 
                        img = pygame.Surface((50, 50), pygame.SRCALPHA)
                        pygame.draw.circle(img, (255, 255, 255), (25, 25), 25)
                    else:
                        img = pygame.Surface((50, 50), pygame.SRCALPHA)
                        img.fill((255, 255, 255))
                elif path in self.sprites:
                    img = self.sprites[path]
                
                if img:
                    rot = go.world_rotation
                    base_scale = go.world_scale
                    
                    # Apply Zoom to Scale
                    scale_x = base_scale[0] * zoom
                    scale_y = base_scale[1] * zoom
                    
                    # Tint
                    tint = sprite_data.get("tint", [255, 255, 255, 255])
                    if tint != [255, 255, 255, 255]:
                        img = img.copy()
                        if tint[0] != 255 or tint[1] != 255 or tint[2] != 255:
                            img.fill((tint[0], tint[1], tint[2], 255), special_flags=pygame.BLEND_RGBA_MULT)
                        if tint[3] != 255:
                            img.set_alpha(tint[3])
                    
                    # Flip
                    if scale_x < 0: 
                        img = pygame.transform.flip(img, True, False)
                        scale_x = abs(scale_x)
                    if scale_y < 0:
                        img = pygame.transform.flip(img, False, True)
                        scale_y = abs(scale_y)
                    
                    # Scale (Base size * zoom)
                    target_w = max(1, int(img.get_width() * scale_x))
                    target_h = max(1, int(img.get_height() * scale_y))
                    
                    if target_w < 10000 and target_h < 10000 and target_w > 0 and target_h > 0:
                        try:
                            img = pygame.transform.scale(img, (target_w, target_h))
                            if rot != 0:
                                img = pygame.transform.rotate(img, -rot)
                            rect = img.get_rect(center=(screen_x, screen_y))
                            self.screen.blit(img, rect)
                        except:
                            pass
            
            # 2. Draw Text (TextRenderer)
            text_data = go.components.get("TextRenderer")
            if text_data:
                text_content = text_data.get("text", "Text")
                base_font_size = int(text_data.get("font_size", 24))
                
                # Apply Zoom to Font Size
                scaled_font_size = int(base_font_size * zoom)
                
                color_list = text_data.get("color", [255, 255, 255])
                color = tuple(color_list[:3])
                
                if scaled_font_size > 0:
                    if not hasattr(self, "_font_cache"): self._font_cache = {}
                    if scaled_font_size not in self._font_cache:
                        self._font_cache[scaled_font_size] = pygame.font.SysFont("Arial", scaled_font_size)
                    
                    font = self._font_cache[scaled_font_size]
                    surf = font.render(text_content, True, color)
                    rect = surf.get_rect(center=(screen_x, screen_y))
                    self.screen.blit(surf, rect)

        pygame.display.flip()

if __name__ == "__main__":
    # DPI Awareness for Windows
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

    if len(sys.argv) > 1:
        scene_file = sys.argv[1]
        try:
            game = GameRuntime(scene_file)
            game.run()
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("\nCRITICAL ERROR: Runtime crashed.")
            input("Press Enter to close window...")
    else:
        print("Usage: python runtime/game_loop.py <path_to_scene_json>")
        input("Press Enter to close...")
