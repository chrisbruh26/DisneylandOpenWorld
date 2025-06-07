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
        # The global coordinates of the (0,0) point of this area's grid
        self.area_origin_coords = area_origin_coords if area_origin_coords else Coordinates(0, 0, 0)
        self.grid_width = grid_width
        self.grid_length = grid_length
        self.connections = {}  # direction_str -> connected_Area_object
        
        # For objects within the area's grid
        # Key: (grid_x, grid_y), Value: list of objects (Item or NPC instances)
        self.grid_objects = {} 
        self.items = [] # List of Item instances physically in this area
        self.npcs = []  # List of NPC instances physically in this area
        self.portals = {} # (grid_x, grid_y) -> {'target_area': AreaObject, 'target_gx': int_or_None, 'target_gy': int_or_None}
        self.id = f"area_{name.lower().replace(' ', '_')}"

        # Shop-specific attributes
        self.is_shop = False
        self.is_shelter = False # Flag to indicate if this area is a good place to hide
        
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
            "up": "down", "down": "up" # For potential future use
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

    def add_portal(self, from_gx, from_gy, target_area, target_gx=None, target_gy=None):
        """Adds a portal at a specific grid cell that teleports to another area."""
        if not self.is_valid_grid_position(from_gx, from_gy):
            print(f"Warning: Cannot add portal at invalid grid ({from_gx},{from_gy}) in {self.name}.")
            return
        if not isinstance(target_area, Area): # Ensure target_area is an Area instance
            print(f"Warning: Portal target in {self.name} from ({from_gx},{from_gy}) is not a valid Area object: {target_area}")
            return
        self.portals[(from_gx, from_gy)] = {
            'target_area': target_area,
            'target_gx': target_gx, # Target grid x in the new area (optional, defaults to center)
            'target_gy': target_gy  # Target grid y in the new area (optional, defaults to center)
        }

    def is_valid_grid_position(self, grid_x, grid_y):
        """Check if the given grid coordinates are within the area's bounds."""
        return 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_length

    def get_global_coordinates(self, grid_x, grid_y, grid_z=0):
        """Convert local grid coordinates to global world coordinates."""
        return Coordinates(
            self.area_origin_coords.x + grid_x,
            self.area_origin_coords.y + grid_y,
            self.area_origin_coords.z + grid_z # Assuming items/NPCs are at base Z of area for now
        )

    def get_relative_coordinates(self, global_coords):
        """Convert global world coordinates to local grid coordinates."""
        return (
            global_coords.x - self.area_origin_coords.x,
            global_coords.y - self.area_origin_coords.y,
            global_coords.z - self.area_origin_coords.z
        )

    def add_object_to_grid(self, obj, grid_x, grid_y):
        """Adds an object (Item or NPC) to a specific grid cell and updates its global coords."""
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
        """Removes an object from a specific grid cell."""
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
        """Get all objects at a specific grid cell."""
        return self.grid_objects.get((grid_x, grid_y), [])

    def __str__(self):
        return f"{self.name} (Origin: {self.area_origin_coords}, Size: {self.grid_width}x{self.grid_length})"

