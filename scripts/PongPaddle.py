
from runtime.api import Script, Input, KeyCode, Time

class PongPaddle(Script):
    def start(self):
        self.speed = 400.0
        self.y_limit = 220.0  # Safe limit to avoid touching walls (290 - 20 (wall) - 50 (paddle) = 220) 
        self.initial_x = self.transform.position[0]

    def update(self, dt):
        velocity = [0.0, 0.0]

        # Use Input.get_key()
        up_key = KeyCode.W
        down_key = KeyCode.S
        
        if self.game_object.name == "PaddleRight":
            up_key = KeyCode.UP
            down_key = KeyCode.DOWN

        if Input.get_key(up_key):
            velocity[1] = -1.0
        elif Input.get_key(down_key):
            velocity[1] = 1.0

        # Apply movement via Physics
        if hasattr(self.transform, "components") and "RigidBody" in self.transform.components:
            rb = self.transform.components["RigidBody"]
             
            # Reset X to lock it (handling drift from collisions)
            current_x = self.transform.position[0]
            if abs(current_x - self.initial_x) > 0.1:
                self.transform.position[0] = self.initial_x
                
            # Set Velocity
            current_vel = rb.get("velocity", [0.0, 0.0])
            target_vy = velocity[1] * self.speed
            
            # Direct velocity control for responsiveness, but respect collisions?
            # If we just set it, we override collision stops.
            # But the 'stop' happened last frame. 
            # We want to move UNLESS blocked.
            
            rb["velocity"] = [0.0, target_vy] # Force X velocity 0
            
            # Note: Removing manual clamp. Physics walls will stop us.
