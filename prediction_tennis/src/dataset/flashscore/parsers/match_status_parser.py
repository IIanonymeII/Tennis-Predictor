from dataclasses import replace
import logging
from typing import Dict, Optional

from prediction_tennis.src.dataset.flashscore.models.matchs import Match
from prediction_tennis.src.dataset.flashscore.models.players import Player
from prediction_tennis.src.dataset.flashscore.utils.flashscore_client import retrieve_flashscore_data
from prediction_tennis.src.dataset.flashscore.utils.text_extraction import extract_pattern_from_text

class FlashscoreMatchStatusProcessor:
    """
    Processes match status data from Flashscore API responses.

    This class initializes match-related variables, extracts status and winner
    information from API response texts using regex patterns, and updates the
    match object accordingly.
    """
    def __init__(self):
        """
        Initialize the processor with logging and mapping configurations.
        """
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [MATCH][STATUS]")
        
        # Initialize variables for the current match and API URL.
        self.current_match: Match
        self.url_api: str

        # Mapping of status IDs to standardized status names.
        self.status_mapping: Dict[str, str] = {
            "1" : "SCHEDULED",
            "3" : "FINISH",
            "8" : "RETIRED",
            "9" : "WALKOVER",
            "54": "AWARDED",
        }

        # Mapping of winner identifiers to player numbers.
        self.winner_mapping: Dict[str, int] = {
            "H": 1,  # Home player (player 1)
            "A": 2,  # Away player (player 2)
        }

    def initialize_variables(self, match: Match) -> None:
        """
        Validate and initialize match-related variables.

        Args:
            match (Match): The match object to process.

        Raises:
            ValueError: If the provided object is not an instance of Match.
        """
        self.logger.info("___ INIT ___")

        # Verify that match is an instance of the Match class
        if not isinstance(match, Match):
            self.logger.error("Provided object is not an instance of the Match class")
            raise ValueError("Provided object is not an instance of the Match class")
        
        # Create a copy of the match object and store the API URL for the match status.
        self.current_match = replace(match)
        self.url_api = self.current_match.status_link

    def _status_name(self, text: str) -> str:
        """
        Extract the standardized status name from the provided text.

        Args:
            text (str): The response text containing match status data.

        Returns:
            str: The standardized status name.

        Raises:
            ValueError: If the extracted status ID is unknown.
        """
        self.logger.debug("Extracting status from text.")

        # Regex pattern to capture the status ID (ensuring no '¬' or '÷' is included in the captured group).
        status_id_pattern = r"¬DB÷([^¬÷]+)¬DD÷"
        status_id = extract_pattern_from_text(text=text, pattern=status_id_pattern)

        if status_id in self.status_mapping:
            standardized_status: str = self.status_mapping[status_id]
            self.logger.info(f"Extracted status name: {standardized_status}")
            return standardized_status

        self.logger.error(f"Unknown status ID: {status_id}")
        raise ValueError(f"Unknown status ID: {status_id}")
    
    def _winner(self, text: str) -> int:
        """
        Extract the winner information from the provided text.

        Args:
            text (str): The response text containing winner data.

        Returns:
            int: The player number of the winner. Returns -1 if no valid winner is found.
        """
        self.logger.debug("Extracting winner from text.")

        # Regex pattern to capture the winner identifier.
        winner_id_pattern = r"¬DJ÷([^¬÷]+)¬AZ÷"
        winner_id = extract_pattern_from_text(
            text=text, pattern=winner_id_pattern, optional_value=True
        )

        # Default winner value (-1) indicates no winner or an unknown winner.
        standardized_winner: int = -1
        if winner_id in self.winner_mapping:
            standardized_winner = self.winner_mapping[winner_id]

        self.logger.info(f"Extracted winner: {standardized_winner}")
        return standardized_winner
    
    def process_data(self, match: Match) -> Match:
        """
        Retrieve Flashscore data, extract status and winner information, and update the match object.

        Args:
            match (Match): The match object to process.

        Returns:
            Match: The updated match object with status and winner information.
        """
        # Initialize match variables.
        self.initialize_variables(match=match)

        self.logger.info("Retrieving Flashscore data...")
        response_text = retrieve_flashscore_data(url=self.url_api, return_as_text=True)

        status: str = self._status_name(text=response_text)
        winner: int = self._winner(text=response_text)

        # Update the match object with extracted status and winner.
        self.current_match.status = status
        self.current_match.winner = winner

        self.logger.debug(f"Match updated: Winner Player {winner} [{status}]")
        return self.current_match

if __name__ == "__main__":    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    # FINISH
    id = "Kx3ou23b"
    # RETIRED
    id = "C2238Yq4"
    # WALKAVER
    id= "OYu8QUV7"

    player1 = Player(id          = "golem",
                     name        = "golem",
                     nationality = "golem",
                     link        = "golem")
    player2 = replace(player1)

    data = Match(
        match_id   = f"{id}",
        odds_link  = "golem",
        stats_link = "golem",
        score_link = "golem",
        status_link= f"https://2.flashscore.ninja/2/x/feed/dc_1_{id}",
        match_date = "golem",
        timestamp  = "golem",
        round      = "golem",
        player1    = player1,
        player2    = player2,
        )

    parser = FlashscoreMatchStatusProcessor()
    current_match = parser.process_data(match=data)

    print(" === match === ")
    print(current_match)