class AreaGroup:
    """Manages a group of related areas, like a land complex."""
    def __init__(self, name, origin_coords=None):
        self.name = name
        self.origin_coords = origin_coords if origin_coords else Coordinates(0, 0, 0)
        self.areas = {}  # area_id -> Area_object
        self.layout = {}  # Stores relative positions of areas within the group
        
    def add_area(self, area, relative_position=None):
        """
        Add an area to the group with an optional relative position.
        relative_position can be:
        - None: No specific position
        - "center": Center of the group
        - (x_offset, y_offset): Relative to group origin
        - {"from": "area_id", "direction": "north/south/east/west", "distance": 10}
        """
        if area.id in self.areas:
            print(f"Warning: Area with ID '{area.id}' already exists in group '{self.name}'. Overwriting.")
        
        self.areas[area.id] = area
        
        # Set area coordinates based on relative position
        if relative_position is None:
            # Default placement at group origin
            area.area_origin_coords = Coordinates(
                self.origin_coords.x,
                self.origin_coords.y,
                self.origin_coords.z
            )
        elif relative_position == "center":
            # Place at group origin
            area.area_origin_coords = Coordinates(
                self.origin_coords.x,
                self.origin_coords.y,
                self.origin_coords.z
            )
        elif isinstance(relative_position, tuple) and len(relative_position) == 2:
            # Place at offset from group origin
            x_offset, y_offset = relative_position
            area.area_origin_coords = Coordinates(
                self.origin_coords.x + x_offset,
                self.origin_coords.y + y_offset,
                self.origin_coords.z
            )
        elif isinstance(relative_position, dict) and "from" in relative_position and "direction" in relative_position:
            # Place relative to another area in the group
            from_area_id = relative_position["from"]
            direction = relative_position["direction"]
            distance = relative_position.get("distance", 20)  # Default distance
            
            if from_area_id in self.areas:
                from_area = self.areas[from_area_id]
                
                # Calculate new coordinates based on direction
                if direction == "north":
                    area.area_origin_coords = Coordinates(
                        from_area.area_origin_coords.x,
                        from_area.area_origin_coords.y - distance,
                        from_area.area_origin_coords.z
                    )
                elif direction == "south":
                    area.area_origin_coords = Coordinates(
                        from_area.area_origin_coords.x,
                        from_area.area_origin_coords.y + distance,
                        from_area.area_origin_coords.z
                    )
                elif direction == "east":
                    area.area_origin_coords = Coordinates(
                        from_area.area_origin_coords.x + distance,
                        from_area.area_origin_coords.y,
                        from_area.area_origin_coords.z
                    )
                elif direction == "west":
                    area.area_origin_coords = Coordinates(
                        from_area.area_origin_coords.x - distance,
                        from_area.area_origin_coords.y,
                        from_area.area_origin_coords.z
                    )
            else:
                print(f"Warning: Reference area '{from_area_id}' not found in group. Using group origin.")
                area.area_origin_coords = Coordinates(
                    self.origin_coords.x,
                    self.origin_coords.y,
                    self.origin_coords.z
                )
        
        # Store the layout information
        self.layout[area.id] = {
            "area": area,
            "relative_position": relative_position
        }
        
    def connect_areas_in_group(self, area1_id, direction, area2_id):
        """Connect two areas within the group."""
        if area1_id in self.areas and area2_id in self.areas:
            self.areas[area1_id].add_connection(direction, self.areas[area2_id])
            return True
        return False
    
    def connect_all_adjacent_areas(self):
        """
        Automatically connect areas that are adjacent to each other.
        This is useful for creating a connected complex like a land.
        """
        # This is a simplified version - in a real implementation, you'd check
        # actual adjacency based on coordinates and dimensions
        for area1_id, area1_data in self.layout.items():
            area1 = area1_data["area"]
            for area2_id, area2_data in self.layout.items():
                if area1_id == area2_id:
                    continue
                    
                area2 = area2_data["area"]
                
                # Check if areas are adjacent (simplified)
                # East-West adjacency
                if (abs(area1.area_origin_coords.x + area1.grid_width - area2.area_origin_coords.x) < 5 and
                    abs(area1.area_origin_coords.y - area2.area_origin_coords.y) < 5):
                    area1.add_connection("east", area2)
                
                # West-East adjacency
                if (abs(area1.area_origin_coords.x - (area2.area_origin_coords.x + area2.grid_width)) < 5 and
                    abs(area1.area_origin_coords.y - area2.area_origin_coords.y) < 5):
                    area1.add_connection("west", area2)
                
                # North-South adjacency
                if (abs(area1.area_origin_coords.y - (area2.area_origin_coords.y + area2.grid_length)) < 5 and
                    abs(area1.area_origin_coords.x - area2.area_origin_coords.x) < 5):
                    area1.add_connection("north", area2)
                
                # South-North adjacency
                if (abs(area1.area_origin_coords.y + area1.grid_length - area2.area_origin_coords.y) < 5 and
                    abs(area1.area_origin_coords.x - area2.area_origin_coords.x) < 5):
                    area1.add_connection("south", area2)

