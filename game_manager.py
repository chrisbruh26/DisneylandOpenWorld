"""
Game Manager module for the Disneyland Adventure game.
Handles game state, setup, and command processing.
"""
import random
import sys

from .player import Player
from .area import Area, AreaManager, Land, Ride, Shop # Import new classes
from .area import FenceShop # Import FenceShop
from .item import Item, ItemManager
from .npc import NPC, NPCManager, ParkCharacter, Guest, CastMember # Import new NPC types
from .npc import ShadyCharacter # Import ShadyCharacter
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

        # --- Create Lands ---
        main_street_land = Land(name="Main Street U.S.A.", description="A charming turn-of-the-century American town square.", grid_width=15, grid_length=5)
        self.area_manager.add_area(main_street_land)

        adventureland = Land(name="Adventureland", description="An exotic land of jungles, rivers, and mystery.", grid_width=20, grid_length=15)
        self.area_manager.add_area(adventureland)

        fantasyland = Land(name="Fantasyland", description="A whimsical land of fairy tales and dreams.", grid_width=18, grid_length=18)
        self.area_manager.add_area(fantasyland)

        # --- Create Shops and Rides within Lands ---

        # Main Street Shops
        emporium = Shop(name="Emporium", description="The largest gift shop on Main Street, full of souvenirs.", parent_area=main_street_land, grid_width=6, grid_length=4)
        # Position Emporium within Main Street's conceptual space (global coords)
        emporium.area_origin_coords = Coordinates(main_street_land.area_origin_coords.x + 2, main_street_land.area_origin_coords.y + 0)
        emporium.add_item_to_sell_stock(self.item_manager.item_prototypes["mickey ears"], price=15, quantity=20)
        emporium.add_item_to_sell_stock(self.item_manager.item_prototypes["churro"], price=6, quantity=30) # Slightly more expensive here
        emporium.add_item_to_buy_stock("Lost Map", buy_price=0.50, desired_stock=3)
        self.area_manager.add_area(emporium)
        main_street_land.add_sub_area(emporium) # Link it as a sub_area

        # Adventureland Rides & Shops
        jungle_cruise_queue = Ride(name="Jungle Cruise Queue", description="The winding queue for the world-famous Jungle Cruise.", parent_area=adventureland, ride_type="Boat Ride", grid_width=3, grid_length=8)
        jungle_cruise_queue.area_origin_coords = Coordinates(adventureland.area_origin_coords.x + 5, adventureland.area_origin_coords.y + 2)
        jungle_cruise_queue.suspicion_reduction_on_ride = 7 # Specific value for this ride
        self.area_manager.add_area(jungle_cruise_queue)
        adventureland.add_sub_area(jungle_cruise_queue)

        adventure_bazaar = Shop(name="Adventureland Bazaar", description="A marketplace full of exotic treasures.", parent_area=adventureland, grid_width=4, grid_length=4)
        adventure_bazaar.area_origin_coords = Coordinates(adventureland.area_origin_coords.x + 1, adventureland.area_origin_coords.y + 10)
        adventure_bazaar.add_item_to_sell_stock(self.item_manager.item_prototypes["lost map"], price=2, quantity=10) # They sell maps!
        self.area_manager.add_area(adventure_bazaar)
        adventureland.add_sub_area(adventure_bazaar)

        # Add a FenceShop and a ShadyCharacter
        hidden_alley = FenceShop(name="Hidden Alley", description="A dark, out-of-the-way alley. Smells faintly of desperation.", parent_area=adventureland, fence_cut=0.3)
        hidden_alley.area_origin_coords = Coordinates(adventureland.area_origin_coords.x + 18, adventureland.area_origin_coords.y + 1) # Tucked away
        self.area_manager.add_area(hidden_alley)
        adventureland.add_sub_area(hidden_alley) # It's "in" Adventureland
        shady_sam = ShadyCharacter(name="Shady Sam", description="A nervous-looking individual who keeps glancing over his shoulder.")
        shady_sam.set_location(hidden_alley, 1, 1) # Placed within the alley
        self.npc_manager.add_npc(shady_sam)

        # --- Connect Lands and Sub-Areas ---
        self.area_manager.connect_areas(main_street_land.id, "north", fantasyland.id) # Main Street path leads to Fantasyland path
        self.area_manager.connect_areas(main_street_land.id, "west", adventureland.id) # Main Street path leads to Adventureland path
        
        # Connections for entering/exiting sub-areas (shops, rides)
        # These are conceptual "doors" or transition points.
        # Player uses "enter <sub_area_name>" or "exit to <parent_area_name>"
        # Main Street <-> Emporium
        main_street_land.add_connection("enter emporium", emporium) # A conceptual "action" or a specific grid point exit
        emporium.add_connection("exit to main street", main_street_land)

        # Adventureland <-> Jungle Cruise Queue
        adventureland.add_connection("enter jungle cruise", jungle_cruise_queue)
        jungle_cruise_queue.add_connection("exit to adventureland", adventureland)
        
        # Adventureland <-> Adventureland Bazaar
        adventureland.add_connection("enter bazaar", adventure_bazaar) # Changed from "enter adventureland bazaar" for brevity
        adventure_bazaar.add_connection("exit to adventureland", adventureland)

        # Adventureland <-> Hidden Alley (FenceShop)
        adventureland.add_connection("enter alley", hidden_alley)
        hidden_alley.add_connection("exit to adventureland", adventureland)

        # Place some items in the world
        map_instance = self.item_manager.create_instance("Lost Map")
        if map_instance: # create_instance returns the item
            adventureland.add_object_to_grid(map_instance, 10, 10) # Lost map in Adventureland

        # Create NPCs
        mickey = ParkCharacter(name="Mickey Mouse", description="The one and only, cheerful and friendly!", signature_move="gives a friendly wave and a chuckle")
        mickey.set_location(main_street_land, 7, 2) 
        self.npc_manager.add_npc(mickey)

        goofy = ParkCharacter(name="Goofy", description="A lovable and clumsy friend.", signature_move="stumbles a bit but recovers with a 'Gawrsh!'")
        goofy.set_location(fantasyland, 5, 5)
        self.npc_manager.add_npc(goofy)

        # Add Cast Members to the Emporium
        cm_alice = CastMember(name="Alice", description="A helpful Cast Member at the till.", role="Cashier")
        cm_alice.set_location(emporium, 1, 1) # Near a till
        self.npc_manager.add_npc(cm_alice)

        cm_bob = CastMember(name="Bob", description="A vigilant Cast Member keeping an eye on the displays.", role="Floor Staff")
        cm_bob.set_location(emporium, 4, 2) # Roaming the floor
        self.npc_manager.add_npc(cm_bob)

        # Place Player
        self.player.set_current_area(main_street_land, 1, 1)

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
        # Allow moving into sub-areas by name (simple version)
        elif action == "enter" and args:
            target_sub_area_name = " ".join(args)
            if self.player.current_area and target_sub_area_name.lower() in self.player.current_area.connections:
                self.player.move(target_sub_area_name.lower()) # Use the connection key
            else:
                print(f"You can't seem to enter '{target_sub_area_name}' from here.")
        elif action == "look" or action == "l":
            self.player.look_around()
        elif action == "inventory" or action == "i" or action == "bag":
            self.player.show_inventory()
        elif action == "get" or action == "take" or action == "pickup":
            if target_name: self.player.pick_up(target_name, self.item_manager) # Pass item_manager
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
        elif action == "ride":
            if not isinstance(self.player.current_area, Ride):
                print("You need to be in a ride area (like a queue) to experience a ride.")
                # Check if player is in a Land and there's a ride with that name as a sub-area
                if args and self.player.current_area and hasattr(self.player.current_area, 'sub_areas'):
                    target_ride_name_for_suggestion = " ".join(args)
                    for sub_area in self.player.current_area.sub_areas:
                        if isinstance(sub_area, Ride) and sub_area.name.lower() == target_ride_name_for_suggestion.lower():
                            print(f"Try 'enter {sub_area.name}' first.")
                            break
                return

            ride_area = self.player.current_area # This is a Ride object
            if args and " ".join(args).lower() != ride_area.name.lower():
                print(f"You are in {ride_area.name}. If you want to ride this, just type 'ride'.")
                return

            ride_area.experience_ride(self.player)
            # The turn will advance in update_world()
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
        elif action == "where":
            if not args:
                print("Where what? Please specify what you are looking for (e.g., where Jungle Cruise).")
                return
            
            search_term = " ".join(args).lower()
            found_locations = []
            for area_obj in self.area_manager.areas.values(): # Iterate through Area objects
                if search_term in area_obj.name.lower():
                    found_locations.append(area_obj)

            if not found_locations:
                print(f"No place matching '{' '.join(args)}' was found.")
            else:
                print(f"Locations matching '{' '.join(args)}':")
                for loc in found_locations:
                    print(f"  - {loc.name}: Starts around global coordinates {loc.area_origin_coords}.")
            self.running = False
        else:
            print(f"Command not understood. Try 'help' for commands.")

    def update_world(self):
        self.game_turn += 1
        npc_action_messages = self.npc_manager.update_all_npcs(self.game_turn)
        self.player.update_suspicion_decay() # Player's suspicion passively decays
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
                    print("  enter <place_name> - Enter a shop or ride queue from a Land")
                    print("  look (l)          - Look around the area")
                    print("  inventory (i, bag)- Check your bag and money")
                    print("  get <item_name>   - Pick up an item")
                    print("  drop <item_name>  - Drop an item")
                    print("  buy <item_name>   - Buy an item from a shop")
                    print("  sell <item_name>  - Sell an item to a shop")
                    print("  ride              - Experience the ride you are currently in (e.g., a ride queue)")
                    print("  teleport (tp) <area_name> [x] [y] - Fast travel")
                    print("  where <place_name> - Find the global coordinates of a place")
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