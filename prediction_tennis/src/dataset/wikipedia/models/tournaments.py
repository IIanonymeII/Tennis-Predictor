

from dataclasses import asdict, dataclass, field
import logging
from typing import Dict, List

from prediction_tennis.src.dataset.flashscore.models.matchs import Match


logger = logging.getLogger("[DATACLASS] [TOURNAMENT]")
  
@dataclass
class Tournaments:
    name        : str
    year        : str
    type        : str
    money       : int
    surface     : str

    def __str__(self):
        return f"[{self.year}][{self.name.center(20)}]({self.surface} - {self.type}) => {self.money}"
    
    def to_dict(self):
        return asdict(self)