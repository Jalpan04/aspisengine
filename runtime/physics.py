from shared.component_defs import COMPONENT_RIGIDBODY, COMPONENT_BOX_COLLIDER
import pygame

class PhysicsSystem:
    GRAVITY = 980.0  # Pixels per second squared

    def __init__(self):
        self.colliders = [] # List of (id, rect, is_trigger, game_object)
        self.debug_contacts = [] # List of (center_point, normal_vector)

    def update(self, dt, objects):
        # 1. Integration Step (Apply Gravity & Velocity)
        # ... logic ...
        
        # 2. Collision Detection
        self.colliders.clear()
        self.debug_contacts.clear()
        events = [] # List of (obj_a, obj_b)
        
        # Collect all colliders
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
        events = [] # List of (obj_a, obj_b)
        
        # Collect all colliders
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
            
            self.colliders.append({
                "obj": obj,
                "rect": rect,
                "is_trigger": col_data.get("is_trigger", False),
                "rb": obj.components.get(COMPONENT_RIGIDBODY)
            })

        # Check pairs
        for i in range(len(self.colliders)):
            c1 = self.colliders[i]
            for j in range(i + 1, len(self.colliders)):
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
        
        # Determine center point of impact (approximate)
        contact_x = inter.centerx
        contact_y = inter.centery
        self.debug_contacts.append(((contact_x, contact_y), normal))
                
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
            # Bounce
            restitution = rb.get("restitution", 0.5)

            if normal[0] != 0: 
                # Reflect X
                if (normal[0] > 0 and vel[0] < 0) or (normal[0] < 0 and vel[0] > 0):
                    # Moving towards wall, so reflect
                    vel[0] = -vel[0] * restitution
            
            if normal[1] != 0:
                # Reflect Y
                if (normal[1] > 0 and vel[1] < 0) or (normal[1] < 0 and vel[1] > 0):
                    vel[1] = -vel[1] * restitution
                
            rb["velocity"] = vel
