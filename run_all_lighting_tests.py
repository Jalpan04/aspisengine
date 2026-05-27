import sys
import subprocess
import os

def print_menu():
    print("=" * 60)
    print("           ASPIS ENGINE - DYNAMIC LIGHTING TEST HUB")
    print("=" * 60)
    print("Select a lighting test to launch:")
    print("1) Test 1: Multi-Color Overlapping Light Blending (RGB)")
    print("2) Test 2: Shadow Toggle / Penetration Contrast Demo")
    print("3) Test 3: Octagonal Circle vs Sharp Box Shadows Comparison")
    print("4) Test 4: Variable Light Intensity & Radius Pulse Oscillation")
    print("5) Test 5: Complex Corridor Maze Occlusion Stress Test")
    print("q) Quit Test Hub")
    print("=" * 60)

def main():
    while True:
        print_menu()
        choice = input("Enter choice (1-5, or q): ").strip().lower()
        if choice == 'q':
            print("Exiting Test Hub.")
            break
        elif choice == '1':
            subprocess.run([sys.executable, "run_multi_light_demo.py"])
        elif choice == '2':
            subprocess.run([sys.executable, "run_shadow_toggle_demo.py"])
        elif choice == '3':
            subprocess.run([sys.executable, "run_collider_shadows_demo.py"])
        elif choice == '4':
            subprocess.run([sys.executable, "run_intensity_demo.py"])
        elif choice == '5':
            subprocess.run([sys.executable, "run_maze_stress_test.py"])
        else:
            print("Invalid selection. Please choose 1-5 or q.")
            
if __name__ == "__main__":
    main()
