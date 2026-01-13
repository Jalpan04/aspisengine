from runtime.api import Script

class LifecycleLogger(Script):
    timer = 0.0

    def awake(self):
        print(f"LifecycleTest: Awake called on {self.game_object.name}")

    def start(self):
        print(f"LifecycleTest: Start called on {self.game_object.name}")

    def update(self, dt):
        self.timer += dt
        if self.timer > 1.0:
            self.timer = 0
            print(f"LifecycleTest: Update called on {self.game_object.name} (1s interval)")

    def on_destroy(self):
        print(f"LifecycleTest: Destroy called on {self.game_object.name}")
