from runtime.api import Script
import math

class VerticalHover(Script):
    def awake(self):
        self.time_elapsed = 0.0
        self.start_x = 200.0
        self.start_y = 300.0
        self.range_y = 150.0
        self.speed = 1.5
        
    def update(self, dt):
        self.time_elapsed += dt * self.speed
        if self.transform:
            y = self.start_y + math.sin(self.time_elapsed) * self.range_y
            self.transform.position = [self.start_x, y]
