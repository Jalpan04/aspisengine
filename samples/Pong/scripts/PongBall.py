
from runtime.api import Script, Time
import random
import math

class PongBall(Script):
    def start(self):
        self.speed = 400.0
        self.score_left = 0
        self.score_right = 0
        
        # Cache Text Objects
        self.txt_left_obj = self.find_object("ScoreTextLeft")
        self.txt_right_obj = self.find_object("ScoreTextRight")
        
        if not self.txt_left_obj or not self.txt_right_obj:
            print("Warning: Score Texts not found!")
            
        self.reset_ball()

    def reset_ball(self):
        self.transform.position = [0.0, 0.0]
        
        # Random start direction (left or right with some angle)
        angle = random.uniform(-45, 45)
        if random.random() < 0.5:
            angle += 180
            
        rad = math.radians(angle)
        vx = math.cos(rad) * self.speed
        vy = math.sin(rad) * self.speed
        
        # Set velocity on RigidBody (assuming component exists)
        if hasattr(self.transform, "components") and "RigidBody" in self.transform.components:
             self.transform.components["RigidBody"]["velocity"] = [vx, vy]

    def update(self, dt):
        # Maintain constant speed
        if hasattr(self.transform, "components") and "RigidBody" in self.transform.components:
            rb = self.transform.components["RigidBody"]
            vel = rb.get("velocity", [0.0, 0.0])
            
            # Check magnitude
            mag_sq = vel[0]**2 + vel[1]**2
            if mag_sq > 0.001:
                mag = math.sqrt(mag_sq)
                if abs(mag - self.speed) > 1.0:
                    # Normalize and rescale
                    scale = self.speed / mag
                    vel[0] *= scale
                    vel[1] *= scale
                    rb["velocity"] = vel
        
        # Check scoring (out of bounds)
        x = self.transform.position[0]
        if x < -450: # Left Limit -> Right Scores
            self.score_right += 1
            self.play_sound("hit.wav") # Sound feedback
            self.update_ui()
            self.reset_ball()
        elif x > 450: # Right Limit -> Left Scores
            self.score_left += 1
            self.play_sound("hit.wav")
            self.update_ui()
            self.reset_ball()
            
    def update_ui(self):
        if self.txt_left_obj and "TextRenderer" in self.txt_left_obj.components:
            self.txt_left_obj.components["TextRenderer"]["text"] = str(self.score_left)
            
        if self.txt_right_obj and "TextRenderer" in self.txt_right_obj.components:
            self.txt_right_obj.components["TextRenderer"]["text"] = str(self.score_right)

    def on_collision_enter(self, other):
        # Simple feedback
        # print("Bounced!")
        # Play bounce sound
        self.play_sound("hit.wav")
        
        # Increase speed slightly on paddle hit?
        if "Paddle" in other.name:
            self.speed += 10.0
            
        # Wall Scoring
        if other.name == "WallLeft":
            self.score_right += 1
            self.update_ui()
            self.reset_ball()
        elif other.name == "WallRight":
            self.score_left += 1
            self.update_ui()
            self.reset_ball()