class AreaManager:
    """Manages all areas in the game world."""
    def __init__(self):
        self.areas = {}  # area_id -> Area_object
        self.area_groups = {}  # group_name -> AreaGroup_object

    def add_area(self, area):
        """Add an area to the manager."""
        if area.id in self.areas:
            print(f"Warning: Area with ID '{area.id}' already exists. Overwriting.")
        self.areas[area.id] = area

    def get_area(self, area_id_or_name):
        """Get an area by its ID or case-insensitive name."""
        if area_id_or_name in self.areas:
            return self.areas[area_id_or_name]
        for area in self.areas.values():
            if area.name.lower() == area_id_or_name.lower():
                return area
        return None
    
    def get_area_by_id(self, area_id):
        """Get an area by its exact ID."""
        return self.areas.get(area_id)

    def find_areas_by_partial_name(self, search_term):
        """Finds areas whose names contain the search_term (case-insensitive)."""
        if not search_term:
            return []
        
        found_areas = []
        search_term_lower = search_term.lower()
        for area_obj in self.areas.values():
            if search_term_lower in area_obj.name.lower():
                found_areas.append(area_obj)
        return found_areas

    def connect_areas(self, area1_id, direction, area2_id):
        """Connect two areas in the specified direction."""
        area1 = self.get_area(area1_id)
        area2 = self.get_area(area2_id)
        if area1 and area2:
            area1.add_connection(direction, area2)
            return True
        print(f"Error connecting areas: One or both not found ('{area1_id}', '{area2_id}')")
        return False
        
    def create_area_group(self, name, origin_coords=None):
        """Create a new area group."""
        group = AreaGroup(name, origin_coords)
        self.area_groups[name.lower()] = group
        return group
        
    def get_area_group(self, name):
        """Get an area group by name."""
        return self.area_groups.get(name.lower())
        
    def register_areas_from_group(self, group_name):
        """Register all areas from a group with the main area manager."""
        group = self.get_area_group(group_name)
        if not group:
            print(f"Area group '{group_name}' not found.")
            return False
            
        for area_id, area in group.areas.items():
            self.add_area(area)
        
        return True
        
    def list_areas(self, include_connections=True, include_coords=True):
        """List all areas including their IDs and optionally connections."""
        print("\n=== GAME AREAS ===")
        print(f"Total areas: {len(self.areas)}")
        
        # Group areas by complex/group
        area_groups = {}
        for area in self.areas.values():
            # Extract group name from area name if possible
            group_name = "Ungrouped"
            if " Land " in area.name:
                group_name = "Land Complex"
            elif "Disneyland" in area.name:
                group_name = "Disneyland"
            elif area.name in ["Main Street U.S.A.", "Adventureland", "Fantasyland"]:
                group_name = "Main Areas"
                
            if group_name not in area_groups:
                area_groups[group_name] = []
            area_groups[group_name].append(area)
        
        # Print areas by group
        for group_name, areas in sorted(area_groups.items()):
            print(f"\n{group_name} ({len(areas)} areas):")
            for area in sorted(areas, key=lambda a: a.name):
                print(f"  ID: {area.id}, Name: {area.name}")
                if include_coords:
                    print(f"    Coordinates: {area.area_origin_coords}")
                if include_connections:
                    connections = [f"{dir}: {conn.name}" for dir, conn in area.connections.items()]
                    if connections:
                        print(f"    Connections: {', '.join(connections)}")
                    else:
                        print("    Connections: None")
        print("\n=== END OF AREAS ===\n")


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