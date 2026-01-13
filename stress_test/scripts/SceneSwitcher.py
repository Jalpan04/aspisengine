from runtime.api import Script

class SceneSwitcher(Script):
    timer = 0.0
    next_scene = ""
    
    def update(self, dt):
        self.timer += dt
        if self.timer > 1.0: # Switch every 1 second
            self.timer = -999 # Prevent multiple calls
            print(f"Switching to {self.next_scene}...")
            self.load_scene(self.next_scene)
