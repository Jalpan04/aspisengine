from runtime.api import Script

class AutoRestart(Script):
    """
    Monitors a target object (default: Knight Player).
    If they fall below a Y threshold, waits a short delay then reloads the scene.
    Attach to any always-active game object (e.g. Main Camera or a dedicated Manager).

    Properties:
    - target_name:     Name of the object to monitor.
    - scene_path:      Relative path to scene to reload (e.g. scenes/showcase_demo.scene.json)
    - fall_threshold:  World Y position below which restart is triggered.
    - restart_delay:   Seconds to wait before restarting.
    """
    target_name = "Knight Player"
    scene_path = "scenes/showcase_demo.scene.json"
    fall_threshold = 700.0
    restart_delay = 1.5

    def start(self):
        self._timer = 0.0
        self._restarting = False
        self._target = None

    def update(self, dt):
        if not self._target:
            self._target = self.find_object(self.target_name)
            if not self._target:
                return

        py = self._target.world_position[1]

        if not self._restarting and py > self.fall_threshold:
            self._restarting = True
            self._timer = 0.0
            print(f"[AutoRestart] {self.target_name} fell! Restarting in {self.restart_delay}s...")

        if self._restarting:
            self._timer += dt
            if self._timer >= self.restart_delay:
                print("[AutoRestart] Reloading scene...")
                self.load_scene(self.scene_path)
