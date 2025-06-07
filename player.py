"""
Player module for the Disneyland Adventure game.
Handles the player character and their interactions.
"""
from .coordinates import Coordinates
from .area import Land, FenceShop # To check instance type for get_current_land and FenceShop
from .item import Item # For type hinting and isinstance checks
import random
class Player:
    """Player class for the game."""
    def __init__(self, name="Adventurer", start_money=100):
        self.name = name
        self.inventory = []
        self.current_area = None
        self.coordinates = Coordinates(0, 0) # Global coordinates
        self.money = start_money
        self.suspicion_rating = 0 # How suspicious the player appears to Cast Members

    def set_current_area(self, area, grid_x=None, grid_y=None):
        """Set the current area for the player and position them on its grid."""
        old_area_being_left = self.current_area # Store the area player is LEAVING

        self.current_area = area
        if area:
            if grid_x is None: grid_x = area.grid_width // 2
            if grid_y is None: grid_y = area.grid_length // 2
            
            grid_x = max(0, min(grid_x, area.grid_width - 1))
            grid_y = max(0, min(grid_y, area.grid_length - 1))

            self.coordinates = area.get_global_coordinates(grid_x, grid_y)
            
            # Check for theft when leaving a shop
            # This check is for when player leaves 'old_area_being_left' if it was a shop,
            # and isn't just moving to its parent area (which is a normal exit).
            if old_area_being_left and hasattr(old_area_being_left, 'is_shop') and old_area_being_left.is_shop:
                if area != old_area_being_left and area != old_area_being_left.parent_area:
                    self.check_for_theft(old_area_being_left)

            print(f"You are now in {area.name}. {area.description}") # Message after potential theft check
            self.look_around()
        else:
            print("Error: Tried to move to a null area.")
            self.current_area = old_area_being_left # Revert if new area is null

    def get_grid_position(self):
        """Get the player's position relative to the current area's grid."""
        if not self.current_area: return None, None
        rel_coords = self.current_area.get_relative_coordinates(self.coordinates)
        return int(rel_coords[0]), int(rel_coords[1])

    def get_current_land_name(self):
        """Traverses up parent_area to find the name of the Land the player is in."""
        if not self.current_area:
            return None
        
        area = self.current_area
        # If current_area is already a Land, its parent is None.
        # If current_area is a sub-area, traverse up.
        while area.parent_area:
            area = area.parent_area
        
        # Now 'area' is the topmost area in this hierarchy.
        # We assume a Land will not have a parent_area.
        if isinstance(area, Land): # Check if it's a Land instance
            return area.name
        elif not area.parent_area: # It's a top-level area but not specifically a Land
             return area.name # Could be a standalone area not part of a Land
        return None # Should not happen if structure is correct

    def look_around(self):
        if not self.current_area:
            print("You are floating in a magical void...")
            return
        grid_x, grid_y = self.get_grid_position()
        
        current_land_name = self.get_current_land_name()
        location_header = self.current_area.name
        if current_land_name and self.current_area.name != current_land_name:
            location_header += f" (in {current_land_name})"

        print(f"\n--- {location_header} ---")
        print(self.current_area.description)
        print(f"You are at grid position ({grid_x}, {grid_y}).")

        objects_here = self.current_area.get_objects_at_grid_cell(grid_x, grid_y)
        items_here = [obj for obj in objects_here if isinstance(obj, Item)]
        if items_here:
            print("Items at your feet:")
            for item in items_here: print(f"  - {item.name}: {item.description}")
        
        npcs_here = [obj for obj in objects_here if obj.__class__.__name__ == "NPC"]
        if npcs_here:
            print("People here:")
            for npc in npcs_here: print(f"  - {npc.name}")

        # Show other items/NPCs in the current specific area
        other_items_in_current_area = [item for item in self.current_area.items if item not in items_here]
        if other_items_in_current_area:
            print("Other items in this spot:")
            for item in other_items_in_current_area:
                item_gx, item_gy = self.current_area.get_relative_coordinates(item.coordinates)[:2]
                print(f"  - {item.name} at ({int(item_gx)}, {int(item_gy)})")

        # Only show NPCs that are close enough to be visible (within 10 units)
        visible_npcs_in_current_area = []
        for npc in self.current_area.npcs:
            if npc not in npcs_here:
                # Calculate distance to player
                npc_distance = npc.coordinates.distance_to(self.coordinates)
                if npc_distance <= 10:  # Only include NPCs within visible range
                    visible_npcs_in_current_area.append((npc, npc_distance))
        
        if visible_npcs_in_current_area:
            print("Other people you can see:")
            # Sort by distance, closest first
            for npc, distance in sorted(visible_npcs_in_current_area, key=lambda x: x[1]):
                npc_gx, npc_gy = self.current_area.get_relative_coordinates(npc.coordinates)[:2]
                print(f"  - {npc.name} at ({int(npc_gx)}, {int(npc_gy)}) - {distance:.1f} units away")

        # Show sub-areas if the current area is a Land (or a container)
        if self.current_area.sub_areas:
            print("Places inside here:")
            for sub_area in self.current_area.sub_areas:
                print(f"  - Entrance to {sub_area.name}") # Could be more descriptive

        if self.current_area.connections:
            # Filter out connections that are just for entering sub-areas if already listed
            # This is a bit simplistic; a better way would be to tag connection types.
            listed_sub_area_names = [sa.name.lower() for sa in self.current_area.sub_areas]
            main_exits = {d: a for d, a in self.current_area.connections.items() if not any(sub_name in d for sub_name in listed_sub_area_names) or a not in self.current_area.sub_areas}
            if main_exits: print("Exits:")
            for direction, area in self.current_area.connections.items():
                print(f"  - {direction.capitalize()}: to {area.name}")
        
        if hasattr(self.current_area, 'get_shop_sell_listing'): # Check if it's a Shop instance
            # Pass player inventory to fence shop for its dynamic listing
            if isinstance(self.current_area, FenceShop):
                for line in self.current_area.get_shop_buy_listing(player_inventory=self.inventory): print(f"  {line}")
            else: # Regular shop
                for line in self.current_area.get_shop_sell_listing(): print(f"  {line}")
                for line in self.current_area.get_shop_buy_listing(): print(f"  {line}")
        print("---")

    def move(self, direction):
        if not self.current_area:
            print("You can't move, you're not in any area.")
            return

        grid_x, grid_y = self.get_grid_position()
        new_grid_x, new_grid_y = grid_x, grid_y

        if direction == "north": new_grid_y += 1
        elif direction == "south": new_grid_y -= 1
        elif direction == "east": new_grid_x += 1
        elif direction == "west": new_grid_x -= 1
        else:
            if direction in self.current_area.connections:
                self.set_current_area(self.current_area.connections[direction])
                return
            print(f"Unknown direction: {direction}.")
            return

        if self.current_area.is_valid_grid_position(new_grid_x, new_grid_y):
            self.coordinates = self.current_area.get_global_coordinates(new_grid_x, new_grid_y)
            print(f"You move {direction}.")

            # Check for portals at the new location
            current_gx, current_gy = self.get_grid_position()
            if (current_gx, current_gy) in self.current_area.portals:
                portal_info = self.current_area.portals[(current_gx, current_gy)]
                target_area = portal_info['target_area']
                target_gx = portal_info.get('target_gx')
                target_gy = portal_info.get('target_gy')
                
                if target_area == self.current_area.parent_area:
                     print(f"You find an exit from {self.current_area.name} and step back into {target_area.name}.")
                else:
                     print(f"You step through an opening into {target_area.name}...")
                self.set_current_area(target_area, target_gx, target_gy)
                return # Movement and transition complete
            # No portal, just regular move.

        elif direction in self.current_area.connections: # Edge of grid, try connection
            target_area = self.current_area.connections[direction]
            print(f"You head {direction} and arrive in {target_area.name}.")
            # Enter new area at its default position (usually center)
            self.set_current_area(target_area) 
            return
        else:
            print("You can't go that way. Perhaps a wall or the edge of the park?")

    def teleport(self, target_area, grid_x=None, grid_y=None):
        if not target_area:
            print("Teleport target area not found.")
            return
        self.set_current_area(target_area, grid_x, grid_y)
        # set_current_area already prints arrival message.

    def add_item_to_inventory(self, item, purchased=False):
        self.inventory.append(item)
        item.coordinates = None # Item is no longer in the world grid
        # is_unpaid and unpaid_from_shop_id should be set before calling this
        if item.is_unpaid:
            print(f"You discreetly take {item.name}.")
        elif not purchased: # Only print if it's a regular pickup, not a purchase
            print(f"You got {item.name}.")

    def reduce_suspicion_from_activity(self, amount):
        if self.suspicion_rating > 0:
            old_suspicion = self.suspicion_rating
            self.suspicion_rating = max(0, self.suspicion_rating - amount)
            reduction_amount = old_suspicion - self.suspicion_rating
            if reduction_amount > 0: # Only print if there was an actual reduction
                print(f"(Your suspicion rating decreased by {reduction_amount}.)")

    def update_suspicion_decay(self):
        """Passively decays suspicion over time."""
        self.reduce_suspicion_from_activity(0.5) # Decay by 0.5 each turn
    def remove_item_from_inventory(self, item_name):
        item_to_drop = None
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                item_to_drop = item
                break
        
        if item_to_drop:
            self.inventory.remove(item_to_drop)
            print(f"You dropped {item_to_drop.name}.")
            if self.current_area:
                player_gx, player_gy = self.get_grid_position()
                self.current_area.add_object_to_grid(item_to_drop, player_gx, player_gy)
        else:
            print(f"You don't have '{item_name}' in your inventory.")

    def pick_up(self, item_name_query, item_manager): # Added item_manager
        if not self.current_area:
            print("You are not in an area to pick up items from.")
            return

        player_gx, player_gy = self.get_grid_position()
        objects_at_player = self.current_area.get_objects_at_grid_cell(player_gx, player_gy)
        item_to_pickup = None

        # Case 1: Picking up a loose item already existing in the area's grid
        for obj in objects_at_player:
            if isinstance(obj, Item) and obj.name.lower() == item_name_query.lower():
                if obj.pickupable:
                    item_to_pickup = obj
                    break
                else:
                    print(f"You can't pick up {obj.name}.")
                    return
        if item_to_pickup:
            self.current_area.remove_object_from_grid(item_to_pickup, player_gx, player_gy)
            self.add_item_to_inventory(item_to_pickup, purchased=False)
            return

        # Case 2: "Picking up" (potentially stealing) an item from a shop's stock
        if hasattr(self.current_area, 'shop_sells_stock'): # It's a Shop
            shop_item_details = self.current_area.shop_sells_stock.get(item_name_query.lower())
            if shop_item_details and shop_item_details['stock'] > 0:
                # Create a new instance of the item for the player
                stolen_item_instance = item_manager.create_instance(shop_item_details['prototype'].name)
                if stolen_item_instance:
                    stolen_item_instance.is_unpaid = True
                    stolen_item_instance.unpaid_from_shop_id = self.current_area.id
                    self.add_item_to_inventory(stolen_item_instance, purchased=False) # is_unpaid handles message
                    # Note: We are NOT decrementing shop_sells_stock here.
                    # The item is "taken" but the shop still thinks it has it for sale.
                    # This simplifies things; otherwise, we'd need to handle "phantom stock".
                    # The consequence is purely on the player if caught.
                    self.suspicion_rating += 5 # Taking an item increases suspicion
                    return
                else:
                    print(f"Error: Could not create an instance of {item_name_query} to take.")
                    return

        print(f"You don't see '{item_name_query}' here to pick up, or it's not available in the shop.")

    def show_inventory(self):
        if not self.inventory: print("Your bag is empty.")
        else:
            print("\nYour Bag:")
            for item in self.inventory: print(f"  - {item.name}")
        print(f"Park Tickets (Money): ${self.money:.2f}")
        print(f"Suspicion Rating: {self.suspicion_rating}")

    def buy_item(self, item_name_query, item_manager):
        if not self.current_area or not hasattr(self.current_area, 'process_player_purchase'):
            print("This isn't a place where you can buy things.")
            return

        # First, check if player is trying to "buy" an item they already "took" (is_unpaid)
        for item_in_inv in self.inventory:
            if item_in_inv.name.lower() == item_name_query.lower() and \
               item_in_inv.is_unpaid and \
               item_in_inv.unpaid_from_shop_id == self.current_area.id:
                
                item_price = self.current_area.shop_sells_stock.get(item_name_query.lower(), {}).get('price', item_in_inv.value)
                if self.money >= item_price:
                    self.money -= item_price
                    item_in_inv.is_unpaid = False
                    item_in_inv.unpaid_from_shop_id = None
                    print(f"You pay for the {item_in_inv.name} you were holding. Cost: ${item_price:.2f}. Money: ${self.money:.2f}")
                    self.reduce_suspicion_from_activity(5) # Paying reduces suspicion
                    # Potentially reduce shop stock if we were tracking that for stolen items
                    # shop_details = self.current_area.shop_sells_stock.get(item_name_query.lower())
                    # if shop_details and shop_details['stock'] != float('inf'):
                    #    shop_details['stock'] -=1 # This is if we want to actually reduce stock on payment of a taken item
                    return
                else:
                    print(f"You try to pay for {item_in_inv.name}, but you can't afford the ${item_price:.2f}.")
                    return

        # If not paying for an already taken item, proceed with normal purchase
        item_instance, price, status = self.current_area.process_player_purchase(item_name_query, self.money, item_manager)

        if status == "success" and item_instance:
            self.money -= price
            self.add_item_to_inventory(item_instance, purchased=True)
            print(f"You bought {item_instance.name} for ${price:.2f}. Remaining money: ${self.money:.2f}")
            self.reduce_suspicion_from_activity(1) # Small reduction for normal shopping
        elif status == "not_found": print(f"The shop doesn't seem to have '{item_name_query}'.")
        elif status == "out_of_stock": print(f"'{item_name_query}' is out of stock.")
        elif status == "cannot_afford": print(f"You can't afford that. It costs ${getattr(self.current_area, 'shop_sells_stock', {}).get(item_name_query.lower(), {}).get('price', 0.0):.2f}.")
        elif status == "creation_failed": print("Something went wrong creating the item.")

    def sell_item(self, item_name_query):
        if not self.current_area:
            print("This isn't a place where you can sell things.")
            return

        item_to_sell = None
        for item_in_inv in self.inventory:
            if item_in_inv.name.lower() == item_name_query.lower():
                item_to_sell = item_in_inv
                break

        if not item_to_sell:
            print(f"You don't have '{item_name_query}' to sell.")
            return

        # Handle selling to a FenceShop
        if isinstance(self.current_area, FenceShop):
            if not item_to_sell.is_unpaid:
                print(f"'I only deal in... acquired goods,' the fence says, eyeing your {item_to_sell.name}.")
                return
            
            sell_price = self.current_area.get_fence_price(item_to_sell.value)
            self.inventory.remove(item_to_sell)
            self.money += sell_price
            item_to_sell.is_unpaid = False # Mark as "laundered"
            item_to_sell.unpaid_from_shop_id = None
            print(f"You offload the {item_to_sell.name} to the fence for ${sell_price:.2f}. Money: ${self.money:.2f}")
            self.reduce_suspicion_from_activity(2) # Successfully fencing might slightly lower suspicion
            return

        # Handle selling to a regular Shop
        if hasattr(self.current_area, 'shop_buys_stock'):
            if item_to_sell.is_unpaid:
                print(f"You try to sell the {item_to_sell.name}, but the cashier gives you a suspicious look. 'Is this... paid for?'")
                self.suspicion_rating += 15 # Trying to sell stolen goods to legit shop is very suspicious
                return

            shop_buy_details = self.current_area.shop_buys_stock.get(item_name_query.lower())
            if not shop_buy_details:
                print(f"This shop isn't buying '{item_name_query}' right now.")
                return
            if shop_buy_details['current_stock'] >= shop_buy_details['desired_stock']:
                print(f"The shop has enough '{item_name_query}' for now.")
                return

            sell_price = shop_buy_details['buy_price']
            self.inventory.remove(item_to_sell)
            self.money += sell_price
            shop_buy_details['current_stock'] += 1
            print(f"You sold {item_to_sell.name} for ${sell_price:.2f}. Remaining money: ${self.money:.2f}")
        else:
            print("This isn't a place where you can sell things.")

    def check_for_theft(self, shop_left):
        """Checks for unpaid items when leaving a shop and triggers Cast Member detection."""
        if not hasattr(shop_left, 'is_shop') or not shop_left.is_shop:
            return # Not a shop

        unpaid_items_from_this_shop = [
            item for item in self.inventory
            if item.is_unpaid and item.unpaid_from_shop_id == shop_left.id
        ]

        if not unpaid_items_from_this_shop:
            return # No stolen goods from this specific shop

        print(f"You attempt to leave {shop_left.name}...")
        self.suspicion_rating += 10 * len(unpaid_items_from_this_shop) # Higher suspicion for more items

        cast_members_in_shop = [npc for npc in shop_left.npcs if npc.__class__.__name__ == "CastMember"]
        
        if not cast_members_in_shop:
            print("Luckily, no Cast Members seem to be around. You slip out with the goods!")
            # Items remain is_unpaid, player got away with it from this shop
            return

        player_gx, player_gy = shop_left.get_relative_coordinates(self.coordinates) # Player's pos at exit point
        caught = False
        for cm in cast_members_in_shop:
            cm_gx, cm_gy = cm.get_grid_position()
            distance = ((player_gx - cm_gx)**2 + (player_gy - cm_gy)**2)**0.5
            
            # Detection chance: higher for closer, more alert CMs, and higher player suspicion
            # Base chance + alertness - distance penalty + suspicion bonus
            detection_chance = (0.1 + cm.alertness*0.2 - (distance*0.05) + self.suspicion_rating * 0.01) * (1 / len(cast_members_in_shop))
            detection_chance = max(0.05, min(0.95, detection_chance)) # Clamp chance

            if random.random() < detection_chance:
                print(f"{cm.name} notices you acting suspiciously with unpaid items!")
                print(f"'Hey! You haven't paid for those!' {cm.name} exclaims.")
                for item_to_confiscate in unpaid_items_from_this_shop:
                    self.inventory.remove(item_to_confiscate)
                    print(f"{item_to_confiscate.name} has been confiscated.")
                self.suspicion_rating += 20 # Getting caught increases suspicion a lot
                # Potentially add other penalties: fine, kicked out, etc.
                # For now, items are just lost.
                caught = True
                break # Caught by one is enough
        
        if not caught:
            print("Phew! You managed to leave without being noticed by the Cast Members.")
        # If not caught, items remain is_unpaid.