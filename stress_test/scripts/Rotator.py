from runtime.api import Script

class Rotator(Script):
    speed = 90.0 # Degrees per second

    def update(self, dt):
        # Debug who is rotating
        # print(f"Rotating: {self.game_object.name}")
        current_rot = self.transform.rotation
        self.transform.rotation = current_rot + self.speed * dt
