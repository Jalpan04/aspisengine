from runtime.api import Script
import random

class Spawner(Script):
    spawn_timer = 0.0
    spawn_rate = 0.1 # Spawn every 0.1s
    count = 0
    max_count = 200

    def update(self, dt):
        if self.count >= self.max_count: return

        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_timer = 0
            self.spawn_object()

    def spawn_object(self):
        self.count += 1
        x = random.uniform(50, 750)
        y = -50 # Start above screen
        
        # We need a prefab file to instantiate
        # For this test, we assume 'assets/FallingBox.json' exists or similar
        # Since we don't have prefabs easily setup in this limited environment, 
        # we will rely on duplicated logic or just print for now? 
        # Wait, the runtime API has 'instantiate' but it needs a prefab path.
        
        # We will create a prefab file first in the execution.
        if hasattr(self, "instantiate"):
            self.instantiate("stress_test/prefabs/FallingBox.json", [x, y], 0)
