
from runtime.api import Script, Time
import random
import math

class PongBall(Script):
    def start(self):
        self.speed = 400.0
        self.reset_ball()

    def reset_ball(self):
        self.transform.position = [0.0, 0.0]
        
        # Random start direction (left or right with some angle)
        angle = random.uniform(-45, 45)
        if random.random() < 0.5:
            angle += 180
            
        rad = math.radians(angle)
        vx = math.cos(rad) * self.speed
        vy = math.sin(rad) * self.speed
        
        # Set velocity on RigidBody (assuming component exists)
        if hasattr(self.transform, "components") and "RigidBody" in self.transform.components:
             self.transform.components["RigidBody"]["velocity"] = [vx, vy]

    def update(self, dt):
        # Maintain constant speed
        if hasattr(self.transform, "components") and "RigidBody" in self.transform.components:
            rb = self.transform.components["RigidBody"]
            vel = rb.get("velocity", [0.0, 0.0])
            
            # Check magnitude
            mag_sq = vel[0]**2 + vel[1]**2
            if mag_sq > 0.001:
                mag = math.sqrt(mag_sq)
                if abs(mag - self.speed) > 1.0:
                    # Normalize and rescale
                    scale = self.speed / mag
                    vel[0] *= scale
                    vel[1] *= scale
                    rb["velocity"] = vel
        
        # Check scoring (out of bounds)
        x = self.transform.position[0]
        if x < -450 or x > 450: # Screen width 800 ( +/- 400). margin 50.
            print("Score! Resetting...")
            self.reset_ball()

    def on_collision_enter(self, other):
        # Simple feedback
        # print("Bounced!")
        pass
