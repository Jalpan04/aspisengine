from shared.component_defs import COMPONENT_RIGIDBODY, COMPONENT_BOX_COLLIDER
import pygame

class PhysicsSystem:
    GRAVITY = 980.0  # Pixels per second squared

    def __init__(self):
        self.colliders = [] # List of (id, rect, is_trigger, game_object)

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
                
        # Distribute correction
        # Calculate combined restitution (average)
        restitution_1 = rb1.get("restitution", 0.5) if rb1 else 0.5
        restitution_2 = rb2.get("restitution", 0.5) if rb2 else 0.5
        e = (restitution_1 + restitution_2) / 2.0
        
        m1 = rb1.get("mass", 0.0) if rb1 else 0.0
        m2 = rb2.get("mass", 0.0) if rb2 else 0.0
        
        # Determine which object(s) are dynamic (movable)
        dynamic1 = rb1 is not None and m1 > 0
        dynamic2 = rb2 is not None and m2 > 0
        
        # Calculate inverse normal for c2
        neg_normal = [-normal[0], -normal[1]]

        if dynamic1 and not dynamic2:
            self.apply_resolution(c1, normal, overlap, e) # Push c1 away (along normal)
        elif dynamic2 and not dynamic1:
            self.apply_resolution(c2, neg_normal, overlap, e) # Push c2 away (along neg_normal)
        elif dynamic1 and dynamic2:
            # Mass-based resolution
            total_mass = m1 + m2
            if total_mass == 0:
                ratio1 = 0.5
                ratio2 = 0.5
            else:
                ratio1 = m2 / total_mass # If m1 is huge (heavy), ratio1 is small (moves less)
                ratio2 = m1 / total_mass
            
            self.apply_resolution(c1, normal, overlap * ratio1, e)
            self.apply_resolution(c2, neg_normal, overlap * ratio2, e)
        else:
            pass

    def apply_resolution(self, collider, normal, pixel_depth, restitution):
        obj = collider["obj"]
        rb = collider["rb"]
        
        # Move Object
        obj.position[0] += normal[0] * pixel_depth * 1.01
        obj.position[1] += normal[1] * pixel_depth * 1.01
        
        # Velocity Response
        if rb:
            vel = rb.get("velocity", [0.0, 0.0])
            
            # v_normal = vel . normal
            vn = vel[0] * normal[0] + vel[1] * normal[1]
            
            # Only bounce if moving towards the normal (collision)
            if vn < 0:
                # J = -(1 + e) * vn
                jn = -(1 + restitution) * vn
                
                # Apply impulse
                vel[0] += normal[0] * jn
                vel[1] += normal[1] * jn
                
            rb["velocity"] = vel
