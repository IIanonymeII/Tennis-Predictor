#!/usr/bin/env python3

from dataclasses import replace
import datetime
import logging
import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
import pandas as pd
import requests

from prediction_tennis.src.dataset.flashscore.raw.models.players import Player
from prediction_tennis.src.dataset.flashscore.raw.models.tournaments import Tournaments
from prediction_tennis.src.dataset.flashscore.raw.models.matchs import Match
from prediction_tennis.src.dataset.flashscore.raw.utils.flashscore_client import retrieve_flashscore_data, validate_and_check_url
from prediction_tennis.src.dataset.flashscore.raw.utils.text_extraction import extract_pattern_from_text

PARTICULAR_CASE: List[str] = ["EV2zgEbq",
                              "6H7IaZrg",
                              "0v7Mbgba"]

class FlashscoreMatchInTournamentParser:
    """
    Found for a Tournament-year all match on it
    """

    def __init__(self) -> None:
        """Initialize the parser state and set up logging."""
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [MATCHS IN TOURNAMENT]")
        
        # URL for the tournament page (to be set later)
        self.url_result: str = ""

        # surface type for tournament (to be set later)
        self.surface_type: str = ""

        # Base URL for player information
        self.url_base_player = "https://www.flashscore.com/player/"

        self.url_base_odd    = "https://2.flashscore.ninja/2/x/feed/df_od_1_"
        self.url_base_stat   = "https://2.flashscore.ninja/2/x/feed/df_st_1_"
        self.url_base_score  = "https://2.flashscore.ninja/2/x/feed/df_sur_1_"
        self.url_base_status = "https://2.flashscore.ninja/2/x/feed/dc_1_"

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

        # valid surfaces 
        self.valid_surfaces = ["hard", "clay", "grass", "carpet"]

    def initialize_variables(self, tournament : Tournaments) -> None:
        self.logger.info("___ INIT ___")

        # reset value
        self.list_match: List[Match] = []
        self.surface_type: str = ""
        
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

    def _surface_type(self, text: str) -> str:
        """
        Extract the surface type from a tennis tournament string and validate it.

        This function searches for tournament details in the input text using a specific pattern.
        It then identifies the surface type by extracting the substring following the last occurrence of ', '.
        If the extracted surface (converted to lowercase) is one of the valid surfaces: ['hard', 'clay', 'grass', 'carpet'],
        it is returned. Otherwise, an error is logged and a ValueError is raised.

        Args:
            text (str): The input string containing tournament information.

        Returns:
            str: The validated surface type in lowercase.

        Raises:
            ValueError: If the tournament format is invalid or the surface type is not recognized.
        """
        # Step 1: Extract tournament part
        tournament_part_pattern: str = r"¬~ZA÷([^¬÷]+)¬ZEE÷"
        tournament_part: str = extract_pattern_from_text(text=text, pattern=tournament_part_pattern)

        # Step 2: Locate the last occurrence of ', ' to find the surface type.
        last_comma_index: int = tournament_part.rfind(", ")
        if last_comma_index == -1:
            self.logger.error("Comma delimiter not found in tournament part: '%s'", tournament_part)
            raise ValueError("Invalid tournament format: missing comma delimiter for surface extraction.")

        # Extract the surface type by taking the substring after the last comma and stripping whitespace.
        surface: str = tournament_part[last_comma_index + 2:].strip()

        # Step 3: Convert the surface to lowercase and verify it against valid surfaces.
        surface_lower: str = surface.lower()
        if surface_lower in self.valid_surfaces:
            return surface_lower

        self.logger.error("Extracted surface '%s' is not valid. Expected one of: %s", surface_lower, self.valid_surfaces)
        raise ValueError(f"Invalid surface type: {surface_lower}")

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
        player_name_1_pattern: str = r"¬WU÷([^¬÷]+)¬(?:AS|GRA|AZ)÷" 
        player_name_2_pattern: str = r"¬WV÷([^¬÷]+)¬(?:AS|GRB|AZ)÷"

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
        player_nationality_2_pattern: str = r"¬FV÷([^¬÷]+)¬(?:AH|OB|WB|BB)÷"

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
        extracted_round: str = extract_pattern_from_text(text, match_round_pattern, optional_value=True)
        
        if extracted_round in self.round_mapping:
            standardized_round = self.round_mapping[extracted_round]
            self.logger.info(f"Extracted 'MATCH ROUND': {standardized_round}")
            return standardized_round
        return "NOT Play Off"
        # # Raise error
        # self.logger.error(f"Unknown match round: {extracted_round}")
        # raise ValueError(f"Unknown match round: {extracted_round}")

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
        match_segments = response_text.split("~AA÷")
        surface_info, match_segments = match_segments[0], match_segments[1:]
        self.logger.debug("Found %d match segments", len(match_segments))

        self.surface_type = self._surface_type(text=surface_info)

        for segment in match_segments:
            self.logger.debug("Processing match segment: %s", segment)

            match_id: str = self._match_id(text=segment)
            if match_id in PARTICULAR_CASE:
                # Particular case do not implement
                continue

            player_name_1, player_name_2 = self._player_name(text=segment) # Tuple[str, str]
            player_nationality_1, player_nationality_2 = self._player_nationality(text=segment) # Tuple[str, str]
            player_id_1, player_id_2 = self._player_id(text=segment) # Tuple[str, str]
            formatted_match_date, match_timestamp = self._match_date(text=segment) # Tuple[str, str]
            match_round: str = self._match_round(text=segment)
            
            # Build player profile links
            player_link_1: str = validate_and_check_url(url=f"{self.url_base_player}{player_name_1}/{player_id_1}/")
            player_link_2: str = validate_and_check_url(url=f"{self.url_base_player}{player_name_2}/{player_id_2}/")

            # Builds odd, stat and score url for this match
            match_link_odd   : str = validate_and_check_url(url=f"{self.url_base_odd}{match_id}/")
            match_link_stat  : str = validate_and_check_url(url=f"{self.url_base_stat}{match_id}/")
            match_link_score : str = validate_and_check_url(url=f"{self.url_base_score}{match_id}/")
            match_link_status: str = validate_and_check_url(url=f"{self.url_base_status}{match_id}/")

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
                match_id    = match_id,
                match_date  = formatted_match_date,
                timestamp   = match_timestamp,
                round       = match_round,
                player1     = player_1,
                player2     = player_2,
                odds_link   = match_link_odd,
                stats_link  = match_link_stat,
                score_link  = match_link_score,
                status_link = match_link_status,
                surface_type= self.surface_type,
                )
            
            self.list_match.append(_match)
            
        return self.list_match.copy()

        
if __name__ == "__main__":

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # # NORMAL
    # tournament = "acapulco"
    # year = "2025"
    # PARTICULAR CASE
    tournament = "adelaide"
    year = "2007"

    # Grass
    tournament= "wimbledon"
    year = "2016"

    data = Tournaments(
        slug          = "golem",
        id            = "golem",
        name          = f"{tournament}-{year}",
        year          = f"{year}",
        link          = f"https://www.flashscore.com/tennis/atp-singles/{tournament}-{year}/",
        link_archives = f"https://www.flashscore.com/tennis/atp-singles/{tournament}/achives/",
        link_results  = f"https://www.flashscore.com/tennis/atp-singles/{tournament}-{year}/results/",
        winner_name   = "golem",
        )

    parser = FlashscoreMatchInTournamentParser()
    list_match: List[Match] = parser.find_all_matches_in_tournament(tournament=data)

    print(" === Match === ")
    for _match in list_match:
        print(_match)
        print("\n")
    # ERROR :https://www.flashscore.com/tennis/atp-singles/adelaide/#/GScbsICl/draw
    ["Hard", "Clay", "Grass", "Carpet"]
