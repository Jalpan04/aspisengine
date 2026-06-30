from runtime.api import Script

class GoalTrigger(Script):
    def start(self):
        self.won = False
        
    def on_collision_enter(self, other):
        # Detect if the dynamic ball collides with this trigger zone
        if other.name == "Light Ball" and not self.won:
            self.won = True
            print("VICTORY: The ball reached the goal hole!")
            
            # 1. Update Instructions Text message and color
            instructions = self.find_object("Instructions")
            if instructions and "TextRenderer" in instructions.components:
                instructions.components["TextRenderer"]["text"] = "VICTORY! The ball fell into the goal!"
                instructions.components["TextRenderer"]["color"] = [100, 255, 100, 255] # Green
                
            # 2. Change the Goal Light color to bright Green to signify success
            if "LightSource" in self.game_object.components:
                self.game_object.components["LightSource"]["color"] = [100, 255, 100, 255]
                self.game_object.components["LightSource"]["intensity"] = 2.0
                self.game_object.components["LightSource"]["radius"] = 350.0
