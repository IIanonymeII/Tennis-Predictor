  
from dataclasses import asdict, replace
import logging
import re
from typing import Any, Dict, List
import pandas as pd

from prediction_tennis.src.dataset.flashscore.raw.models.matchs import Match
from prediction_tennis.src.dataset.flashscore.raw.models.odds import CorrectScoreOdds, HomeAwayOdds, OverUnderOdds
from prediction_tennis.src.dataset.flashscore.raw.models.players import Player
from prediction_tennis.src.dataset.flashscore.raw.utils.flashscore_client import retrieve_flashscore_data
from prediction_tennis.src.dataset.flashscore.raw.utils.text_extraction import extract_odds, extract_pattern_from_text



class FlashscoreOddsParser:
    """
    Parser utilisant une machine à états pour traiter les segments du flux.
    """
    def __init__(self) -> None:
        """Initialize the parser state and set up logging."""
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [ODDS]")

        # Mapping of bookmaker IDs to their respective names
        self.bookmaker_mapping = {
            "160": "Unibet",
            "129": "Bwin",
            "398": "Netbet",
            "141": "Betclic",
            "484": "Parions-Sport",
            "264": "Winamax",
            }

        # URL for the tournament page (to be set later)
        self.url_api : str = ""

        # The current match being processed
        self.current_match: Match

        # Lists to store odds data for different bet types
        self.home_away_odds     : List[HomeAwayOdds]     = []
        self.over_odds          : List[OverUnderOdds]    = []
        self.under_odds         : List[OverUnderOdds]    = []
        self.correct_score_odds : List[CorrectScoreOdds] = []

    def initialize_variables(self, match: Match) -> None:
        """
        Initializes variables related to the match odds and stores the current match details.

        Args:
            match (Match): The match object containing the match data.

        This method resets the odds lists, verifies the match data, and logs relevant information.
        """
        self.logger.info("___ INIT ___")

        # Verify that match is an instance of the Match class
        if not isinstance(match, Match):
            self.logger.error("Provided object is not an instance of the Match class")
            raise ValueError("Provided object is not an instance of the Match class")

        # Store the current match and the API URL
        self.current_match : Match = replace(match)
        self.url_api: str = self.current_match.odds_link

        # Log match ID and API URL for debugging purposes
        self.logger.info(f"[{self.current_match.match_id}] : {self.url_api}")

    def _bet_type(self, text: str) -> str:
        """
        Extracts the type of bet from the text.
        ex: "home-away", "over-under", "correct-score", etc.

        Args:
            text (str): The input text containing bet information.

        Returns:
            str: The extracted bet type.
        """
        self.logger.debug("Extracting bet type from text: %s", text)

        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        bet_type_pattern = r"¬OAU÷([^¬÷]+)¬OAI÷"
        bet_type = extract_pattern_from_text(text=text, pattern=bet_type_pattern)

        self.logger.info("Bet type extracted: %s", bet_type)

        return bet_type

    def _bet_variant(self, text: str) -> str:
        """
        Extracts the bet variant from the sub-category text.
        ex : "Full match", "Set 1", "Set 2", etc.

        Args:
            sub_category (str): The input text containing sub-category information.

        Returns:
            str: The extracted bet variant.
        """
        self.logger.debug("Extracting bet variant from sub-category: %s", text)
        
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        bet_variant_pattern = r"([^¬÷]+)¬OBU÷"
        bet_variant = extract_pattern_from_text(text=text, pattern=bet_variant_pattern)
        
        self.logger.info("Bet variant extracted: %s", bet_variant)
        
        return bet_variant
    
    def _threshold_type(self, text: str) -> str:
        """
        Extracts the threshold type from the given text. The threshold type can be either "Games" or "Sets".

        Args:
            text (str): The input text from which to extract the threshold type.

        Returns:
            str: The extracted threshold type.
        """
        self.logger.debug("Extracting threshold type from text: %s", text)
        
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        threshold_type_pattern = r"([^¬÷]+)¬OC÷"
        threshold_type = extract_pattern_from_text(text=text, pattern=threshold_type_pattern)

        self.logger.info("threshold type extracted: %s", threshold_type)

        return threshold_type
    
    def _threshold_value(self, text: str) -> str:
        """
        Extracts the threshold value from the given text. The threshold value can be a score or a set number.

        Args:
            text (str): The input text from which to extract the threshold value.

        Returns:
            str: The extracted threshold value.
        """
        self.logger.debug("Extracting threshold value from text: %s", text)

        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        threshold_value_pattern = r"¬OC÷([^¬÷]+)(?:¬LY÷|¬LZ÷)"
        threshold_value = extract_pattern_from_text(text=text, pattern=threshold_value_pattern)

        self.logger.info("threshold value extracted: %s", threshold_value)

        return threshold_value

    def _bookmaker_name(self, text: str) -> str:
        """
        Extracts the bookmaker name from the given text.

        Args:
            text (str): The input text containing the bookmaker ID.

        Returns:
            str: The name of the bookmaker corresponding to the extracted ID.
        """
        self.logger.debug(f"Extracting 'BOOKMAKER ID' from sub-category: {text}")

        # Extract the bookmaker ID from the text using the defined pattern
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        bookmaker_id_pattern = r"([^¬÷]+)¬OD÷"
        bookmaker_id = extract_pattern_from_text(text=text, pattern=bookmaker_id_pattern)

        if bookmaker_id in self.bookmaker_mapping:
            standardized_bookmaker: str = self.bookmaker_mapping[bookmaker_id]
            self.logger.info(f"Extracted 'BOOKMAKER NAME': {standardized_bookmaker}")
            return standardized_bookmaker

        # Raise error
        self.logger.error(f"Unknown Bookmaker ID: {bookmaker_id}")
        raise ValueError(f"Unknown Bookmaker ID: {bookmaker_id}")
    
    def _bookmaker_web_name(self, text: str) -> str:
        """
        Extracts the bookmaker's web name from the given text.

        Args:
            text (str): The input text from which to extract the bookmaker's web name.

        Returns:
            str: The extracted bookmaker's web name.
        """
        self.logger.debug("Extracting bookmaker web name from sub-category: %s", text)

        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        bookmaker_web_name_pattern = r"¬OD÷([^¬÷]+)¬OPI÷"
        bookmaker_web_name = extract_pattern_from_text(text=text, pattern=bookmaker_web_name_pattern)

        self.logger.info("Bookmaker web name extracted: %s", bookmaker_web_name)

        return bookmaker_web_name
    
    def _bookmaker_odd_player(self, text: str) -> List[str]:
        """
        Extracts the bookmaker's odds for two players from the given text.

        Args:
            text (str): The input text from which to extract the bookmaker's odds.

        Returns:
            List[str]: A list containing the extracted odds for two players.
        """
        self.logger.debug("Extracting bookmaker odd from sub-category: %s", text)
        
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        bookmaker_odd_1_pattern    = r"¬XB÷([^¬÷]+)¬XC÷"
        bookmaker_odd_2_pattern    = r"¬XC÷([^¬÷]+)¬OG÷"

        bookmaker_odd_1 = extract_pattern_from_text(text=text, pattern=bookmaker_odd_1_pattern)
        bookmaker_odd_2 = extract_pattern_from_text(text=text, pattern=bookmaker_odd_2_pattern)

        self.logger.debug("[BEFORE DIV] Bookmaker odd 1 extracted: %s", bookmaker_odd_1)
        self.logger.debug("[BEFORE DIV] Bookmaker odd 2 extracted: %s", bookmaker_odd_2)

        begin_odd_1, end_odd_1 = extract_odds(odd_str=bookmaker_odd_1)
        begin_odd_2, end_odd_2 = extract_odds(odd_str=bookmaker_odd_2)

        self.logger.debug("[AFTER DIV] Bookmaker odd 1 extracted: %s -> %s", begin_odd_1, end_odd_1)
        self.logger.debug("[AFTER DIV] Bookmaker odd 2 extracted: %s -> %s", begin_odd_2, end_odd_2)

        return (begin_odd_1, end_odd_1), (begin_odd_2, end_odd_2)
      
    def _bookmaker_odd(self, text: str) -> List[str]:
        """
        Extracts the bookmaker's odd from the given text.

        Args:
            text (str): The input text from which to extract the bookmaker's odd.

        Returns:
            List[str]: A list containing the extracted odd.
        """
        self.logger.debug("Extracting boolmake odd from sub-category: %s", text)
        
        # Extract the pattern from the text
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        bookmaker_odd_pattern = r"¬XC÷([^¬÷]+)¬OG÷"
        bookmaker_odd = extract_pattern_from_text(text=text, pattern=bookmaker_odd_pattern)
        
        self.logger.debug("[BEFORE DIV] Bookmaker odd extracted: %s", bookmaker_odd)
        
        # Divide the odd into beginning and end parts
        begin_odd, end_odd = extract_odds(odd_str=bookmaker_odd)
        
        self.logger.debug("[AFTER DIV] Bookmaker odd extracted: %s -> %s", begin_odd, end_odd)
        
        return (begin_odd, end_odd)

    def process_home_away(self, sub_category: str, bet_variant: str) -> None:
        """
        Processes the home-away bet data and logs the extracted information.

        Args:
            sub_category (str): The sub-category string containing bookmaker data.
            bet_variant  (str): The type of bet being processed.
        """
        # Split the sub-category string to extract individual bookmaker data segments
        sub_bookmakers: list[str] = sub_category.split("~OE÷")[1:]

        for sub_bookmaker in sub_bookmakers:
            try:
                # Extract bookmaker name and web name
                bookmaker_name    : str = self._bookmaker_name(text=sub_bookmaker)
                bookmaker_web_name: str = self._bookmaker_web_name(text=sub_bookmaker)

                # Extract odds for both players
                (begin_odd_1, end_odd_1), (begin_odd_2, end_odd_2) = self._bookmaker_odd_player(text=sub_bookmaker)

                self.logger.info(f"[{bet_variant}] [{bookmaker_web_name} ({bookmaker_name})] [1]: {begin_odd_1} -> {end_odd_1}")
                self.logger.info(f"[{bet_variant}] [{bookmaker_web_name} ({bookmaker_name})] [2]: {begin_odd_2} -> {end_odd_2}")

                # Create HomeAwayOdds objects for each player and append them to the corresponding lists.
                home_away_odd_player1 = HomeAwayOdds(
                                            bet_variant = bet_variant,
                                            bookmaker   = bookmaker_name,
                                            odd_start   = begin_odd_1,
                                            odd_end     = end_odd_1
                                            )
                
                home_away_odd_player2 = HomeAwayOdds(
                                            bet_variant = bet_variant,
                                            bookmaker   = bookmaker_name,
                                            odd_start   = begin_odd_2,
                                            odd_end     = end_odd_2
                                            )
                # Save (append) in Current match
                self.current_match.append_home_away(player_1 = home_away_odd_player1,
                                                    player_2 = home_away_odd_player2)

            except Exception as e:
                self.logger.error(f"Error processing home-away bet data for sub-category: {sub_category}, error: {e}")
        
    def process_over_under(self, sub_category: str, bet_variant: str) -> None:
        """
        Processes the over-under bet data and logs the extracted information.

        Args:
            sub_category (str): The sub-category string containing bookmaker data.
            bet_variant  (str): The type of bet being processed.
        """
        # Split the sub-category string to extract individual over-under data segments
        sub_type_over_under_list = sub_category.split("~OCT÷")[1:]

        for sub_type_over_under in sub_type_over_under_list:
            try:
                # Extract threshold type and value
                threshold_type  = self._threshold_type(text=sub_type_over_under)
                threshold_value = self._threshold_value(text=sub_type_over_under)

                # Split the over-under data segment to extract individual bookmaker data segments
                sub_bookmakers = sub_type_over_under.split("~OE÷")[1:]

                for sub_bookmaker in sub_bookmakers:
                    # Extract bookmaker name and web name
                    bookmaker_name = self._bookmaker_name(text=sub_bookmaker)
                    bookmaker_web_name = self._bookmaker_web_name(text=sub_bookmaker)

                    # Extract odds for over and under
                    (begin_odd_over, end_odd_over), (begin_odd_under, end_odd_under) = self._bookmaker_odd_player(text=sub_bookmaker)

                    self.logger.info(f"[{bet_variant}] [{bookmaker_web_name} ({bookmaker_name})] [{threshold_type} - {threshold_value}] [Over]: {begin_odd_over} -> {end_odd_over}")
                    self.logger.info(f"[{bet_variant}] [{bookmaker_web_name} ({bookmaker_name})] [{threshold_type} - {threshold_value}] [Under]: {begin_odd_under} -> {end_odd_under}")

                    # Create OverUnderOdds objects and append them
                    over_odd = OverUnderOdds(
                                bet_variant     = bet_variant,
                                threshold_type  = threshold_type,
                                threshold_value = threshold_value,
                                bookmaker       = bookmaker_name,
                                odd_start       = begin_odd_over,
                                odd_end         = end_odd_over
                                )

                    under_odd = OverUnderOdds(
                                bet_variant     = bet_variant,
                                threshold_type  = threshold_type,
                                threshold_value = threshold_value,
                                bookmaker       = bookmaker_name,
                                odd_start       = begin_odd_under,
                                odd_end         = end_odd_under
                                )
                    # Save (append) in Current match
                    self.current_match.append_over_under(over=over_odd,
                                                         under=under_odd)

            except Exception as e:
                self.logger.error(f"Error processing over-under bet data for sub-category: {sub_category}, error: {e}")

    def process_correct_score(self, sub_category: str, bet_variant: str) -> None:
        """
        Processes the correct score bet data and logs the extracted information.

        Args:
            sub_category (str): The sub-category string containing bookmaker data.
            bet_variant (str): The type of bet being processed.
        """
        # Split the sub-category string to extract individual correct score data segments
        sub_type_over_under_list = sub_category.split("~OCT÷")[1:]

        for sub_type_over_under in sub_type_over_under_list:
            try:
                # Extract threshold value
                threshold_value = self._threshold_value(text=sub_type_over_under)

                # Split the correct score data segment to extract individual bookmaker data segments
                sub_bookmakers = sub_type_over_under.split("~OE÷")[1:]

                for sub_bookmaker in sub_bookmakers:
                    # Extract bookmaker name and web name
                    bookmaker_name = self._bookmaker_name(text=sub_bookmaker)
                    bookmaker_web_name = self._bookmaker_web_name(text=sub_bookmaker)

                    # Extract odds
                    begin_odd, end_odd = self._bookmaker_odd(text=sub_bookmaker)

                    self.logger.info(f"[{bet_variant}] [{bookmaker_web_name} ({bookmaker_name})] [{threshold_value}]: {begin_odd} -> {end_odd}")

                    # Create a CorrectScoreOdds object and append it to the list
                    correct_score_odd = CorrectScoreOdds(
                                        score     = threshold_value,
                                        bookmaker = bookmaker_name,
                                        odd_start = begin_odd,
                                        odd_end   = end_odd
                                        )
                    # Save (append) in Current match
                    self.current_match.append_correct_score(correct=correct_score_odd)

            except Exception as e:
                self.logger.error(f"Error processing correct score bet data for sub-category: {sub_category}, error: {e}")
           
    def process_data(self, match: Match) -> Match:
        """Processes the bet data and prints the extracted information."""
        
        # Initialize match-specific variables
        self.initialize_variables(match=match)

        # Retrieve Flashscore data
        self.logger.info("Retrieving Flashscore data...")
        response_txt = retrieve_flashscore_data(url=self.url_api, return_as_text=True)

        # Split the data into market segments based on separator
        market_segments = response_txt.split("~OA÷")[1:]

        for market_segment in market_segments:
            # it's split that why we skip the first element
            sub_categories = market_segment.split("~OB÷")[1:]

            # Extract bet type (e.g., home-away, over-under, correct score)
            bet_type = self._bet_type(text=market_segment)
            
            for sub_category in sub_categories:
                # Extract bet variant (e.g., full match, set 1, set 2)
                bet_variant = self._bet_variant(text=sub_category)

                # Process based on the bet type
                if bet_type == "home-away":
                    # Process home away and save it to self.current_match
                    self.logger.info("[HOME - AWAY]")
                    self.process_home_away(sub_category = sub_category,
                                           bet_variant  = bet_variant)
                    
                
                elif bet_type == "over-under":
                    # Process over_under and save it to self.current_match
                    self.logger.info("[OVER - UNDER]")
                    self.process_over_under(sub_category = sub_category,
                                            bet_variant  = bet_variant)   
                
                elif bet_type == "correct-score":
                    # Process correct score and save it to self.current_match
                    self.logger.info("[CORRRECT SCORE]")
                    self.process_correct_score(sub_category = sub_category,
                                               bet_variant  = bet_variant)
                    
                elif bet_type == "odd-even":
                    # Match  =>¬OBU÷full-time¬OBI÷ft¬SOB÷1¬~LY÷Odd¬LZ÷Even¬~OE÷141¬OD÷Betclic.fr¬OPI÷https://static.flashscore.com/res/image/data/bookmakers/80-141.png¬OPN÷¬BIP÷1¬OK÷0¬XB÷1.85¬XC÷1.85¬OG÷1
                    pass
                
                elif bet_type == "asian-handicap":
                    pass # GnqMEQkK
                
                else:
                    self.logger.warning("Unknown bet type: %s", bet_type)
                    raise NotImplementedError(f"Bet type '{bet_type}' not implemented yet.")    

        return self.current_match  

if __name__ == "__main__":
    import requests

    # Set up logging (if not already configured)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(name)s: %(message)s')

    player1 = Player(id          = "golem",
                     name        = "golem",
                     nationality = "golem",
                     link        = "golem")
    player2 = replace(player1)

    data = Match(
        match_id   = "Kx3ou23b",
        odds_link  = "https://2.flashscore.ninja/2/x/feed/df_od_1_Kx3ou23b",
        stats_link = "golem",
        score_link = "golem",
        status_link= "golem",
        match_date = "golem",
        timestamp  = "golem",
        round      = "golem",
        player1    = player1,
        player2    = player2,
        )

    parser = FlashscoreOddsParser()
    match_processed = parser.process_data(match=data)

    print(" === Match === ")
    print(match_processed.to_dict())
