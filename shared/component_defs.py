from dataclasses import dataclass, field
from typing import Tuple, Optional, List, Dict, Any

# Core component types
COMPONENT_TRANSFORM = "Transform"
COMPONENT_SPRITE_RENDERER = "SpriteRenderer"
# Physics Components
COMPONENT_BOX_COLLIDER = "BoxCollider"
COMPONENT_RIGIDBODY = "RigidBody"

COMPONENT_SCRIPT = "Script"

@dataclass
class Transform:
    position: Tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)
    parent_id: Optional[str] = None # Hierarchy support

@dataclass
class SpriteRenderer:
    sprite_path: str = ""
    layer: int = 0
    visible: bool = True
    tint: Tuple[int, int, int, int] = (255, 255, 255, 255)

@dataclass
class BoxCollider:
    size: Tuple[float, float] = (50.0, 50.0)
    offset: Tuple[float, float] = (0.0, 0.0)
    is_trigger: bool = False

@dataclass
class RigidBody:
    mass: float = 1.0
    drag: float = 0.0
    use_gravity: bool = True
    restitution: float = 0.5
    friction: float = 0.5
    fixed_rotation: bool = False
    velocity: Tuple[float, float] = (0.0, 0.0) # Runtime only

@dataclass
class CircleCollider:
    radius: float = 25.0
    offset: Tuple[float, float] = (0.0, 0.0)
    is_trigger: bool = False

@dataclass
class LightSource:
    color: List[int] = field(default_factory=lambda: [255, 255, 255, 255])
    intensity: float = 1.0
    radius: float = 200.0
    type: str = "point" # point, directional, spot

@dataclass
class Script:
    script_path: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Background:
    sprite_path: str = ""
    color: List[int] = field(default_factory=lambda: [255, 255, 255, 255])
    loop_x: bool = False
    loop_y: bool = False
    scroll_speed: List[float] = field(default_factory=lambda: [0.0, 0.0]) # Auto-scroll
    fixed: bool = True # If True, follows camera (UI space). If False, world space.
    layer: int = -100

@dataclass
class Camera:
    width: float = 800.0
    height: float = 600.0
    is_main: bool = True

# Map component names to classes for easy lookup
COMPONENT_MAP = {
    COMPONENT_TRANSFORM: Transform,
    COMPONENT_SPRITE_RENDERER: SpriteRenderer,
    COMPONENT_BOX_COLLIDER: BoxCollider,
    COMPONENT_RIGIDBODY: RigidBody,
    "CircleCollider": CircleCollider,
    "LightSource": LightSource,
    COMPONENT_SCRIPT: Script,
    "Camera": Camera,
}
