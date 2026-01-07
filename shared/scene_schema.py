from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import uuid
from shared.component_defs import Transform, COMPONENT_MAP

class GameObject(BaseModel):
    id: str
    name: str
    active: bool = True
    components: Dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def create(name: str = "New Object") -> 'GameObject':
        obj_id = str(uuid.uuid4())
        # All objects have a Transform by default
        transform = Transform()
        return GameObject(
            id=obj_id,
            name=name,
            components={"Transform": transform.model_dump()}
        )

class Scene(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    objects: List[Dict[str, Any]] = Field(default_factory=list) # Stored as dicts for JSON
    prefabs: Dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def create_empty(name: str = "New Scene") -> 'Scene':
        return Scene(
            metadata={"name": name, "version": 1},
            objects=[],
            prefabs={}
        )

    def add_object(self, obj: GameObject):
        # Convert model to dict for storage if it isn't already
        if isinstance(obj, GameObject):
            self.objects.append(obj.model_dump())
        else:
            self.objects.append(obj)
