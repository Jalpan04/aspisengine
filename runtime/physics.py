from shared.component_defs import COMPONENT_RIGIDBODY, COMPONENT_BOX_COLLIDER
import pygame
import math

class SpatialHash:
    def __init__(self, cell_size=100):
        self.cell_size = cell_size
        self.cells = {}

    def _get_cell_coords(self, x, y):
        return int(x / self.cell_size), int(y / self.cell_size)

    def _get_cells_for_rect(self, rect):
        start_x, start_y = self._get_cell_coords(rect.left, rect.top)
        end_x, end_y = self._get_cell_coords(rect.right, rect.bottom)

        cells = []
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                cells.append((x, y))
        return cells

    def insert(self, item, rect):
        for cell_coord in self._get_cells_for_rect(rect):
            if cell_coord not in self.cells:
                self.cells[cell_coord] = []
            self.cells[cell_coord].append(item)

    def get_nearby(self, rect):
        nearby = set()
        for cell_coord in self._get_cells_for_rect(rect):
            if cell_coord in self.cells:
                for item in self.cells[cell_coord]:
                    nearby.add(item)
        return nearby

    def clear(self):
        self.cells.clear()


class PhysicsSystem:
    GRAVITY = 980.0  # Pixels per second squared

    def __init__(self):
        self.colliders = [] # List of wrapped collider dicts
        self.spatial_hash = SpatialHash(cell_size=128) # Tuned for typical object size

    def update(self, dt, objects):
        # 1. Integration Step (Apply Gravity & Velocity)
        for obj in objects:
            rb_data = obj.components.get(COMPONENT_RIGIDBODY)
            if not rb_data:
                continue
            
            use_gravity = rb_data.get("use_gravity", True)
            velocity = rb_data.get("velocity", [0.0, 0.0])
            
            # Apply Gravity
            if use_gravity:
                velocity[1] += self.GRAVITY * dt
            
            # Apply Drag (Simple linear drag)
            drag = rb_data.get("drag", 0.0)
            if drag > 0:
                velocity[0] *= (1.0 - drag * dt)
                velocity[1] *= (1.0 - drag * dt)
            
            # Update Position
            transform = obj.position # [x, y]
            transform[0] += velocity[0] * dt
            transform[1] += velocity[1] * dt
            
            # Save back to component
            rb_data["velocity"] = velocity

        # 2. Collision Detection
        self.colliders.clear()
        self.spatial_hash.clear()
        events = [] # List of (obj_a, obj_b)
        
        # Collect all colliders and populate Spatial Hash
        for obj in objects:
            col_data = obj.components.get(COMPONENT_BOX_COLLIDER)
            if not col_data:
                continue
                
            pos = obj.position
            size = col_data.get("size", [50, 50])
            offset = col_data.get("offset", [0, 0])
            
            # AABB
            rect = pygame.Rect(
                pos[0] + offset[0] - size[0]/2, 
                pos[1] + offset[1] - size[1]/2, 
                size[0], size[1]
            )
            
            # Store index instead of object to avoid hashing issues if dict
            # We wrap it in a tuple or object that is hashable for the set, or just use ID
            # Let's use ID or index. Since objects is a list, we can use index if stable, but ID is safer.

            collider_wrapper = {
                "id": obj.id,
                "obj": obj,
                "rect": rect,
                "is_trigger": col_data.get("is_trigger", False),
                "rb": obj.components.get(COMPONENT_RIGIDBODY)
            }

            # We need a way to store this wrapper in the set.
            # We can use the object ID as a key in a separate dict if needed,
            # but here we can just append to self.colliders and use index or ID.
            # Let's make the wrapper hashable by id

            self.colliders.append(collider_wrapper)

            # Use index for spatial hash to keep it simple and hashable (int)
            idx = len(self.colliders) - 1
            self.spatial_hash.insert(idx, rect)

        # Check collisions using Spatial Hash
        checked_pairs = set()

        for i, c1 in enumerate(self.colliders):
            potential_collisions = self.spatial_hash.get_nearby(c1["rect"])

            for j in potential_collisions:
                if i >= j: # Avoid duplicates and self-check
                    continue

                pair_id = (i, j)
                if pair_id in checked_pairs:
                    continue
                checked_pairs.add(pair_id)

                c2 = self.colliders[j]
                
                if c1["rect"].colliderect(c2["rect"]):
                    self.resolve_collision(c1, c2)
                    events.append((c1["obj"], c2["obj"]))
                    events.append((c2["obj"], c1["obj"]))
        
        return events

    def resolve_collision(self, c1, c2):
        # Physical Resolution
        # Only if both are not triggers and at least one has a rigidbody
        if c1["is_trigger"] or c2["is_trigger"]:
            return
            
        rb1 = c1["rb"]
        rb2 = c2["rb"]
        
        # If neither has rigidbody, they are both static (like two walls), do nothing
        if not rb1 and not rb2:
            return

        # Calculate overlap
        r1 = c1["rect"]
        r2 = c2["rect"]
        
        # Calculate intersection rectangle
        inter = r1.clip(r2)
        if inter.width == 0 or inter.height == 0:
            return
            
        # Minimum Translation Vector (MTV)
        if inter.width < inter.height:
            # Push horizontally
            overlap = inter.width
            if r1.centerx < r2.centerx:
                normal = [-1, 0] # r1 is left of r2
            else:
                normal = [1, 0]
        else:
            # Push vertically
            overlap = inter.height
            if r1.centery < r2.centery:
                normal = [0, -1] # r1 is above r2
            else:
                normal = [0, 1]
                
        # Distribute correction
        # If one is static (no RB), move the other 100%
        # If both dynamic, move each 50%
        
        if rb1 and not rb2:
            self.apply_resolution(c1, normal, overlap) # Push c1 away (along normal)
        elif rb2 and not rb1:
            self.apply_resolution(c2, normal, -overlap) # Push c2 away (against normal)
        else:
            # Both dynamic
            self.apply_resolution(c1, normal, overlap * 0.5)
            self.apply_resolution(c2, normal, -overlap * 0.5)

    def apply_resolution(self, collider, normal, pixel_depth):
        obj = collider["obj"]
        rb = collider["rb"]
        
        # Move Object
        obj.position[0] += normal[0] * pixel_depth * 1.01 # 1% slop to prevent sinking
        obj.position[1] += normal[1] * pixel_depth * 1.01
        
        # Zero out velocity against the wall
        if rb:
            vel = rb.get("velocity", [0,0])
            
            # Simple bounce could be here, but for now just cancel (inelastic)
            # Zero out velocity against the wall
            if normal[0] != 0: 
                vel[0] = 0
            if normal[1] != 0:
                vel[1] = 0
                
            rb["velocity"] = vel
