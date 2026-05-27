from runtime.api import Script
import math

class MultiLightOrbit(Script):
    def awake(self):
        self.time_elapsed = 0.0
        self.center_x = 400.0
        self.center_y = 300.0
        self.orbit_radius = 160.0
        self.speed = 1.2
        self.angle_offset = 0.0
        
    def update(self, dt):
        self.time_elapsed += dt * self.speed
        if self.transform:
            angle = self.time_elapsed + self.angle_offset
            x = self.center_x + math.cos(angle) * self.orbit_radius
            y = self.center_y + math.sin(angle) * self.orbit_radius
            self.transform.position = [x, y]
