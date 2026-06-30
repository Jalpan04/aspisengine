from runtime.api import Script, Input
import pygame

class SideScrollPlayer(Script):
    def start(self):
        self.set_anim_parameter("speed", 0.0)
        self.jump_force = -420.0  # Upward velocity (Y-down, so negative is up)
        self.move_speed = 220.0
        
    def update(self, dt):
        rb = self.game_object.components.get("RigidBody")
        if not rb: return
        
        # Read current velocity (synced from physics engine)
        current_vel = rb.get("velocity", [0.0, 0.0])
        vx = current_vel[0]
        vy = current_vel[1]
        
        # Horizontal movement
        target_vx = 0.0
        moving = False
        if Input.get_key(pygame.K_a):
            target_vx = -self.move_speed
            moving = True
            # Flip sprite left
            if self.transform.scale[0] > 0:
                self.transform.scale[0] = -self.transform.scale[0]
        elif Input.get_key(pygame.K_d):
            target_vx = self.move_speed
            moving = True
            # Flip sprite right
            if self.transform.scale[0] < 0:
                self.transform.scale[0] = -self.transform.scale[0]
                
        # Smoothly apply horizontal velocity
        vx = target_vx
        
        # Jump check (Space or W key)
        # Ground check: check if vertical velocity is close to 0 to prevent infinite jumps
        if (Input.get_key(pygame.K_w) or Input.get_key(pygame.K_SPACE)) and abs(vy) < 8.0:
            vy = self.jump_force
            
        # Update component dictionary so physics engine picks it up
        rb["velocity"] = [vx, vy]
        
        # Update animator speed parameter
        self.set_anim_parameter("speed", 1.0 if moving else 0.0)
