"""
Area module for the Disneyland Adventure game.
Handles game world areas (lands, shops) and their connections.
"""

from .coordinates import Coordinates
from .item import Item # Required for type checking and shop logic

# Forward declaration for type hinting if Land, Ride, Shop were in separate files
# class Land: pass
# class Ride: pass
# class Shop: pass

class Area:
    """Area class representing different locations in the game world."""
    def __init__(self, name, description, area_origin_coords=None, grid_width=10, grid_length=10, parent_area=None):
        self.name = name
        self.description = description
        self.area_origin_coords = area_origin_coords if area_origin_coords else Coordinates(0, 0)
        self.grid_width = grid_width
        self.grid_length = grid_length
        self.connections = {}  # direction_str -> connected_Area_object
        self.grid_objects = {} # (grid_x, grid_y) -> list of objects (Item or NPC instances)
        self.items = [] # List of Item instances physically in this area
        self.npcs = []  # List of NPC instances physically in this area
        self.id = f"area_{name.lower().replace(' ', '_')}"

        # Shop-specific attributes
        self.is_shop = False
        # These will be moved to the Shop subclass
        # self.shop_sells_stock = {}
        # self.shop_buys_stock = {}

        self.parent_area = parent_area # Reference to the containing Area (e.g., a Land)
        self.sub_areas = [] # List of Area objects contained within this one

    def add_connection(self, direction, connected_area):
        """Add a connection to another area and a reverse connection."""
        if not isinstance(connected_area, Area):
            print(f"Error: Attempted to connect {self.name} to non-Area object: {connected_area}")
            return
        self.connections[direction.lower()] = connected_area
        reverse_directions = {
            "north": "south", "south": "north",
            "east": "west", "west": "east",
        }
        if direction.lower() in reverse_directions:
            reverse_dir = reverse_directions[direction.lower()]
            if reverse_dir not in connected_area.connections:
                connected_area.add_connection(reverse_dir, self)

    def add_sub_area(self, sub_area_object):
        """Adds a sub-area (like a Ride or Shop) to this area (typically a Land)."""
        if isinstance(sub_area_object, Area) and sub_area_object not in self.sub_areas:
            self.sub_areas.append(sub_area_object)
            sub_area_object.parent_area = self
            # print(f"DEBUG: Added {sub_area_object.name} as sub-area to {self.name}")

    def is_valid_grid_position(self, grid_x, grid_y):
        return 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_length

    def get_global_coordinates(self, grid_x, grid_y):
        return Coordinates(
            self.area_origin_coords.x + grid_x,
            self.area_origin_coords.y + grid_y
        )

    def get_relative_coordinates(self, global_coords):
        return (
            global_coords.x - self.area_origin_coords.x,
            global_coords.y - self.area_origin_coords.y
        )

    def add_object_to_grid(self, obj, grid_x, grid_y):
        if not self.is_valid_grid_position(grid_x, grid_y):
            print(f"Warning: Cannot place {obj.name} at ({grid_x},{grid_y}) in {self.name}. Out of bounds.")
            return

        obj.coordinates = self.get_global_coordinates(grid_x, grid_y)
        grid_pos = (grid_x, grid_y)
        if grid_pos not in self.grid_objects:
            self.grid_objects[grid_pos] = []
        
        if obj not in self.grid_objects[grid_pos]:
            self.grid_objects[grid_pos].append(obj)

        # Using string comparison for type to avoid circular import with Npc here
        if isinstance(obj, Item) and obj not in self.items:
            self.items.append(obj)
        elif obj.__class__.__name__ == "NPC" and obj not in self.npcs: # Check for NPC type
            self.npcs.append(obj)
            obj.location = self # NPC needs to know its area

    def remove_object_from_grid(self, obj, grid_x, grid_y):
        grid_pos = (grid_x, grid_y)
        if grid_pos in self.grid_objects and obj in self.grid_objects[grid_pos]:
            self.grid_objects[grid_pos].remove(obj)
            if not self.grid_objects[grid_pos]:
                del self.grid_objects[grid_pos]

        if isinstance(obj, Item) and obj in self.items:
            self.items.remove(obj)
        elif obj.__class__.__name__ == "NPC" and obj in self.npcs: # Check for NPC type
            self.npcs.remove(obj)

    def get_objects_at_grid_cell(self, grid_x, grid_y):
        return self.grid_objects.get((grid_x, grid_y), [])

    def __str__(self):
        return f"{self.name} (Origin: {self.area_origin_coords}, Size: {self.grid_width}x{self.grid_length})"

class AreaManager:
    """Manages all areas in the game world."""
    def __init__(self):
        self.areas = {}  # area_id -> Area_object

    def add_area(self, area):
        if area.id in self.areas:
            print(f"Warning: Area with ID '{area.id}' already exists. Overwriting.")
        self.areas[area.id] = area

    def get_area(self, area_id_or_name):
        if area_id_or_name in self.areas:
            return self.areas[area_id_or_name]
        for area in self.areas.values():
            if area.name.lower() == area_id_or_name.lower():
                return area
        return None

    def connect_areas(self, area1_id, direction, area2_id):
        area1 = self.get_area(area1_id)
        area2 = self.get_area(area2_id)
        if area1 and area2:
            area1.add_connection(direction, area2)
            return True
        print(f"Error connecting areas: One or both not found ('{area1_id}', '{area2_id}')")
        return False


class Land(Area):
    """Represents a major themed land in Disneyland, which can contain other areas."""
    def __init__(self, name, description, area_origin_coords=None, grid_width=20, grid_length=20):
        super().__init__(name, description, area_origin_coords, grid_width, grid_length, parent_area=None)
        # Lands typically don't have parents themselves in this model
        self.id = f"land_{name.lower().replace(' ', '_').replace('.', '')}"


