"""
Game Manager module for the Disneyland Adventure game.
Handles game state, setup, and command processing.
"""
import random
import sys

from .player import Player
from .area import Area, AreaManager
from .item import Item, ItemManager
from .npc import NPC, NPCManager
from .coordinates import Coordinates

class OutputMonitor:
    """Monitors stdout to see if any actual text is written."""
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.texts_buffer = []

    def write(self, text):
        stripped_text = text.strip()
        if stripped_text:
            self.texts_buffer.append(stripped_text)
        return self.original_stdout.write(text)

    def flush(self):
        return self.original_stdout.flush()

    def get_buffered_texts_and_reset(self):
        texts = list(self.texts_buffer)
        self.texts_buffer.clear()
        return texts

class GameManager:
    """Manages the overall game state and systems."""
    def __init__(self):
        self.player = Player(name="Guest", start_money=50)
        self.area_manager = AreaManager()
        self.item_manager = ItemManager()
        self.npc_manager = NPCManager()
        self.running = True
        self.game_turn = 0
        self._AMBIENT_NO_EVENT_MESSAGES = [
            "The magical air of Disneyland hums around you.",
            "You hear the distant laughter of children.",
            "A gentle breeze rustles the leaves on a nearby tree.",
            "Time passes peacefully.",
        ]

    def initialize_game(self):
        print("Warming up the magic of Disneyland...")

        # Create Item Prototypes
        mickey_ears = Item(name="Mickey Ears", description="Classic Mickey Mouse ears.", value=15)
        self.item_manager.add_prototype(mickey_ears)
        churro = Item(name="Churro", description="A delicious cinnamon sugar treat.", value=5)
        self.item_manager.add_prototype(churro)
        lost_map = Item(name="Lost Map", description="A slightly crumpled park map.", value=1, pickupable=True) # Low value, just for example
        self.item_manager.add_prototype(lost_map)

        # Create Areas
        main_street = Area(name="Main Street U.S.A.", description="A charming turn-of-the-century American town square.", grid_width=10, grid_length=5)
        self.area_manager.add_area(main_street)

        # Add a shop to Main Street
        main_street.is_shop = True
        main_street.add_item_to_sell_stock(self.item_manager.item_prototypes["mickey ears"], price=15, quantity=20)
        main_street.add_item_to_sell_stock(self.item_manager.item_prototypes["churro"], price=5, quantity=50)
        main_street.add_item_to_buy_stock("Lost Map", buy_price=1, desired_stock=5) # Shop buys lost maps

        fantasyland = Area(name="Fantasyland", description="A whimsical land of fairy tales and dreams.", grid_width=8, grid_length=8)
        self.area_manager.add_area(fantasyland)

        adventureland = Area(name="Adventureland", description="An exotic land of jungles and mystery.", grid_width=12, grid_length=7)
        self.area_manager.add_area(adventureland)

        # Connect Areas
        self.area_manager.connect_areas(main_street.id, "north", fantasyland.id)
        self.area_manager.connect_areas(main_street.id, "west", adventureland.id)

        # Place some items in the world
        map_instance = self.item_manager.create_instance("Lost Map")
        if map_instance: # create_instance returns the item
            fantasyland.add_object_to_grid(map_instance, 2, 2)

        # Create NPCs
        mickey = NPC(name="Mickey Mouse", description="The one and only, cheerful and friendly!")
        mickey.set_location(main_street, 3, 3) # NPCManager adds to its list via set_location if area is given
        self.npc_manager.add_npc(mickey)

        goofy = NPC(name="Goofy", description="A lovable and clumsy friend.")
        goofy.set_location(fantasyland, 5, 5)
        self.npc_manager.add_npc(goofy)

        # Place Player
        self.player.set_current_area(main_street, 1, 1)

        print("The gates are open! Welcome to Disneyland!")
        # self.player.look_around() # set_current_area calls look_around

    def process_command(self, command_input):
        parts = command_input.lower().split()
        if not parts: return

        action = parts[0]
        args = parts[1:]
        target_name = " ".join(args)

        if action in ["n", "north", "s", "south", "e", "east", "w", "west"]:
            direction_map = {"n": "north", "s": "south", "e": "east", "w": "west"}
            self.player.move(direction_map.get(action, action))
        elif action == "look" or action == "l":
            self.player.look_around()
        elif action == "inventory" or action == "i" or action == "bag":
            self.player.show_inventory()
        elif action == "get" or action == "take" or action == "pickup":
            if target_name: self.player.pick_up(target_name)
            else: print("Pickup what? (e.g., get mickey ears)")
        elif action == "drop":
            if target_name: self.player.remove_item_from_inventory(target_name)
            else: print("Drop what?")
        elif action == "buy":
            if target_name: self.player.buy_item(target_name, self.item_manager)
            else: print("Buy what? (e.g., buy churro)")
        elif action == "sell":
            if target_name: self.player.sell_item(target_name)
            else: print("Sell what? (e.g., sell lost map)")
        elif action == "teleport" or action == "tp":
            if not args:
                print("Teleport where? Usage: tp <area_name> [x] [y]")
                return
            
            area_name_parts = []
            tp_x, tp_y = None, None
            
            if len(args) >= 2 and args[-2].isdigit() and args[-1].isdigit():
                try:
                    tp_x = int(args[-2])
                    tp_y = int(args[-1])
                    area_name_parts = args[:-2]
                except ValueError: area_name_parts = args # Not numbers
            else: area_name_parts = args

            target_area_name = " ".join(area_name_parts)
            target_area = self.area_manager.get_area(target_area_name)
            
            if not target_area:
                print(f"Sorry, can't find a place called '{target_area_name}'.")
                return
            self.player.teleport(target_area, tp_x, tp_y)
        elif action == "whereami":
             if self.player.current_area:
                gx, gy = self.player.get_grid_position()
                print(f"You are in {self.player.current_area.name} at grid ({gx},{gy}). Global: {self.player.coordinates}")
             else: print("You are nowhere specific.")
        elif action == "quit" or action == "exit":
            self.running = False
        else:
            print(f"Hmm, I don't know how to '{action}'. Try 'help' for commands.")

    def update_world(self):
        self.game_turn += 1
        npc_action_messages = self.npc_manager.update_all_npcs(self.game_turn)
        for msg in npc_action_messages:
            print(msg) # Print messages from NPC actions

    def run(self):
        print("\nWelcome to your Disneyland Adventure!")
        print("Type 'help' for a list of commands, or 'quit' to exit.")

        original_stdout = sys.stdout
        output_monitor = OutputMonitor(original_stdout)
        sys.stdout = output_monitor

        while self.running:
            command_input = input("\n> ").strip()
            output_monitor.texts_buffer.clear() # Reset for game logic output

            if command_input:
                if command_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("  n, s, e, w (or north, south, east, west) - Move")
                    print("  look (l)          - Look around the area")
                    print("  inventory (i, bag)- Check your bag and money")
                    print("  get <item_name>   - Pick up an item")
                    print("  drop <item_name>  - Drop an item")
                    print("  buy <item_name>   - Buy an item from a shop")
                    print("  sell <item_name>  - Sell an item to a shop")
                    print("  teleport (tp) <area_name> [x] [y] - Fast travel")
                    print("  whereami          - Show your current location details")
                    print("  quit (exit)       - Exit the game")
                else:
                    self.process_command(command_input)
                
                if self.running: # Don't update world if quit command was issued
                    self.update_world() 
            elif self.running: # Empty input, pass turn
                 self.update_world()
            
            buffered_texts = output_monitor.get_buffered_texts_and_reset()

            if self.running and not buffered_texts:
                print(random.choice(self._AMBIENT_NO_EVENT_MESSAGES))

        sys.stdout = original_stdout # Restore original stdout
        print("\nThanks for visiting Disneyland! Come back soon!")