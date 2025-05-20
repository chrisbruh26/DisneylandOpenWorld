"""
Item module for the Disneyland Adventure game.
Handles all items that can be picked up, used, or interacted with.
"""
import random

class Item:
    """Base class for all items in the game."""
    def __init__(self, name, description, value=0, pickupable=True, sell_value_modifier=0.5):
        self.name = name
        self.description = description
        self.value = value  # Cost to buy from a shop
        # Price shop pays player for this item. Can be a fixed value or calculated.
        self.buy_back_price = round(value * sell_value_modifier)
        self.pickupable = pickupable
        self.id = f"item_{name.lower().replace(' ', '_')}_{random.randint(1000,9999)}"
        self.coordinates = None # Global coordinates if in an area, None if in inventory
        self.is_unpaid = False # True if taken from a shop without paying
        self.unpaid_from_shop_id = None # ID of the shop it was taken from

    def __str__(self):
        return self.name

    def clone(self):
        """Creates a new instance of this item (a copy)."""
        return Item(
            name=self.name,
            description=self.description,
            value=self.value,
            pickupable=self.pickupable,
            # The sell_value_modifier for the prototype is used to calculate its buy_back_price
            # When cloning, we just copy the calculated buy_back_price directly.
            # The sell_value_modifier argument in __init__ is for prototype creation.
            # We can reconstruct it if needed, or just ensure buy_back_price is set.
        )

    def to_dict(self):
        """Convert item to dictionary for serialization (future use)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "buy_back_price": self.buy_back_price,
            "pickupable": self.pickupable,
            "coordinates": self.coordinates.to_dict() if self.coordinates else None,
            "is_unpaid": self.is_unpaid,
            "unpaid_from_shop_id": self.unpaid_from_shop_id,
        }

    @classmethod
    def from_dict(cls, data, coordinates_module): # Pass the module for Coordinates class
        """Create item from dictionary (future use)."""
        coords = coordinates_module.Coordinates.from_dict(data["coordinates"]) if data["coordinates"] else None
        item = cls(data["name"], data["description"], value=data.get("value",0), pickupable=data.get("pickupable", True))
        item.buy_back_price = data.get("buy_back_price", round(item.value * 0.5))
        item.coordinates = coords
        item.id = data.get("id", item.id) # Keep original ID if present
        item.is_unpaid = data.get("is_unpaid", False)
        item.unpaid_from_shop_id = data.get("unpaid_from_shop_id", None)
        return item

class ItemManager:
    """Manages all item prototypes and instances in the game."""
    def __init__(self):
        self.item_prototypes = {} # name.lower() -> Item (prototype)
        self.world_items = {} # item_id -> Item (instance in the world or inventory)

    def add_prototype(self, item_prototype):
        self.item_prototypes[item_prototype.name.lower()] = item_prototype

    def create_instance(self, item_name):
        prototype = self.item_prototypes.get(item_name.lower())
        if prototype:
            new_item = prototype.clone()
            self.world_items[new_item.id] = new_item
            return new_item
        return None