class Ride(Area):
    """Represents a ride or attraction. Can be a sub-area of a Land."""
    def __init__(self, name, description, area_origin_coords=None, grid_width=5, grid_length=10, parent_area=None, ride_type="Unknown"):
        super().__init__(name, description, area_origin_coords, grid_width, grid_length, parent_area)
        self.ride_type = ride_type
        self.is_operational = True # By default
        self.suspicion_reduction_on_ride = 5 # Default suspicion reduction
        self.id = f"ride_{name.lower().replace(' ', '_').replace('.', '')}"
        # Could add queue_time, capacity, etc. later

    def experience_ride(self, player):
        if not self.is_operational:
            print(f"{self.name} is currently not operational.")
            return False

        print(f"You decide to experience {self.name}...")
        print(f"After enjoying {self.name}, you feel more like a regular tourist.")
        player.reduce_suspicion_from_activity(self.suspicion_reduction_on_ride)
        return True


class Shop(Area):
    """Represents a shop where items can be bought or sold. Can be a sub-area of a Land."""
    def __init__(self, name, description, area_origin_coords=None, grid_width=5, grid_length=5, parent_area=None):
        super().__init__(name, description, area_origin_coords, grid_width, grid_length, parent_area)
        self.is_shop = True # Mark this area as a shop
        # For items the shop sells to the player: item_name.lower() -> {'prototype': Item_instance, 'price': float, 'stock': int}
        self.shop_sells_stock = {}
        # For items the shop buys from the player: item_name.lower() -> {'buy_price': float, 'desired_stock': int, 'current_stock': int}
        self.shop_buys_stock = {}
        self.id = f"shop_{name.lower().replace(' ', '_').replace('.', '').replace(chr(39), '')}"

    def add_item_to_sell_stock(self, item_prototype, price, quantity):
        """Adds an item type to the shop's for-sale stock."""
        self.shop_sells_stock[item_prototype.name.lower()] = {
            'prototype': item_prototype,
            'price': price,
            'stock': quantity
        }

    def add_item_to_buy_stock(self, item_name, buy_price, desired_stock=10):
        """Adds an item type that the shop is willing to buy from the player."""
        self.shop_buys_stock[item_name.lower()] = {
            'buy_price': buy_price,
            'current_stock': 0, # How many the shop has bought
            'desired_stock': desired_stock
        }

    def get_shop_sell_listing(self, **kwargs): # Added kwargs for potential future use by subclasses
        """Returns a list of strings describing items for sale by the shop."""
        if not self.shop_sells_stock: return []
        listing = ["Items for sale:"]
        for name_key, details in self.shop_sells_stock.items():
            stock_info = "Unlimited" if details['stock'] == float('inf') else str(details['stock'])
            listing.append(f"  - {details['prototype'].name}: ${details['price']:.2f} (Stock: {stock_info})")
        if not listing[1:]: # Only header was added
            return []
        return listing

    def get_shop_buy_listing(self):
        """Returns a list of strings describing items the shop wants to buy."""
        if not self.shop_buys_stock: return []
        listing = ["Items we are buying:"]
        for name_key, details in self.shop_buys_stock.items():
            proper_name = name_key.title()
            needed = details['desired_stock'] - details['current_stock']
            if needed > 0:
                listing.append(f"  - {proper_name}: We'll pay ${details['buy_price']:.2f} (Want: {needed})")
        return listing

    def process_player_purchase(self, item_name_query, player_money, item_manager):
        """Processes a player buying an item from the shop."""
        item_details = self.shop_sells_stock.get(item_name_query.lower())
        if not item_details: return None, 0, "not_found"
        if item_details['stock'] <= 0 and item_details['stock'] != float('inf'): return None, 0, "out_of_stock"
        if player_money < item_details['price']: return None, 0, "cannot_afford"

        if item_details['stock'] != float('inf'):
            item_details['stock'] -= 1
        
        new_item_instance = item_manager.create_instance(item_details['prototype'].name)
        if not new_item_instance:
            return None, 0, "creation_failed"
            
        return new_item_instance, item_details['price'], "success"


class FenceShop(Shop):
    """A special shop that only buys unpaid items from the player at a low price."""
    def __init__(self, name, description, area_origin_coords=None, grid_width=3, grid_length=3, parent_area=None, fence_cut=0.25):
        super().__init__(name, description, area_origin_coords, grid_width, grid_length, parent_area)
        self.fence_cut = fence_cut # The percentage of item's value the fence offers
        self.id = f"fenceshop_{name.lower().replace(' ', '_').replace('.', '').replace(chr(39), '')}"
        # FenceShops don't have regular sell stock or buy stock in the traditional sense.
        self.shop_sells_stock = {} # They don't sell anything
        self.shop_buys_stock = {}  # This will be dynamically determined

    def get_shop_buy_listing(self, player_inventory=None):
        """Dynamically lists unpaid items from player's inventory that the fence will buy."""
        if player_inventory is None:
            return ["The fence eyes you suspiciously. 'Whatcha got?'"]

        listing = ["The fence looks over your goods... 'I might be interested in these...'"]
        found_items = False
        for item in player_inventory:
            if item.is_unpaid:
                buy_price = round(item.value * self.fence_cut)
                listing.append(f"  - {item.name} (stolen): We'll give ya ${buy_price:.2f}")
                found_items = True
        
        if not found_items:
            return ["'Got nothin' I want from you right now,' the fence grunts."]
        return listing

    # Note: The actual selling logic will primarily be handled in Player.sell_item
    # when interacting with a FenceShop, as it needs access to player's inventory
    # and money directly. This shop class mainly defines its unique buying behavior/listings.
    # We can add a helper here if needed.
    def get_fence_price(self, item_value):
        return round(item_value * self.fence_cut)