from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
import uuid
from shared.component_defs import Transform, Camera, COMPONENT_MAP # Verify import path

@dataclass
class GameObject:
    id: str
    name: str
    active: bool = True
    parent: Optional[str] = None
    components: Dict[str, Any] = field(default_factory=dict)


    @staticmethod
    def create(name: str = "New Object") -> 'GameObject':
        obj_id = str(uuid.uuid4())
        # All objects have a Transform by default
        transform = Transform()
        return GameObject(
            id=obj_id,
            name=name,
            parent=None,
            components={"Transform": asdict(transform)}
        )

@dataclass
class Scene:
    metadata: Dict[str, Any] = field(default_factory=dict)
    objects: List[Dict[str, Any]] = field(default_factory=list) # Stored as dicts for JSON
    prefabs: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=lambda: {"background_color": [20, 20, 20, 255]})

    @staticmethod
    def create_empty(name: str = "New Scene") -> 'Scene':
        # Default Main Camera
        cam = GameObject.create("Main Camera")
        cam.components["Camera"] = asdict(Camera(width=1280, height=720, is_main=True))
        cam.components["Transform"]["position"] = [0.0, 0.0]
        
        return Scene(
            metadata={"name": name, "version": 1},
            objects=[asdict(cam)],
            prefabs={},
            settings={"background_color": [20, 20, 20, 255]}
        )

    def add_object(self, obj: GameObject):
        # Convert dataclass to dict for storage if it isn't already
        if isinstance(obj, GameObject):
            self.objects.append(asdict(obj))
        else:
            self.objects.append(obj)
