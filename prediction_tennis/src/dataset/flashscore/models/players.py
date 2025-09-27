"""
Player dataclass module.

This module defines a Player dataclass that represents a player with basic information
such as ID, name, nationality, and a link to additional information.
"""

from dataclasses import dataclass
import logging

logger = logging.getLogger("[DATACLASS] [PLAYER]")


@dataclass
class Player:
    """
    Dataclass representing a player with basic information.

    This class stores essential player information including unique identifier,
    name, nationality, and a link to additional player details.

    Parameters
    ----------
    id : str
        Unique identifier for the player
    name : str
        Player's full name
    nationality : str
        Player's nationality
    link : str
        URL or link to additional player information
    """

    id: str
    name: str
    nationality: str
    link: str

    def __str__(self) -> str:
        """
        Return a formatted string representation of the player.

        Returns
        -------
        str
            Formatted string representation of the player with centered name and nationality
        """
        return f"{self.name.center(20)} ({self.nationality.center(10)})"