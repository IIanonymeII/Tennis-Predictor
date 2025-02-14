#!/usr/bin/env python3

from dataclasses import replace
import datetime
import logging
import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import pandas as pd
import requests

from prediction_tennis.src.dataset.flashscore.models.players import Player
from prediction_tennis.src.dataset.flashscore.models.tournaments import Tournaments
from prediction_tennis.src.dataset.flashscore.models.matchs import Match
from prediction_tennis.src.dataset.flashscore.utils.flashscore_client import retrieve_flashscore_data, validate_and_check_url
from prediction_tennis.src.dataset.flashscore.utils.text_extraction import extract_pattern_from_text


class FlashscoreMatchInTournamentParser:
    """
    Found for a Tournament-year all match on it
    """

    def __init__(self) -> None:
        """Initialize the parser state and set up logging."""
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [MATCHS IN TOURNAMENT]")
        
        # URL for the tournament page (to be set later)
        self.url_result: str = ""

        # Base URL for player information
        self.url_base_player = "https://www.flashscore.com/player/"

        self.url_base_odd = "https://2.flashscore.ninja/2/x/feed/df_od_1_"

        # List to store match information
        self.list_match: List[Match] = []

        # Mapping of tournament round names to internal representation
        self.round_mapping: Dict[str, str] = {
            "Final"            : "final",
            "Semi-finals"      : "semi_finals",
            "3rd place"        : "robin",
            "Quarter-finals"   : "quarter_finals",
            "1/8-finals"       : "round_of_8",
            "1/16-finals"      : "round_of_16",
            "1/32-finals"      : "round_of_32",
            "1/64-finals"      : "round_of_64",
            "Qualifying Finals": "qualif",
        }

    def initialize_variables(self, tournament : Tournaments) -> None:
        self.logger.info("___ INIT ___")

        # reset value
        self.list_match: List[Match] = []
        
        # Verify that match is an instance of the Match class
        if not isinstance(tournament, Tournaments):
            self.logger.error("Provided object is not an instance of the Tournaments class")
            raise ValueError("Provided object is not an instance of the Tournaments class")

        self.current_tournament: Tournaments = replace(tournament)

        # Construct the URL
        self.url_result = self.current_tournament.link_results
        self.logger.info(f"{self.current_tournament}")

    def extract_flashscore_results_data(self, response: requests.Response) -> str:
        """
        Extract the encoded results data string from the FlashScore webpage.

        Args:
            response (requests.Response): The HTTP response containing the webpage content.

        Returns:
            str: The encoded data string.

        Raises:
            ValueError: If the data is not found in the scripts.
        """
        self.logger.debug("Searching for script tags with encoded data")

        soup = BeautifulSoup(response.content, "html.parser")
        
        script_tags = soup.find_all('script', {'type': 'text/javascript'})
        pattern = re.compile(
            r"cjs\.initialFeeds\['results'\] = {[\s\S]*?data: `(.*?)`,", re.DOTALL
        )
        data_str: Optional[str] = None

        for script in script_tags:
            if script.string:
                match = pattern.search(script.string)
                if match:
                    self.logger.debug("found match for data_str")
                    data_str = match.group(1)
                    break

        if not data_str:
            self.logger.error("Data not found in scripts")
            raise ValueError("Data not found in scripts")
        
        self.logger.info("Encoded data string found")
        return data_str

    def _match_id(self, text: str) -> str:
        """
        Extract and return the match ID from the given text using a regex pattern.
        
        The match ID is identified by a pattern ending with "¬AD÷".

        Args:
            text (str): The input text containing the match ID.

        Returns:
            str: The extracted match ID.
        """
        self.logger.debug(f"Extracting 'MATCH ID' from text: {text}")

        # Define regex pattern to capture the 'MATCH ID'
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        match_id_pattern: str = r"([^¬÷]+)¬AD÷"
        match_id: str = extract_pattern_from_text(text=text, pattern=match_id_pattern)

        self.logger.info(f"Extracted 'MATCH ID': {match_id}")
        return match_id
    
    def _player_name(self, text: str) -> Tuple[str,str]:
        """
        Extract and return player 1 name and player 2 name from the given 
        text using a regex pattern.
        
        Args:
            text (str): The input text containing the player name 1 & 2.

        Returns:
            str: The extracted player name 1 & 2.
        """
        self.logger.debug(f"Extracting 'PLAYER NAME 1 & 2' from text: {text}")

        # Define regex pattern to capture the 'PLAYER NAME 1 & 2'
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        player_name_1_pattern: str = r"¬WU÷([^¬÷]+)¬AS÷" 
        player_name_2_pattern: str = r"¬WV÷([^¬÷]+)¬(?:AS|GRB)÷"

        player_name_1: str = extract_pattern_from_text(text=text, pattern=player_name_1_pattern)
        player_name_2: str = extract_pattern_from_text(text=text, pattern=player_name_2_pattern)

        self.logger.info(f"Extracted 'PLAYER NAME 1 & 2': ({player_name_1}, {player_name_2}) ")
        return (player_name_1, player_name_2)
     
    def _player_nationality(self, text: str) -> Tuple[str,str]:
        """
        Extract and return player 1 nationality and 
                           player 2 nationality 
        from the given text using a regex pattern.
        
        Args:
            text (str): The input text containing the player nationality 1 & 2.

        Returns:
            str: The extracted player nationality 1 & 2.
        """
        self.logger.debug(f"Extracting 'PLAYER NATIONALITY 1 & 2' from text: {text}")

        # Define regex pattern to capture the 'PLAYER NATIONALITY 1 & 2'
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        player_nationality_1_pattern: str = r"¬FU÷([^¬÷]+)¬CY÷"  
        player_nationality_2_pattern: str = r"¬FV÷([^¬÷]+)¬AH÷"

        player_nationality_1: str = extract_pattern_from_text(text=text, pattern=player_nationality_1_pattern)
        player_nationality_2: str = extract_pattern_from_text(text=text, pattern=player_nationality_2_pattern)

        self.logger.info(f"Extracted 'PLAYER NATIONALITY 1 & 2': ({player_nationality_1}, {player_nationality_2}) ")
        return (player_nationality_1, player_nationality_2)
    
    def _player_id(self, text: str) -> Tuple[str,str]:
        """
        Extract and return player 1 id and player 2 id from the given 
        text using a regex pattern.
        
        Args:
            text (str): The input text containing the player id 1 & 2.

        Returns:
            str: The extracted player id 1 & 2.
        """
        self.logger.debug(f"Extracting 'PLAYER ID 1 & 2' from text: {text}")

        # Define regex pattern to capture the 'PLAYER ID 1 & 2'        
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        player_id_1_pattern: str = r"¬PX÷([^¬÷]+)¬WU÷"  
        player_id_2_pattern: str = r"¬PY÷([^¬÷]+)¬WV÷"

        player_id_1: str = extract_pattern_from_text(text=text, pattern=player_id_1_pattern)
        player_id_2: str = extract_pattern_from_text(text=text, pattern=player_id_2_pattern)

        self.logger.info(f"Extracted 'PLAYER ID 1 & 2': ({player_id_1}, {player_id_2}) ")
        return (player_id_1, player_id_2)
   
    def _match_round(self, text: str) -> str:
        """
        Extract and return the standardized match round from the given text using a regex pattern.
        
        Args:
            text (str): The input text containing the match round.
        
        Returns:
            str: The standardized match round.
        
        Raises:
            ValueError: If the match round is not recognized.
        """
        self.logger.debug(f"Extracting 'MATCH ROUND' from text: {text}")

        # Define regex pattern to capture the 'MATCH ROUND'
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        match_round_pattern: str = r"¬ER÷([^¬÷]+)¬RW÷"
        extracted_round: str = extract_pattern_from_text(text, match_round_pattern)
        
        if extracted_round in self.round_mapping:
            standardized_round = self.round_mapping[extracted_round]
            self.logger.info(f"Extracted 'MATCH ROUND': {standardized_round}")
            return standardized_round
        
        # Raise error
        self.logger.error(f"Unknown match round: {extracted_round}")
        raise ValueError(f"Unknown match round: {extracted_round}")

    def _match_date(self, text: str) -> Tuple[str, str]:
        """
        Extract and return the match date from the given text using a regex pattern.

        This function extracts a timestamp from the input text, converts it into a 
        human-readable date-time string, and returns both the formatted date and its 
        original timestamp as a string.

        Args:
            text (str): The input text containing the match date information.

        Returns:
            Tuple[str, str]: A tuple where:
                - The first element is the formatted match date (YYYY-MM-DD HH:MM:SS).
                - The second element is the original match timestamp as a string.
        """
        self.logger.debug(f"Extracting 'MATCH DATE' from text: {text}")

        # Define regex pattern to capture the match date timestamp.
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        match_date_pattern: str = r"¬AD÷([^¬÷]+)¬ADE÷"
        match_timestamp: int = int(extract_pattern_from_text(text=text, pattern=match_date_pattern))

        # Convert the timestamp to a datetime object.
        match_datetime: datetime.datetime = datetime.datetime.fromtimestamp(match_timestamp)
        formatted_match_date: str = match_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        self.logger.info(f"Extracted 'MATCH DATE': {formatted_match_date} -> {match_timestamp}")
        return formatted_match_date, str(match_timestamp)
    
    def find_all_matches_in_tournament(self, tournament: Tournaments) -> List[Match]:
        """
        Extracts and processes all matches from a given tournament.

        Args:
            tournament (Tournaments): The tournament containing match data.

        Returns:
            List[Match]: A list of Match objects representing all extracted matches.
        """
        # Initialize match-specific variables
        self.initialize_variables(tournament=tournament)

        # Retrieve Flashscore data
        self.logger.info("Retrieving Flashscore data...")       
        response = retrieve_flashscore_data(url=self.url_result, return_as_text=False)
        response_text: str = self.extract_flashscore_results_data(response=response)

        # Split response text into individual match segments
        match_segments = response_text.split("~AA÷")[1:]
        self.logger.debug("Found %d match segments", len(match_segments))

        for segment in match_segments:
            self.logger.debug("Processing match segment: %s", segment)

            match_id: str = self._match_id(text=segment)
            player_name_1, player_name_2 = self._player_name(text=segment) # Tuple[str, str]
            player_nationality_1, player_nationality_2 = self._player_nationality(text=segment) # Tuple[str, str]
            player_id_1, player_id_2 = self._player_id(text=segment) # Tuple[str, str]
            formatted_match_date, match_timestamp = self._match_date(text=segment) # Tuple[str, str]
            match_round: str = self._match_round(text=segment)
            
            # Build player profile links
            player_link_1: str = validate_and_check_url(url=f"{self.url_base_player}{player_name_1}/{player_id_1}/")
            player_link_2: str = validate_and_check_url(url=f"{self.url_base_player}{player_name_2}/{player_id_2}/")

            # Builds odd url for this match
            match_link_odd: str = validate_and_check_url(url=f"{self.url_base_odd}{player_id_1}/")

            # Create Player objects
            player_1: Player = Player(
                id          = player_id_1,
                name        = player_name_1,
                nationality = player_nationality_1,
                link        = player_link_1,
                )
            
            player_2: Player = Player(
                id          = player_id_2,
                name        = player_name_2,
                nationality = player_nationality_2,
                link        = player_link_2,
                ) 
            
            # Create Match object
            _match: Match = Match(
                match_id             = match_id,
                formatted_match_date = formatted_match_date,
                match_timestamp      = match_timestamp,
                round                = match_round,
                player_1             = player_1,
                player_2             = player_2,
                link_odd             = match_link_odd,
                )
            
            self.list_match.append(_match)
            
        return self.list_match.copy()

        
if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    data = Tournaments(
        slug          = "golem",
        id            = "golem",
        name          = "acapulco-2001",
        year          = "2001",
        link          = "https://www.flashscore.com/tennis/atp-singles/acapulco-2001/",
        link_archives = "https://www.flashscore.com/tennis/atp-singles/acapulco/achives/",
        link_results  = "https://www.flashscore.com/tennis/atp-singles/acapulco-2001/results/",
        winner_name   = "golem",
        )

    parser = FlashscoreMatchInTournamentParser()
    list_match: List[Match] = parser.find_all_matches_in_tournament(tournament=data)

    print(" === Match === ")
    for _match in list_match:
        print(_match)
        print("\n")
    
