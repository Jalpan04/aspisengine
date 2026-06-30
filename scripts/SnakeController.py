from runtime.api import Script, Input
import pygame
import random

class SnakeController(Script):
    def start(self):
        print("Snake Game Controller Initialized!")
        self.grid_size = 40.0
        self.direction = [1, 0] # Start moving right
        self.next_direction = [1, 0]
        
        self.move_delay = 0.16 # Snake moves 6 times per second
        self.timer = 0.0
        
        self.body_segments = []
        self.pending_grow = False
        
        self.apple = self.find_object("Apple")
        self.score_text = self.find_object("ScoreText")
        self.score = 0
        
        # Grid boundaries (viewport is 1280x720)
        self.min_x, self.max_x = -600.0, 600.0
        self.min_y, self.max_y = -320.0, 320.0
        
        self.reset_game()

    def reset_game(self):
        print("Resetting Snake Game...")
        # Clean up existing body segments
        for seg in self.body_segments:
            self.destroy(seg)
        self.body_segments.clear()
        
        self.direction = [1, 0]
        self.next_direction = [1, 0]
        self.score = 0
        self.pending_grow = False
        
        # Position head in center
        self.transform.position = [0.0, 0.0]
        self.transform.rotation = 0.0
        
        # Reposition apple
        self.respawn_apple()
        
        # Reset score text
        if self.score_text and "TextRenderer" in self.score_text.components:
            self.score_text.components["TextRenderer"]["text"] = "Score: 0"

    def respawn_apple(self):
        if not self.apple:
            return
            
        # Spawn apple at a random grid coordinate that does not overlap with the snake
        while True:
            # Grid ranges: X from -14 to 14, Y from -7 to 7
            gx = random.randint(-14, 14) * int(self.grid_size)
            gy = random.randint(-7, 7) * int(self.grid_size)
            
            # Check overlap with head
            if abs(self.transform.position[0] - gx) < 5 and abs(self.transform.position[1] - gy) < 5:
                continue
                
            # Check overlap with body segments
            overlap = False
            for seg in self.body_segments:
                if abs(seg.position[0] - gx) < 5 and abs(seg.position[1] - gy) < 5:
                    overlap = True
                    break
            if overlap:
                continue
                
            self.apple.position = [float(gx), float(gy)]
            break

    def update(self, dt):
        # 1. Capture direction updates (prevent 180-degree self-reversals)
        if (Input.get_key(pygame.K_w) or Input.get_key(pygame.K_UP)) and self.direction[1] != 1:
            self.next_direction = [0, -1]
        elif (Input.get_key(pygame.K_s) or Input.get_key(pygame.K_DOWN)) and self.direction[1] != -1:
            self.next_direction = [0, 1]
        elif (Input.get_key(pygame.K_a) or Input.get_key(pygame.K_LEFT)) and self.direction[0] != 1:
            self.next_direction = [-1, 0]
        elif (Input.get_key(pygame.K_d) or Input.get_key(pygame.K_RIGHT)) and self.direction[0] != -1:
            self.next_direction = [1, 0]

        # 2. Timing logic for discrete snake movement steps
        self.timer += dt
        if self.timer >= self.move_delay:
            self.timer -= self.move_delay
            self.move_step()

    def move_step(self):
        self.direction = self.next_direction
        
        # Map direction to rotation (heading in degrees for conical spotlight)
        # Right: 0, Down: 90, Left: 180, Up: 270
        rot = 0.0
        if self.direction == [0, -1]:
            rot = 270.0
        elif self.direction == [0, 1]:
            rot = 90.0
        elif self.direction == [-1, 0]:
            rot = 180.0
        elif self.direction == [1, 0]:
            rot = 0.0

        old_pos = list(self.transform.position)
        
        # Calculate new head position
        new_x = self.transform.position[0] + self.direction[0] * self.grid_size
        new_y = self.transform.position[1] + self.direction[1] * self.grid_size
        
        # A. Boundary Collision check
        if new_x < self.min_x or new_x > self.max_x or new_y < self.min_y or new_y > self.max_y:
            print("Snake hit the wall!")
            self.reset_game()
            return

        # B. Self-collision check
        for seg in self.body_segments:
            if abs(seg.position[0] - new_x) < 5 and abs(seg.position[1] - new_y) < 5:
                print("Snake bit itself!")
                self.reset_game()
                return

        # C. Apple Collision check
        if self.apple:
            ap = self.apple.position
            if abs(new_x - ap[0]) < 5 and abs(new_y - ap[1]) < 5:
                self.score += 1
                if self.score_text and "TextRenderer" in self.score_text.components:
                    self.score_text.components["TextRenderer"]["text"] = f"Score: {self.score}"
                
                self.pending_grow = True
                self.respawn_apple()

        # D. Move body segments
        if self.pending_grow:
            # Grow by spawning a new body segment at the head's previous spot
            new_seg = self.instantiate("prefabs/body_segment.json", old_pos, 0.0)
            if new_seg:
                self.body_segments.insert(0, new_seg)
            self.pending_grow = False
        else:
            # Shift body segments forward by moving the tail segment to the head's old spot
            if len(self.body_segments) > 0:
                last_seg = self.body_segments.pop()
                last_seg.position = old_pos
                self.body_segments.insert(0, last_seg)

        # E. Apply final position and rotation to the head
        self.transform.position = [new_x, new_y]
        self.transform.rotation = rot
