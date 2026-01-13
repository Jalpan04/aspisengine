from runtime.api import Script

class FaultyScript(Script):
    timer = 0.0

    def start(self):
        print("FaultyScript attached. Will crash in 2 seconds.")

    def update(self, dt):
        self.timer += dt
        if self.timer > 2.0:
            print("FaultyScript: Attempting divide by zero...")
            x = 1 / 0
