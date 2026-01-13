from runtime.api import Script

class PoisonScript(Script):
    def start(self):
        print("PoisonScript: Injecting NaN coordinates...")
        # Inject NaN
        self.transform.position = [float('nan'), float('nan')]
