from dataclasses import asdict, dataclass
import logging
from typing import Dict, Optional

logger = logging.getLogger("[DATACLASS] [ODD]")

@dataclass
class HomeAwayOdds:
    """
    A dataclass representing odds for a home and away scenario.

    Attributes:
        bet_variant       (str): The type of bet, e.g., "Match", "Set 1".
        bookmaker         (str): The name of the bookmaker, e.g., "Betclic", "Bwin".
        odd_player1_start (str): The starting odds for player 1.
        odd_player1_end   (str): The ending odds for player 1.
        odd_player2_start (str): The starting odds for player 2.
        odd_player2_end   (str): The ending odds for player 2.
    """
    bet_variant: str
    bookmaker: str
    odd_player1_start: str
    odd_player1_end: str
    odd_player2_start: str
    odd_player2_end: str

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the HomeAwayOdds instance to a dictionary.

        Returns:
            Dict[str, str]: A dictionary representation of the odds.
        """
        logger.debug("Starting conversion of HomeAwayOdds to dictionary.")

        data: Dict[str, str] = {}

        # Define keys for the dictionary
        key1_start = f"{self.bookmaker} {self.bet_variant} start 1"
        key1_end = f"{self.bookmaker} {self.bet_variant} end 1"
        key2_start = f"{self.bookmaker} {self.bet_variant} start 2"
        key2_end = f"{self.bookmaker} {self.bet_variant} end 2"

        # Populate the dictionary with the odds values
        data[key1_start] = self.odd_player1_start
        data[key1_end] = self.odd_player1_end
        data[key2_start] = self.odd_player2_start
        data[key2_end] = self.odd_player2_end

        logger.info("Generated odds dictionary: %s", data)
        return data
  
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
    bet_variant: str
    threshold_type: str
    threshold_value: str
    bookmaker: str
    odd_start: str
    odd_end: str

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the OverUnderOdds instance to a dictionary.

        Returns:
            Dict[str, str]: A dictionary representation of the odds.
        """
        logger.debug("Starting conversion of OverUnderOdds to dictionary.")

        data: Dict[str, str] = {}

        # Define keys for the dictionary
        key_start = (f"{self.bookmaker} {self.bet_variant} "
                     f"{self.threshold_type} {self.threshold_value} start")
        key_end = (f"{self.bookmaker} {self.bet_variant} "
                   f"{self.threshold_type} {self.threshold_value} end")

        # Populate the dictionary with the odds values
        data[key_start] = self.odd_start
        data[key_end] = self.odd_end

        logger.info("Generated odds dictionary: %s", data)
        return data

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
    score: str
    bookmaker: str
    odd_start: str
    odd_end: str

    def to_dict(self) -> Dict[str, str]:
        """
        Convert the CorrectScoreOdds instance to a dictionary.

        Returns:
            Dict[str, str]: A dictionary representation of the odds.
        """
        logger.debug("Starting conversion of CorrectScoreOdds to dictionary.")

        data: Dict[str, str] = {}

        # Define keys for the dictionary
        key_start = f"{self.bookmaker} {self.score} start"
        key_end   = f"{self.bookmaker} {self.score} end"

        # Populate the dictionary with the odds values
        data[key_start] = self.odd_start
        data[key_end]   = self.odd_end

        logger.info("Generated odds dictionary: %s", data)
        return data