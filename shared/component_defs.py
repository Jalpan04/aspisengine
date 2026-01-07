from pydantic import BaseModel, Field, model_validator
from typing import Tuple, Optional, Any

# Core component types
COMPONENT_TRANSFORM = "Transform"
COMPONENT_SPRITE_RENDERER = "SpriteRenderer"
# Physics Components
COMPONENT_BOX_COLLIDER = "BoxCollider"
COMPONENT_RIGIDBODY = "RigidBody"
COMPONENT_SCRIPT = "Script"

class Transform(BaseModel):
    position: Tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    scale: Tuple[float, float] = (1.0, 1.0)

    @model_validator(mode='before')
    @classmethod
    def handle_aliases_and_types(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Handle x/y -> position
            x = data.pop('x', None)
            y = data.pop('y', None)
            if x is not None or y is not None:
                # If position is already there, x/y override it? Or just fill in?
                # Let's assume if x/y are provided, they build position.
                current_pos = data.get('position', (0.0, 0.0))
                # Ensure current_pos is tuple/list to access elements
                if not isinstance(current_pos, (list, tuple)):
                     current_pos = (0.0, 0.0)

                new_x = x if x is not None else current_pos[0]
                new_y = y if y is not None else current_pos[1]
                data['position'] = (float(new_x), float(new_y))

            # Handle scale as float -> tuple
            scale = data.get('scale')
            if scale is not None and isinstance(scale, (int, float)):
                data['scale'] = (float(scale), float(scale))

        return data

class SpriteRenderer(BaseModel):
    sprite_path: str = ""
    layer: int = 0
    visible: bool = True

class BoxCollider(BaseModel):
    size: Tuple[float, float] = (50.0, 50.0)
    offset: Tuple[float, float] = (0.0, 0.0)
    is_trigger: bool = False

class RigidBody(BaseModel):
    mass: float = 1.0
    drag: float = 0.0
    use_gravity: bool = True
    velocity: Tuple[float, float] = (0.0, 0.0) # Runtime only

class Script(BaseModel):
    script_path: str = ""

# Map component names to classes for easy lookup
COMPONENT_MAP = {
    COMPONENT_TRANSFORM: Transform,
    COMPONENT_SPRITE_RENDERER: SpriteRenderer,
    COMPONENT_BOX_COLLIDER: BoxCollider,
    COMPONENT_RIGIDBODY: RigidBody,
    COMPONENT_SCRIPT: Script,
}
