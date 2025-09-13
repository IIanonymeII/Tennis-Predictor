from dataclasses import asdict, dataclass
import logging
from typing import Dict, Optional

logger = logging.getLogger("[DATACLASS] [ODD]")

@dataclass
class HomeAwayOdds:
    """
    A dataclass representing odds for a home and away scenario.

    Attributes:
        bet_variant (str): The type of bet, e.g., "Match", "Set 1".
        bookmaker   (str): The name of the bookmaker, e.g., "Betclic", "Bwin".
        odd_start   (str): The starting odds 
        odd_end     (str): The ending odds
    """
    bet_variant: str # e.g., "Match", "Set 1" ...
    bookmaker  : str # e.g., "Betclic", "Bwin" ...
    odd_start  : str 
    odd_end    : str
  
@dataclass
class OverUnderOdds:
    """
    A dataclass representing over/under odds for a specific threshold.

    Attributes:
        bet_variant     (str): The type of bet, e.g., "Match", "Set 1".
        threshold_type  (str): The type of threshold, e.g., "Games" or "Set".
        threshold_value (str): The threshold value, e.g., "21.5".
        bookmaker       (str): The name of the bookmaker, e.g., "Betclic", "Bwin".
        odd_start       (str): The starting odds.
        odd_end         (str): The ending odds.
    """
    bet_variant    : str # e.g., "Match", "Set 1"  ...
    threshold_type : str # e.g., "Games" or "Set"  ...
    threshold_value: str # e.g., "21.5", "3.5"     ...
    bookmaker      : str # e.g., "Betclic", "Bwin" ...
    odd_start      : str
    odd_end        : str

@dataclass
class CorrectScoreOdds:
    """
    A dataclass representing odds for a correct score prediction.

    Attributes:
        score     (str): The predicted score, e.g., "2:0", "2:1".
        bookmaker (str): The name of the bookmaker, e.g., "Betclic", "Bwin".
        odd_start (str): The starting odds for the predicted score.
        odd_end   (str): The ending odds for the predicted score.
    """
    score    : str # e.g., "2:0", "2:1"     ...
    bookmaker: str # e.g., "Betclic", "Bwin"...
    odd_start: str
    odd_end  : str
