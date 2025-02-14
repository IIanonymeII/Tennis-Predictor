

from dataclasses import asdict, dataclass, field
import logging
from typing import Dict, List

from prediction_tennis.src.dataset.flashscore.models.matchs import Match


logger = logging.getLogger("[DATACLASS] [TOURNAMENT]")

@dataclass
class TournamentsMinimaliste:
    """Minimal representation of a Tournament with essential attributes."""
    id           : str
    slug         : str
    link_archives: str

    def __post_init__(self):
        logger.debug(f"TournamentsMinimaliste created: ID={self.id}, Slug={self.slug}")

    def __str__(self):
        return f"[{self.slug}] => {self.link_archives}"
        
@dataclass
class Tournaments(TournamentsMinimaliste):
    """Full representation of a Tournament including matches and additional details."""
    name        : str
    year        : str
    link        : str
    link_results: str
    winner_name : str
    list_match  : List["Match"] = field(default_factory=list)  # Avoid mutable default argument

    def __post_init__(self):
        super().__post_init__()  # Call parent post-init if needed
        logger.info(f"Tournaments created: Name={self.name}, Year={self.year}, Matches={len(self.list_match)}")

    def __str__(self):
        return f"[{self.name.center(20)}] => {self.link_results}"

    # def to_dict(self) -> Dict[str, str]:
    #     """Convert to a dict"""
        
    #     logger.debug(f"Converting Tournaments Date instance to dictionary: {self}")
        
    #     return asdict(self)
