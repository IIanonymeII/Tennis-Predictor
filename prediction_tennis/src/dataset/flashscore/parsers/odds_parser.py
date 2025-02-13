  
from dataclasses import asdict
import logging
import re
from typing import Any, Dict, List
import pandas as pd

from prediction_tennis.src.dataset.flashscore.models.odds import CorrectScoreOdds, HomeAwayOdds, OverUnderOdds
from prediction_tennis.src.dataset.flashscore.utils.text_extraction import extract_odds, extract_pattern_from_text



class FlashscoreOddsParser:
    """
    Parser utilisant une machine à états pour traiter les segments du flux.
    """
    def __init__(self, match_id: str) -> None:
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [ODDS]")
        self.match_id = match_id

        self.home_away_odds     : List[HomeAwayOdds]     = []
        self.over_odds          : List[OverUnderOdds]    = []
        self.under_odds         : List[OverUnderOdds]    = []
        self.correct_score_odds : List[CorrectScoreOdds] = []

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
        self.logger.debug("Extracting bookmaker ID from sub-category: %s", text)

        # Mapping of bookmaker IDs to their respective names
        bookmaker_id_to_name = {
            "160": "Unibet",
            "129": "Bwin",
            "398": "Netbet",
            "141": "betclic"
        }

        # Extract the bookmaker ID from the text using the defined pattern
        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        bookmaker_id_pattern = r"([^¬÷]+)¬OD÷"
        bookmaker_id = extract_pattern_from_text(text=text, pattern=bookmaker_id_pattern)
        self.logger.info("Bookmaker ID extracted: %s", bookmaker_id)

        try:
            bookmaker_name = bookmaker_id_to_name.get(bookmaker_id)

        except Exception as e:
            self.logger.error("Error retrieving bookmaker name: %s", e)
            bookmaker_name = None

        return bookmaker_name
    
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
        sub_bookmakers = sub_category.split("~OE÷")[1:]

        for sub_bookmaker in sub_bookmakers:
            try:
                # Extract bookmaker name and web name
                bookmaker_name = self._bookmaker_name(text=sub_bookmaker)
                bookmaker_web_name = self._bookmaker_web_name(text=sub_bookmaker)

                # Extract odds for both players
                (begin_odd_1, end_odd_1), (begin_odd_2, end_odd_2) = self._bookmaker_odd_player(text=sub_bookmaker)

                self.logger.info(f"[{bet_variant}] [{bookmaker_web_name} ({bookmaker_name})] [1]: {begin_odd_1} -> {end_odd_1}")
                self.logger.info(f"[{bet_variant}] [{bookmaker_web_name} ({bookmaker_name})] [2]: {begin_odd_2} -> {end_odd_2}")

                # Create a HomeAwayOdds object and append it to the list
                home_away_odd = HomeAwayOdds(
                    bet_variant=bet_variant,
                    bookmaker=bookmaker_name,
                    odd_player1_start=begin_odd_1,
                    odd_player1_end=end_odd_1,
                    odd_player2_start=begin_odd_2,
                    odd_player2_end=end_odd_2
                )
                self.home_away_odds.append(home_away_odd)

            except Exception as e:
                # Log any errors that occur during processing
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
                        bet_variant=bet_variant,
                        threshold_type=threshold_type,
                        threshold_value=threshold_value,
                        bookmaker=bookmaker_name,
                        odd_start=begin_odd_over,
                        odd_end=end_odd_over
                        )

                    under_odd = OverUnderOdds(
                        bet_variant=bet_variant,
                        threshold_type=threshold_type,
                        threshold_value=threshold_value,
                        bookmaker=bookmaker_name,
                        odd_start=begin_odd_under,
                        odd_end=end_odd_under
                        )

                    self.over_odds.append(over_odd)
                    self.under_odds.append(under_odd)

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
                        score=threshold_value,
                        bookmaker=bookmaker_name,
                        odd_start=begin_odd,
                        odd_end=end_odd
                    )
                    self.correct_score_odds.append(correct_score_odd)

            except Exception as e:
                self.logger.error(f"Error processing correct score bet data for sub-category: {sub_category}, error: {e}")
           
    def process_data(self, data_str: str) -> None:
        """Processes the bet data and prints the extracted information."""
        market_segments = data_str.split("~OA÷")[1:]

        
        for market_segment in market_segments:
            # it's split that why we skip the first element
            sub_categories = market_segment.split("~OB÷")[1:]

            # extract Home-away , over-under, correct score, etc.
            bet_type = self._bet_type(text=market_segment)
            
            for sub_category in sub_categories:
                # Full match, set 1, set 2, etc.
                bet_variant = self._bet_variant(text=sub_category)

                if bet_type == "home-away":
                    self.logger.info("[HOME - AWAY]")
                    self.process_home_away(sub_category = sub_category,
                                           bet_variant  = bet_variant)
                
                elif bet_type == "over-under":
                    self.process_over_under(sub_category = sub_category,
                                            bet_variant  = bet_variant)   
                
                elif bet_type == "correct-score":
                    self.process_correct_score(sub_category = sub_category,
                                               bet_variant  = bet_variant)                
                else:
                    self.logger.warning("Unknown bet type: %s", bet_type)
                    raise NotImplementedError(f"Bet type '{bet_type}' not implemented yet.")        

    def get_home_away_odds_dict(self) -> Dict[str, str]:
        """
        Constructs a dictionary of home-away odds keyed by match_id.

        Returns:
            Dict[str, str]: A dictionary containing home-away odds data.
        """
        data: Dict[str, str] = {}

        if not self.home_away_odds:
            self.logger.warning("No HomeAwayOdds available to process.")
            return data

        data["match_id"] = self.match_id
        self.logger.info(f"Processing HomeAwayOdds for match_id: {data['match_id']}")

        for odd in self.home_away_odds:
            try:
                data.update(odd.to_dict())
            except AttributeError as e:
                self.logger.error(f"Error processing HomeAwayOdds: {e}")

        self.logger.debug(f"Constructed home away odds dictionary ({len(data)} keys): {data}")
        return data

    def get_over_odds_dict(self) -> Dict[str, str]:
        """
        Constructs a dictionary of over odds keyed by match_id.

        Returns:
            Dict[str, str]: A dictionary containing over odds data.
        """
        data: Dict[str, str] = {}

        if not self.over_odds:
            self.logger.warning("No 'Over odds' available to process.")
            return data

        data["match_id"] = self.match_id
        self.logger.info(f"Processing 'Over odds' for match_id: {data['match_id']}")

        for odd in self.over_odds:
            try:
                data.update(odd.to_dict())
            except AttributeError as e:
                self.logger.error(f"Error processing 'Over odds': {e}")

        self.logger.debug(f"Constructed 'Over odds' dictionary ({len(data)} keys): {data}")
        return data
    
    def get_under_odds_dict(self) -> Dict[str, str]:
        """
        Constructs a dictionary of under odds keyed by match_id.

        Returns:
            Dict[str, str]: A dictionary containing under odds data.
        """
        data: Dict[str, str] = {}

        if not self.under_odds:
            self.logger.warning("No 'Under odds' available to process.")
            return data

        data["match_id"] = self.match_id
        self.logger.info(f"Processing 'Under odds' for match_id: {data['match_id']}")

        for odd in self.under_odds:
            try:
                data.update(odd.to_dict())
            except AttributeError as e:
                self.logger.error(f"Error processing 'Under odds': {e}")

        self.logger.debug(f"Constructed 'Under odds' dictionary ({len(data)} keys): {data}")
        return data
    
    def get_correct_score_odds_dict(self) -> Dict[str, str]:
        """
        Constructs a dictionary of correct score odds keyed by match_id.

        Returns:
            Dict[str, str]: A dictionary containing correct score odds data.
        """
        data: Dict[str, str] = {}

        if not self.correct_score_odds:
            self.logger.warning("No 'Correct Score odds' available to process.")
            return data

        data["match_id"] = self.match_id
        self.logger.info(f"Processing 'Correct Score odds' for match_id: {data['match_id']}")

        for odd in self.correct_score_odds:
            try:
                data.update(odd.to_dict())
            except AttributeError as e:
                self.logger.error(f"Error processing 'Correct Score odds': {e}")

        self.logger.debug(f"Constructed 'Correct Score odds' dictionary ({len(data)} keys): {data}")
        return data

       

if __name__ == "__main__":
    import requests

    # Set up logging (if not already configured)
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(name)s: %(message)s')
    logger = logging.getLogger("Main")

    # Build the URL and headers for the request
    id_match = "Kx3ou23b"
    url = f"https://2.flashscore.ninja/2/x/feed/df_od_1_{id_match}"
    headers = {"x-fsign": "SW9D1eZo"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        data_str = response.text

        parser = FlashscoreOddsParser(match_id=id_match)
        
        parser.process_data(data_str=data_str)
        
        print(" === HOME AWAY ===")
        print(parser.get_home_away_odds_dict())

        print(" === OVER ===")
        print(parser.get_over_odds_dict())

        print(" === UNDER ===")
        print(parser.get_under_odds_dict())

        print(" === CORRECT SCORE ===")
        print(parser.get_correct_score_odds_dict())

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL: {e}")
    except ValueError as e:
        logger.error(f"Error extracting data: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

