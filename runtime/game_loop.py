import pygame
import sys
import os
import json
import importlib.util
import inspect

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
        
        self.load_level()
        self.start_scripts()



    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            Time.dt = dt
            
            self.handle_events()
            
            # Physics Update
            events = self.physics.update(dt, self.objects)
            self.dispatch_collision_events(events)
            
            self.update_scripts(dt)
            self.draw() # Draw should be last
        
        pygame.quit()
        sys.exit()

    def dispatch_collision_events(self, events):
        for obj, other in events:
            # Find script attached to obj
            for script in self.active_scripts:
                if script.game_object == obj:
                    try:
                        script.on_collision_enter(other)
                    except Exception as e:
                        print(f"Error in on_collision_enter for {script}: {e}")

    def update_scripts(self, dt):
        for script in self.active_scripts:
            try:
                script.update(dt)
            except Exception as e:
                print(f"Error in Update() of {script}: {e}")

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

                self.objects.append(go)
                            
        except Exception as e:
            print(f"Failed to load scene: {e}")
            self.running = False

    def start_scripts(self):
        for script in self.active_scripts:
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
        
        if camera_comp:
            screen_w = int(camera_comp.get("width", 800))
            screen_h = int(camera_comp.get("height", 600))
            cam_x, cam_y = camera_obj.position[0], camera_obj.position[1]
        
        # Resize window if needed
        current_w, current_h = self.screen.get_size()
        if current_w != screen_w or current_h != screen_h:
            self.screen = pygame.display.set_mode((screen_w, screen_h))
            
        self.screen.fill((20, 20, 20)) 
        
        # Calculate Offset (Center camera on screen)
        # CamPos + Offset = ScreenCenter => Offset = ScreenCenter - CamPos
        offset_x = (screen_w / 2) - cam_x
        offset_y = (screen_h / 2) - cam_y
        
        cam_offset_x = int(offset_x)
        cam_offset_y = int(offset_y)
        
        # Draw World Origin (Reference)
        pygame.draw.line(self.screen, (50, 50, 50), (cam_offset_x, 0), (cam_offset_x, self.screen.get_height()))
        pygame.draw.line(self.screen, (50, 50, 50), (0, cam_offset_y), (self.screen.get_width(), cam_offset_y))
        
        for go in self.objects:
            # 1. Draw Sprite (if exists and visible)
            sprite_data = go.components.get("SpriteRenderer")
            if sprite_data and sprite_data.get("visible", True):
                path = sprite_data.get("sprite_path")
                img = None
                
                if not path:
                    # Fallback to white square if no sprite
                    img = pygame.Surface((50, 50))
                    img.fill((255, 255, 255))
                elif path in self.sprites:
                    img = self.sprites[path]
                
                if img:
                    # Apply Transform
                    pos = go.position
                    rot = go.rotation
                    scale = go.scale
                    
                    # DEBUG: Print rotation
                    # print(f"Object {go.name} Rotation: {rot}")
                    
                    # Tint
                    tint = sprite_data.get("tint", [255, 255, 255, 255])
                    if tint != [255, 255, 255, 255]:
                        img = img.copy()
                        # 1. Apply Color Tint (RGB) - Keep Alpha 255 here to not double-multiply
                        if tint[0] != 255 or tint[1] != 255 or tint[2] != 255:
                            img.fill((tint[0], tint[1], tint[2], 255), special_flags=pygame.BLEND_RGBA_MULT)
                        
                        # 2. Apply Alpha Transparency
                        if tint[3] != 255:
                            img.set_alpha(tint[3])
                    
                    # Simple handling for negative scales (flipping)
                    if scale[0] < 0: 
                        img = pygame.transform.flip(img, True, False)
                        w_scale = abs(scale[0])
                    else:
                        w_scale = scale[0]
                        
                    if scale[1] < 0:
                        img = pygame.transform.flip(img, False, True)
                        h_scale = abs(scale[1])
                    else:
                        h_scale = scale[1]
                    
                    # Scale
                    if w_scale != 1 or h_scale != 1:
                        w = int(img.get_width() * w_scale)
                        h = int(img.get_height() * h_scale)
                        if w > 0 and h > 0:
                            img = pygame.transform.scale(img, (w, h))
                    
                    # Rotate
                    if rot != 0:
                        img = pygame.transform.rotate(img, -rot)
                    
                    # Draw at position + offset
                    screen_x = pos[0] + cam_offset_x
                    screen_y = pos[1] + cam_offset_y
                    
                    rect = img.get_rect(center=(screen_x, screen_y))
                    self.screen.blit(img, rect)
            
            # 2. Debug Draw Colliders (Always, if they exist)
            if "BoxCollider" in go.components:
                pos = go.position
                col = go.components["BoxCollider"]
                size = col.get("size", [50, 50])
                offset = col.get("offset", [0, 0])
                
                # Calculate world rect
                world_x = pos[0] + offset[0] - size[0]/2
                world_y = pos[1] + offset[1] - size[1]/2
                
                # Screen rect
                debug_rect = pygame.Rect(
                    world_x + cam_offset_x,
                    world_y + cam_offset_y,
                    size[0],
                    size[1]
                )
                pygame.draw.rect(self.screen, (0, 255, 0), debug_rect, 1)
            
        pygame.display.flip()

if __name__ == "__main__":
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
