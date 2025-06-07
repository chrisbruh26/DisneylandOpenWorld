"""
NPC module for the Disneyland Adventure game.
Handles Non-Player Characters.
"""
import random
from .coordinates import Coordinates

class NPC:
    """NPC class representing non-player characters."""
    def __init__(self, name, description, start_coords=None, area=None):
        self.name = name
        self.description = description
        self.coordinates = start_coords if start_coords else Coordinates(0,0) # Global coordinates
        self.location = area # Current Area object
        self.id = f"npc_{name.lower().replace(' ', '_')}_{random.randint(1000,9999)}"
        self.action_cooldown = 0

    def set_location(self, area, grid_x=None, grid_y=None):
        """Places the NPC in an area and on its grid."""
        if self.location and self.location != area:
            old_gx, old_gy = self.location.get_relative_coordinates(self.coordinates)[:2]
            self.location.remove_object_from_grid(self, int(old_gx), int(old_gy))

        self.location = area
        if area:
            if grid_x is None: grid_x = area.grid_width // 2
            if grid_y is None: grid_y = area.grid_length // 2
            
            grid_x = max(0, min(grid_x, area.grid_width - 1))
            grid_y = max(0, min(grid_y, area.grid_length - 1))
            
            area.add_object_to_grid(self, grid_x, grid_y) # Also updates self.coordinates
        else:
            self.coordinates = Coordinates(-1,-1) # Off-map

    def get_grid_position(self):
        if not self.location: return None, None
        rel_coords = self.location.get_relative_coordinates(self.coordinates)
        return int(rel_coords[0]), int(rel_coords[1])

    def move_on_grid(self, dx, dy):
        if not self.location: return False, None

        current_gx, current_gy = self.get_grid_position()
        new_gx, new_gy = current_gx + dx, current_gy + dy

        if self.location.is_valid_grid_position(new_gx, new_gy):
            self.location.remove_object_from_grid(self, current_gx, current_gy)
            self.location.add_object_to_grid(self, new_gx, new_gy)
            return True, f"{self.name} moves."
        return False, None

    def update(self, game_turn, player=None):
        """
        Called each game turn for NPC actions. Very simple autonomy for now.
        If player is provided, only generate messages if NPC is close to player.
        """
        action_message = None
        if self.action_cooldown > 0:
            self.action_cooldown -= 1
            return None # No message if on cooldown

        # Only move within the current area, don't jump between areas
        if self.location and random.random() < 0.3: # 30% chance to try to move
            dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (0,0)])
            if dx != 0 or dy != 0: # Don't report standing still as an action
                moved, msg_part = self.move_on_grid(dx, dy)
                if moved:
                    # Only generate a message if the player is in the same area and close enough
                    if player and player.current_area == self.location:
                        # Calculate distance to player
                        player_distance = self.coordinates.distance_to(player.coordinates)
                        # Only show messages for NPCs within a reasonable distance (e.g., 10 units)
                        if player_distance <= 10:
                            action_message = msg_part # e.g., "Mickey Mouse moves."
            self.action_cooldown = random.randint(2, 5) # Wait a bit before next action
        
        return action_message


class ParkCharacter(NPC):
    """Represents iconic Disney characters like Mickey, Goofy, etc."""
    def __init__(self, name, description, start_coords=None, area=None, signature_move="waves cheerfully"):
        super().__init__(name, description, start_coords, area)
        self.id = f"char_{name.lower().replace(' ', '_').replace('.', '')}_{random.randint(1000,9999)}"
        self.signature_move = signature_move

    def update(self, game_turn, player=None):
        """Characters might have simpler or more scripted behaviors."""
        action_message = super().update(game_turn, player) # Basic movement
        if not action_message and self.action_cooldown == 0 and random.random() < 0.2:
            # Only show signature move if player is in the same area and close enough
            if player and player.current_area == self.location:
                player_distance = self.coordinates.distance_to(player.coordinates)
                if player_distance <= 10:
                    action_message = f"{self.name} {self.signature_move}."
                    self.action_cooldown = random.randint(3, 6)
            else:
                # Still set cooldown even if we don't show the message
                self.action_cooldown = random.randint(3, 6)
        return action_message


class Guest(NPC):
    """Guest class representing NPCs that are Disneyland visitors."""
    def __init__(self, name, description, start_coords=None, area=None):
        # Ensure Guest names are somewhat unique for targeting if needed later
        super().__init__(f"Guest {name}", description, start_coords, area)
        self.id = f"guest_{name.lower().replace(' ', '_')}_{random.randint(1000,9999)}"
        # Guests might have a "suspicion_level" if player tries to plant items on them
        self.suspicion_level = 0
        self.has_been_checked = False # Flag for distraction mechanic

    def update(self, game_turn, player=None):
        """Guests primarily wander, maybe react to nearby events later."""
        # For now, they behave like standard NPCs
        return super().update(game_turn, player)


class CastMember(NPC):
    """Cast Member class representing Disneyland employees."""
    def __init__(self, name, description, start_coords=None, area=None, role="General"):
        super().__init__(f"CM {name}", description, start_coords, area) # Prefix with CM for clarity
        self.id = f"cast_{name.lower().replace(' ', '_')}_{random.randint(1000,9999)}"
        self.role = role # e.g., "Security", "Cashier", "Greeter"
        self.alertness = random.uniform(0.5, 1.0) # How observant they are

    def update(self, game_turn, player=None):
        """Cast members might patrol or stay at posts. For now, standard NPC movement."""
        # Later, their update can include scanning for suspicious activity.
        return super().update(game_turn, player)

class ShadyCharacter(NPC):
    """Represents a character who deals in illicit goods."""
    def __init__(self, name, description, start_coords=None, area=None, greeting="Psst... got something for me?"):
        super().__init__(name, description, start_coords, area)
        self.id = f"shady_{name.lower().replace(' ', '_').replace('.', '')}_{random.randint(1000,9999)}"
        self.greeting = greeting

    def update(self, game_turn, player=None):
        """Shady characters mostly stay put, maybe offer a hint if player is nearby."""
        # Only generate a message if the player is in the same area and close enough
        if player and player.current_area == self.location:
            player_distance = self.coordinates.distance_to(player.coordinates)
            if player_distance <= 5 and random.random() < 0.2:  # Closer proximity threshold and occasional hint
                return f"{self.name} whispers: '{self.greeting}'"
        
        # They don't wander like other NPCs unless explicitly told to
        return None

class NPCManager:
    def __init__(self):
        self.npcs = {} # npc_id -> NPC_object

    def add_npc(self, npc):
        self.npcs[npc.id] = npc

    def get_npc(self, npc_id_or_name):
        if npc_id_or_name in self.npcs: return self.npcs[npc_id_or_name]
        for npc in self.npcs.values():
            if npc.name.lower() == npc_id_or_name.lower(): return npc
        return None

    def update_all_npcs(self, game_turn, player=None):
        """
        Update all NPCs and collect their action messages.
        If player is provided, only show messages for NPCs close to the player.
        """
        messages = []
        for npc_id, npc_obj in self.npcs.items():
            message = npc_obj.update(game_turn, player)
            if message:
                messages.append(message)
        return messages