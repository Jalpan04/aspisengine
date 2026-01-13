from runtime.api import Script, Input, KeyCode

class PlayerController(Script):
    speed = 200.0

    def start(self):
        print("PlayerController Started")

    def update(self, dt):
        move_x = 0
        move_y = 0

        if Input.get_key(KeyCode.W) or Input.get_key(KeyCode.UP):
            move_y = -1
        if Input.get_key(KeyCode.S) or Input.get_key(KeyCode.DOWN):
            move_y = 1
        if Input.get_key(KeyCode.A) or Input.get_key(KeyCode.LEFT):
            move_x = -1
        if Input.get_key(KeyCode.D) or Input.get_key(KeyCode.RIGHT):
            move_x = 1

        # We modify the Transform position directly
        # If we had a rigidbody, we should ideally use physics forces, but this tests Transform updates + Physics sync
        
        current_pos = self.transform.position
        new_x = current_pos[0] + move_x * self.speed * dt
        new_y = current_pos[1] + move_y * self.speed * dt
        
        self.transform.position = [new_x, new_y]
