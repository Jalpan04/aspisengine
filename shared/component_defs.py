from dataclasses import dataclass, field
from typing import Tuple, Optional

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
    velocity: Tuple[float, float] = (0.0, 0.0) # Runtime only

@dataclass
class Script:
    script_path: str = ""

@dataclass
class Camera:
    width: float = 800.0
    height: float = 600.0
    zoom: float = 1.0
    is_main: bool = True

# Map component names to classes for easy lookup
COMPONENT_MAP = {
    COMPONENT_TRANSFORM: Transform,
    COMPONENT_SPRITE_RENDERER: SpriteRenderer,
    COMPONENT_BOX_COLLIDER: BoxCollider,
    COMPONENT_RIGIDBODY: RigidBody,
    COMPONENT_SCRIPT: Script,
    "Camera": Camera
}
