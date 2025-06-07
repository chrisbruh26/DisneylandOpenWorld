"""
Coordinates module for the Disneyland Adventure game.
Handles position and location in the 3D game world.
"""

class Coordinates:
    """Represents a position in the 3D game world."""
    def __init__(self, x=0, y=0, z=0):
        self.x = x  # East-West position
        self.y = y  # North-South position
        self.z = z  # Height/Elevation
    
    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"
    
    def distance_to(self, other_coords):
        """Calculate horizontal distance to another coordinate."""
        return ((self.x - other_coords.x) ** 2 + (self.y - other_coords.y) ** 2) ** 0.5
    
    def height_difference(self, other_coords):
        """Calculate vertical distance to another coordinate."""
        return abs(self.z - other_coords.z)
    
    def to_dict(self):
        """Convert coordinates to dictionary for serialization."""
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create coordinates from dictionary."""
        return cls(data["x"], data["y"], data.get("z", 0))