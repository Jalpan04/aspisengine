from runtime.api import Script
import random

class ObjectCycler(Script):
    timer = 0.0
    spawn_interval = 0.1
    max_objects = 10

    def start(self):
        self.objects = []
        print("ObjectCycler Started. Spawning FallingBoxes...")

    def update(self, dt):
        self.timer += dt
        if self.timer > self.spawn_interval:
            self.timer = 0
            
            # Spawn
            pos = [random.randint(100, 700), 0]
            try:
                # Instantiate returns the ID or the object? Need to check api implementation details.
                # Standard Engine API usually returns the GameObject instance.
                # Assuming our engine supports instantiate via Script base class or we need to pass reference.
                # Wait, runtime/api.py shows instantiate is a method.
                # In game_loop it was monkey-patched.
                
                obj = self.instantiate("stress_test/prefabs/FallingBox.json", pos)
                if obj:
                    self.objects.append(obj)
            except Exception as e:
                print(f"Spawn Error: {e}")

            # Cleanup
            if len(self.objects) > self.max_objects:
                oldest = self.objects.pop(0)
                try:
                    print(f"Destroying {oldest.name}...")
                    self.destroy(oldest)
                except Exception as e:
                    print(f"Destroy Error: {e}")
