from runtime.api import Script, Input
import pygame

class AnimatedPlayer(Script):
    def start(self):
        self.set_anim_parameter("speed", 0.0)

    def update(self, dt):
        move_speed = 300 * dt
        move_x = 0
        move_y = 0
        
        if Input.get_key(pygame.K_w):
            move_y -= move_speed
        if Input.get_key(pygame.K_s):
            move_y += move_speed
        if Input.get_key(pygame.K_a):
            move_x -= move_speed
            # Flip sprite left
            if self.transform.scale[0] > 0:
                self.transform.scale[0] = -self.transform.scale[0]
        if Input.get_key(pygame.K_d):
            move_x += move_speed
            # Flip sprite right
            if self.transform.scale[0] < 0:
                self.transform.scale[0] = -self.transform.scale[0]
                
        self.transform.position[0] += move_x
        self.transform.position[1] += move_y
        
        # Calculate moving speed for animator transition
        moving = (move_x != 0 or move_y != 0)
        self.set_anim_parameter("speed", 1.0 if moving else 0.0)
