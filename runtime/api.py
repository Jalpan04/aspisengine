
import pygame

class Input:
    """Static helper for input."""
    _keys = {}
    
    @staticmethod
    def get_key(key_code):
        try:
            return Input._keys[key_code]
        except (IndexError, TypeError):
            return False

class Time:
    """Static helper for time."""
    dt = 0.0

class GameObject:
    def __init__(self, id, name, position, rotation, scale):
        self.id = id
        self.name = name
        self.position = list(position)
        self.rotation = rotation
        self.scale = list(scale)
        self.components = {}

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

class KeyCode:
    """Mapping to Pygame keys."""
    W = pygame.K_w
    S = pygame.K_s
    UP = pygame.K_UP
    DOWN = pygame.K_DOWN
    SPACE = pygame.K_SPACE
    ESCAPE = pygame.K_ESCAPE
