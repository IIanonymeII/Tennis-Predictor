

from dataclasses import asdict, dataclass
import logging
from typing import Dict


logger = logging.getLogger("[DATACLASS] [TOURNAMENT]")

@dataclass
class Tournaments:
    """
    A dataclass representing a tournament with a slug (name) and an ID.

    Attributes:
        slug (str): The name of the tournament, e.g., 'belgrade-2', 'brussels'.
        id (str): The unique identifier of the tournament, e.g., 'vDAjRCsI'.
    """
    slug: str  # The name of the tournament
    id: str    # The unique identifier of the tournament

    def to_dict(self) -> Dict[str, str]:
        """Convert to a dict"""
        
        logger.debug(f"Converting Tournaments instance to dictionary: {self}")

        return asdict(self)
    
@dataclass
class TournamentsDate(Tournaments):
    tournament_name : str
    year            : str
    link            : str
    winner          : str

    def to_dict(self) -> Dict[str, str]:
        """Convert to a dict"""
        
        logger.debug(f"Converting Tournaments Date instance to dictionary: {self}")
        
        return asdict(self)
