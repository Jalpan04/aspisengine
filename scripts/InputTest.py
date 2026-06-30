from runtime.api import Script, Input
import pygame

class InputTest(Script):
    def start(self):
        print("InputTest Script Started!")
        # Test finding obstacles by tag on start
        obstacles = self.find_objects_with_tag("Obstacle")
        print(f"InputTest: Found {len(obstacles)} objects with tag 'Obstacle'")
        for o in obstacles:
            print(f"  - {o.name} (ID: {o.id})")

    def update(self, dt):
        # 1. Edge-triggered key press (Space)
        if Input.get_key_down(pygame.K_SPACE):
            print("InputTest: [SPACE] Pressed Down!")
        if Input.get_key_up(pygame.K_SPACE):
            print("InputTest: [SPACE] Released!")

        # 2. Mouse click edge detection
        if Input.get_mouse_button_down(0):  # Left click
            m_pos = Input.get_mouse_position()
            print(f"InputTest: [Mouse Left Button] Clicked down at screen position: {m_pos}")
        if Input.get_mouse_button_up(0):
            print("InputTest: [Mouse Left Button] Released!")
