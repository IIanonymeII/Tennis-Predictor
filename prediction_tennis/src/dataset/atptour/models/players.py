from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger("[DATACLASS] [PLAYER]")


@dataclass
class Player:
    id: str
    name: str
    birthday: Optional[date] = None
    height  : Optional[int]  = None  # in centimeters
    turn_pro: Optional[int]  = None  # Year the player turned pro

    hand    : Optional[str]  = None    # Right  or Left
    backhand: Optional[str]  = None # two_handed or one_handed

    def __str__(self) -> str:
        birth_str = self.birthday.strftime('%Y-%m-%d') if self.birthday else "Unknown"
        return f"{self.name.center(20)} | Height: {self.height or 'N/A'} cm | Born: {birth_str}"

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Player object to a dictionary."""
        player_dict = asdict(self)
        logger.debug(f"Serialized Player to dict: {player_dict}")
        return player_dict
