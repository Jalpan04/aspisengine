
import pygame

class Input:
    """Static helper for input."""
    _keys = [False] * 512
    _previous_keys = [False] * 512
    
    _mouse_buttons = (False, False, False)
    _previous_mouse_buttons = (False, False, False)
    _mouse_position = (0, 0)
    
    _gamepad_buttons = {}
    _previous_gamepad_buttons = {}
    _gamepad_axes = {}

    @staticmethod
    def get_key(key_code):
        try:
            return bool(Input._keys[key_code])
        except (IndexError, TypeError, KeyError):
            return False

    @staticmethod
    def get_key_down(key_code):
        try:
            return bool(Input._keys[key_code]) and not bool(Input._previous_keys[key_code])
        except (IndexError, TypeError, KeyError):
            return False

    @staticmethod
    def get_key_up(key_code):
        try:
            return not bool(Input._keys[key_code]) and bool(Input._previous_keys[key_code])
        except (IndexError, TypeError, KeyError):
            return False

    @staticmethod
    def get_mouse_position():
        return Input._mouse_position

    @staticmethod
    def get_mouse_button(button_idx):
        try:
            return bool(Input._mouse_buttons[button_idx])
        except (IndexError, TypeError):
            return False

    @staticmethod
    def get_mouse_button_down(button_idx):
        try:
            return bool(Input._mouse_buttons[button_idx]) and not bool(Input._previous_mouse_buttons[button_idx])
        except (IndexError, TypeError):
            return False

    @staticmethod
    def get_mouse_button_up(button_idx):
        try:
            return not bool(Input._mouse_buttons[button_idx]) and bool(Input._previous_mouse_buttons[button_idx])
        except (IndexError, TypeError):
            return False

    @staticmethod
    def get_button(button_idx, gamepad_id=0):
        try:
            return bool(Input._gamepad_buttons.get((gamepad_id, button_idx), False))
        except (TypeError, KeyError):
            return False

    @staticmethod
    def get_button_down(button_idx, gamepad_id=0):
        try:
            curr = Input._gamepad_buttons.get((gamepad_id, button_idx), False)
            prev = Input._previous_gamepad_buttons.get((gamepad_id, button_idx), False)
            return bool(curr) and not bool(prev)
        except (TypeError, KeyError):
            return False

    @staticmethod
    def get_button_up(button_idx, gamepad_id=0):
        try:
            curr = Input._gamepad_buttons.get((gamepad_id, button_idx), False)
            prev = Input._previous_gamepad_buttons.get((gamepad_id, button_idx), False)
            return not bool(curr) and bool(prev)
        except (TypeError, KeyError):
            return False

    @staticmethod
    def get_axis(axis_idx, gamepad_id=0):
        try:
            return float(Input._gamepad_axes.get((gamepad_id, axis_idx), 0.0))
        except (TypeError, KeyError):
            return 0.0

class Time:
    """Static helper for time."""
    dt = 0.0

class GameObject:
    def __init__(self, id, name, position, rotation, scale, tag=""):
        self.id = id
        self.name = name
        self.tag = tag
        self.position = list(position)
        self.rotation = rotation
        self.scale = list(scale)
        self.components = {}
        
        # Hierarchy
        self.parent = None
        self.children = []

    @property
    def world_position(self):
        if self.parent:
            # Simple 2D transform hierarchy
            # P_world = P_parent + Rotate(P_local, R_parent) * S_parent
            # For MVP, let's just do translation + rotation
            import math
            
            px, py = self.parent.world_position
            pr = self.parent.world_rotation
            ps = self.parent.world_scale
            
            # Local pos relative to parent
            lx = self.position[0] * ps[0]
            ly = self.position[1] * ps[1]
            
            # Rotate local pos by parent rotation
            rad = -math.radians(pr) # Negative for standard math vs screen coords? Check this.
            # Pygame rotation is degrees CCW? Standard math is CCW.
            # Let's assume standard rotation.
            
            rx = lx * math.cos(rad) - ly * math.sin(rad)
            ry = lx * math.sin(rad) + ly * math.cos(rad)
            
            return [px + rx, py + ry]
        return self.position

    @property
    def world_rotation(self):
        if self.parent:
            return self.parent.world_rotation + self.rotation
        return self.rotation

    @property
    def world_scale(self):
        if self.parent:
            ps = self.parent.world_scale
            return [self.scale[0] * ps[0], self.scale[1] * ps[1]]
        return self.scale

class Script:
    """Base class for all user scripts."""
    def __init__(self):
        self.game_object = None  # Injected by runtime
        self.transform = None    # Helper to access transform
    
    def start(self):
        """Called when the scene starts."""
        pass

    def update(self, dt):
        """Called every frame. dt is delta time in seconds."""
        pass

    def on_collision_enter(self, other):
        """Called when this object collides with another."""
        pass
        
    # --- API Methods (Delegated to Runtime) ---
    def instantiate(self, prefab_path, position, rotation=0.0):
        """Spawns a new object from a prefab."""
        # This will be monkey-patched by the runtime
        print("Warning: instantiate called outside runtime")
        return None

    def destroy(self, game_object):
        """Destroys the given game object."""
        # This will be monkey-patched by the runtime
        print("Warning: destroy called outside runtime")

    def load_scene(self, scene_name):
        """Loads a new scene."""
        # This will be monkey-patched by the runtime
        print("Warning: load_scene called outside runtime")
        
    def play_sound(self, sound_path):
        """Plays a sound one-shot."""
        # API hook
        pass

    def find_object(self, name):
        """Finds a GameObject by name."""
        # API hook
        return None

    def find_objects_with_tag(self, tag):
        """Finds all GameObjects with the given tag."""
        # API hook
        return []

    def play_animation(self, state_name):
        """Plays the specified animation state directly."""
        # Monkey-patched by runtime
        pass

    def set_anim_parameter(self, param_name, value):
        """Sets the value of an animator parameter."""
        # Monkey-patched by runtime
        pass

    def get_anim_parameter(self, param_name):
        """Gets the value of an animator parameter."""
        # Monkey-patched by runtime
        return None

class KeyCode:
    """Mapping to Pygame keys."""
    W = pygame.K_w
    A = pygame.K_a
    S = pygame.K_s
    D = pygame.K_d
    UP = pygame.K_UP
    DOWN = pygame.K_DOWN
    LEFT = pygame.K_LEFT
    RIGHT = pygame.K_RIGHT
    SPACE = pygame.K_SPACE
    ESCAPE = pygame.K_ESCAPE
