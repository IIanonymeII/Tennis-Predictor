"""
Player dataclass module.

This module defines a Player dataclass that represents a tennis player with detailed
information including personal details, physical attributes, and professional history.
"""

from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("[DATACLASS] [PLAYER]")


@dataclass
class Player:
    """
    Dataclass representing a tennis player with detailed information.

    This class stores comprehensive player information including personal details,
    physical attributes, and professional history such as height, birthday,
    professional career start year, and playing style.

    Parameters
    ----------
    id : str
        Unique identifier for the player
    name : str
        Player's full name
    birthday : Optional[date], optional
        Player's date of birth, by default None
    height : Optional[int], optional
        Player's height in centimeters, by default None
    turn_pro : Optional[int], optional
        Year the player turned professional, by default None
    hand : Optional[str], optional
        Dominant hand (e.g., 'Right' or 'Left'), by default None
    backhand : Optional[str], optional
        Backhand style ('two_handed' or 'one_handed'), by default None
    """

    id: str
    name: str
    birthday: Optional[date] = None
    height: Optional[int] = None  # in centimeters
    turn_pro: Optional[int] = None  # Year the player turned pro

    hand: Optional[str] = None  # Right  or Left
    backhand: Optional[str] = None  # two_handed or one_handed

    def __str__(self) -> str:
        """
        Return a formatted string representation of the player.

        Returns
        -------
        str
            Formatted string representation of the player with name, height, and birthday
        """
        birth_str = self.birthday.strftime("%Y-%m-%d") if self.birthday else "Unknown"
        return f"{self.name.center(20)} | Height: {self.height or 'N/A'} cm | Born: {birth_str}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Player instance to a dictionary.

        Uses dataclasses.asdict() to convert the dataclass instance
        into a dictionary representation and logs the serialization process.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the Player instance
        """
        player_dict = asdict(self)
        logger.debug(f"Serialized Player to dict: {player_dict}")
        return player_dict
