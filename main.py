"""
Main entry point for the Disneyland Adventure game.
"""
import os
import sys

# Add the modules directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))

from modules.game_manager import GameManager

def main():
    game = GameManager()
    game.initialize_game()
    game.run()

if __name__ == "__main__":
    main()
