from runtime.api import Script
import math

class LightOrbit(Script):
    def awake(self):
        self.time_elapsed = 0.0
        self.center_x = 400.0
        self.center_y = 300.0
        self.orbit_radius = 180.0
        self.speed = 1.5 # Radians per second
        
    def update(self, dt):
        self.time_elapsed += dt * self.speed
        if self.transform:
            x = self.center_x + math.cos(self.time_elapsed) * self.orbit_radius
            y = self.center_y + math.sin(self.time_elapsed) * self.orbit_radius
            self.transform.position = [x, y]
