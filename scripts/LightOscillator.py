from runtime.api import Script
import math

class LightOscillator(Script):
    def awake(self):
        self.time_elapsed = 0.0
        self.base_intensity = 0.6
        self.base_radius = 200.0
        
    def update(self, dt):
        self.time_elapsed += dt * 2.5
        
        light = self.game_object.components.get("LightSource")
        if light:
            # Oscillate intensity between 0.2 and 1.0
            light["intensity"] = self.base_intensity + math.sin(self.time_elapsed) * 0.4
            # Oscillate radius between 100.0 and 300.0
            light["radius"] = self.base_radius + math.cos(self.time_elapsed * 0.8) * 100.0
