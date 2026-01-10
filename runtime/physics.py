
import pymunk
from shared.component_defs import COMPONENT_RIGIDBODY, COMPONENT_BOX_COLLIDER
import math

class PhysicsSystem:
    # Pygame uses Y-down, Pymunk usually Y-up, but we can just use gravity=(0, 980)
    GRAVITY = (0.0, 980.0) 

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = self.GRAVITY
        self.bodies = {} # object.id -> pymunk.Body
        
        # Collision Handler
        # Use add_collision_handler(0, 0) for default types (we set everything to type 0)
        self.space.iterations = 60 # High stability for stacking
        try:
            # Try newer API first
            if hasattr(self.space, 'add_default_collision_handler'):
                h = self.space.add_default_collision_handler()
            else:
                h = self.space.add_collision_handler(0, 0)
            h.begin = self._handle_collision
        except Exception as e:
            print(f"Warning: Could not set up collision handler: {e}")
        
        self.current_collisions = [] # Stores (obj_a, obj_b) for current step

    def _handle_collision(self, arbiter, space, data):
        # Determine objects involved
        shape_a, shape_b = arbiter.shapes
        body_a, body_b = shape_a.body, shape_b.body
        
        obj_a = getattr(body_a, 'data', None)
        obj_b = getattr(body_b, 'data', None)
        
        if obj_a and obj_b:
            self.current_collisions.append((obj_a, obj_b))
            self.current_collisions.append((obj_b, obj_a))
            
        return True # Process collision normally

    def update(self, dt, objects):
        # 0. Clear previous collisions
        self.current_collisions.clear()

        # 1. Sync GameObjects -> Pymunk
        self._sync_to_physics(objects)
        
        # 2. Step Simulation
        self.space.step(dt)
        
        # 3. Sync Pymunk -> GameObjects
        self._sync_from_physics(objects)
        
        # 4. Return collected collisions
        return list(self.current_collisions) 

    def _sync_to_physics(self, objects):
        """
        Creates/Updates Pymunk bodies based on GameObject components.
        If an object moves strictly via physics, we don't force position here 
        unless it's 'Kinematic' or we detect a teleport.
        For now, we Initialize only.
        """
        current_ids = set()
        
        for obj in objects:
            current_ids.add(obj.id)
            
            # Check components
            rb_data = obj.components.get(COMPONENT_RIGIDBODY)
            box_data = obj.components.get("BoxCollider")
            circ_data = obj.components.get("CircleCollider")
            
            if not rb_data and not box_data and not circ_data:
                continue

            # Create Body if missing
            if obj.id not in self.bodies:
                # We pass None for col_data to signal _create_body to look up components itself
                self._create_body(obj, rb_data, None)
            
            # If it's a STATIC body (no RigidBody), we might need to update pos if User moved it via script (teleport)
            # If it's DYNAMIC (RigidBody exists), Pymunk controls it, but if the USER moved the Transform directly (Script),
            # we should treat it as a TELEPORT.
            
            if obj.id in self.bodies:
                body = self.bodies[obj.id]
                dx = body.position.x - obj.position[0]
                dy = body.position.y - obj.position[1]
                
                # If mismatch is significant (e.g. > 0.1 pixels), assume teleport
                if abs(dx) > 0.1 or abs(dy) > 0.1:
                    body.position = (obj.position[0], obj.position[1])
                    body.angle = math.radians(obj.rotation)
                
                # 2. Velocity Override Detection (Script -> Physics)
                if rb_data and body.body_type == pymunk.Body.DYNAMIC:
                    script_vel = rb_data.get("velocity", [0.0, 0.0])
                    # Compare rigid body (script) velocity vs physics engine velocity
                    # We check for difference. Tolerance 0.1
                    if abs(script_vel[0] - body.velocity.x) > 0.1 or abs(script_vel[1] - body.velocity.y) > 0.1:
                        # Script changed it! Apply to physics.
                        body.velocity = (script_vel[0], script_vel[1])
            

    def custom_velocity_func(self, body, gravity, damping, dt):
        """
        Custom velocity callback to handle:
        1. Gravity Toggle (per body)
        2. Linear Drag (per body)
        """
        use_gravity = getattr(body, 'custom_use_gravity', True)
        drag = getattr(body, 'custom_drag', 0.0)
        
        # 1. Apply Gravity (or not)
        g = gravity if use_gravity else (0, 0)
        pymunk.Body.update_velocity(body, g, damping, dt)
        
        # 2. Apply Linear Drag (Air Resistance)
        if drag > 0:
            d = 1.0 - (drag * dt)
            if d < 0: d = 0
            body.velocity = body.velocity * d

    def _create_body(self, obj, rb_data, col_data):
        pos = obj.position
        rot = obj.rotation
        
        # Safety Check: NaN Poisoning
        if math.isnan(pos[0]) or math.isnan(pos[1]) or math.isnan(rot):
            raise ValueError(f"Physics Error: Object '{obj.name}' has NaN position/rotation. Aborting body creation.") # Prevent crash later
        
        # Determine Body Type
        mass = 1.0
        use_gravity = True
        drag = 0.0
        
        initial_velocity = [0.0, 0.0]
        
        if rb_data:
            mass = rb_data.get("mass", 1.0)
            use_gravity = rb_data.get("use_gravity", True)
            drag = rb_data.get("drag", 0.0)
            restitution = rb_data.get("restitution", 0.0) # Read restitution
            friction = rb_data.get("friction", 0.5)
            initial_velocity = rb_data.get("velocity", [0.0, 0.0])
            fixed_rotation = rb_data.get("fixed_rotation", False)
            body_type = pymunk.Body.DYNAMIC
        else:
            mass = 0
            use_gravity = False
            restitution = 0.0 # Default for simple static?
            friction = 0.5 # Default friction for static
            fixed_rotation = False
            body_type = pymunk.Body.STATIC
            
        # Create Body
        if body_type == pymunk.Body.DYNAMIC:
            # If fixed rotation, moment is infinite
            moment = float("inf") if fixed_rotation else 1.0 # Default fallback
            body = pymunk.Body(mass, moment, body_type=body_type)
        else:
            body = pymunk.Body(body_type=body_type)
        
        # Custom Props
        body.custom_use_gravity = use_gravity
        body.custom_drag = drag
        body.data = obj 
        
        # Velocity Func
        if body_type == pymunk.Body.DYNAMIC:
            if not use_gravity or drag > 0:
                body.velocity_func = self.custom_velocity_func
            
        body.position = (pos[0], pos[1])
        body.angle = math.radians(rot)
        
        if body_type == pymunk.Body.DYNAMIC:
             body.velocity = (initial_velocity[0], initial_velocity[1])
        
        # Shapes
        shapes = []
        is_trigger_any = False

            # 1. Box Collider
        if "BoxCollider" in obj.components:
            box_data = obj.components["BoxCollider"]
            size = box_data.get("size", [50, 50])
            offset = box_data.get("offset", [0, 0])
            is_trigger = box_data.get("is_trigger", False)
            if is_trigger: is_trigger_any = True
            
            # Filtering
            cat = box_data.get("category_bitmask", 1)
            mask = box_data.get("collision_mask", 0xFFFFFFFF)
            
            width, height = size
            ox, oy = offset
            l, r = ox - width/2, ox + width/2
            t, b = oy - height/2, oy + height/2
            verts = [(l, t), (r, t), (r, b), (l, b)]
            
            shape = pymunk.Poly(body, verts)
            shape.sensor = is_trigger
            shape.elasticity = restitution
            shape.friction = friction
            shape.filter = pymunk.ShapeFilter(categories=cat, mask=mask)
            shapes.append(shape)

        # 2. Circle Collider
        if "CircleCollider" in obj.components:
            circ_data = obj.components["CircleCollider"]
            radius = circ_data.get("radius", 25.0)
            c_offset = circ_data.get("offset", [0, 0])
            is_trigger = circ_data.get("is_trigger", False)
            if is_trigger: is_trigger_any = True
            
            # Filtering
            cat = circ_data.get("category_bitmask", 1)
            mask = circ_data.get("collision_mask", 0xFFFFFFFF)
            
            shape = pymunk.Circle(body, radius, offset=(c_offset[0], c_offset[1]))
            shape.sensor = is_trigger
            shape.elasticity = restitution
            shape.friction = friction
            shape.filter = pymunk.ShapeFilter(categories=cat, mask=mask)
            shapes.append(shape)
            
        # Add to Space
        if shapes:
            self.space.add(body, *shapes)
        else:
            self.space.add(body)
            
        # Moment Calculation
        if body_type == pymunk.Body.DYNAMIC and shapes and not fixed_rotation:
            if "CircleCollider" in obj.components:
                 radius = obj.components["CircleCollider"].get("radius", 25.0)
                 # Cylinder/Circle Moment: (1/2) * m * r^2
                 body.moment = 0.5 * mass * (radius**2)
            elif "BoxCollider" in obj.components:
                 # Poly Moment
                 for s in shapes:
                     if isinstance(s, pymunk.Poly):
                        try:
                            body.moment = pymunk.moment_for_poly(mass, s.get_vertices())
                            break
                        except: pass
                 
        self.bodies[obj.id] = body 

    def _sync_from_physics(self, objects):
        """
        Updates GameObject position/rotation from Pymunk simulation.
        """
        for obj in objects:
            if obj.id in self.bodies:
                body = self.bodies[obj.id]
                
                # Only sync back for Dynamic bodies 
                # (Static bodies don't move by physics)
                if body.body_type == pymunk.Body.DYNAMIC:
                    obj.position[0] = body.position.x
                    obj.position[1] = body.position.y
                    obj.rotation = math.degrees(body.angle) # Radians -> Degrees
                    
                    # Update Component Velocity (Physics -> Script)
                    if COMPONENT_RIGIDBODY in obj.components:
                        obj.components[COMPONENT_RIGIDBODY]["velocity"] = [body.velocity.x, body.velocity.y]
