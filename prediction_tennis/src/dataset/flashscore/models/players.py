
from dataclasses import dataclass
import logging

logger = logging.getLogger("[DATACLASS] [PLAYER]")

@dataclass
class Player:
    id          : str
    name        : str
    nationality : str
    link        : str

    def __str__(self) -> str:
        return f"{self.name.center(20)} ({self.nationality.center(10)})"
