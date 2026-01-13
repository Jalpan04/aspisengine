from runtime.api import Script
import random
import string

class TextThrasher(Script):
    def update(self, dt):
        # Generate random string
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        # Access TextRenderer component directly?
        # The engine's GameObject.components is a dict.
        # We need to modify the underlying data so the Render system picks it up.
        if "TextRenderer" in self.game_object.components:
            self.game_object.components["TextRenderer"]["text"] = f"Trash: {random_str}"
            
            # Randomize color to check texture cache invalidation
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            self.game_object.components["TextRenderer"]["color"] = [r, g, b]
