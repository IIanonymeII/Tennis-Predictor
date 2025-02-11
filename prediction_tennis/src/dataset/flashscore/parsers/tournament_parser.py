#!/usr/bin/env python3
"""
Module to process tournament data from Flashscore response text.

The response text is expected to be a series of segments separated by '¬'.
Each segment is in the format "prefix÷value" (or exactly "~" to indicate termination).
Global data (from segments like MC or ML) is applied to every tournament record.
"""

import logging
from typing import Dict, List
import pandas as pd
import requests

from prediction_tennis.src.dataset.flashscore.models.tournaments import Tournaments
from prediction_tennis.src.dataset.flashscore.utils.text_extraction import extract_pattern_in_text

class FlashscoreTournamentProcessor:
    """
    A processor for handling Flashscore tournament data.

    This class is responsible for processing data from Flashscore to extract and manage
    information about various tournaments, including their names (slugs) and unique identifiers (IDs).
    """
    def __init__(self):

        self.logger = logging.getLogger("[FLASHSCORE_TOURNAMENT_PARSER]")
        self.list_tournaments: List[Tournaments] = []

    def _tournament_slug(self, text: str) -> str:
        """
        Extracts the tournament slug from the given text.

        Args:
            text (str): The input text from which to extract the tournament slug.

        Returns:
            str: The extracted tournament slug.
        """
        self.logger.debug("Extracting tournament slug from text: %s", text)

        tournament_slug_pattern = r"¬MU÷(.*?)¬MT÷"
        tournament_slug = extract_pattern_in_text(text=text, pattern=tournament_slug_pattern)

        self.logger.info("Tournament slug extracted: %s", tournament_slug)

        return tournament_slug
    
    def _tournament_id(self, text: str) -> str:
        """
        Extracts the tournament ID from the given text.

        Args:
            text (str): The input text from which to extract the tournament ID.

        Returns:
            str: The extracted tournament ID.
        """
        self.logger.debug("Extracting tournament ID from text: %s", text)

        tournament_id_pattern = r"¬MTI÷(.*?)¬"
        tournament_id = extract_pattern_in_text(text=text, pattern=tournament_id_pattern)

        self.logger.info("Tournament ID extracted: %s", tournament_id)

        return tournament_id

    def process_data(self, data_str: str) -> None:
        """
        Processes each tournament to extract its name (slug) and ID.

        Args:
            data_str (str): The input data string containing tournament information.
        """
        # Split the input data string to extract individual tournament segments
        tournament_segments = data_str.split("~MN÷")[1:]

        for tournament_data in tournament_segments:
            try:
                # Extract the tournament slug and ID
                tournament_slug = self._tournament_slug(text=tournament_data)
                tournament_id = self._tournament_id(text=tournament_data)

                self.logger.info(f"[{tournament_slug} ({tournament_id})]")

                tournament = Tournaments(slug=tournament_slug, id=tournament_id)
                self.list_tournaments.append(tournament)

            except Exception as e:
                self.logger.error(f"Error processing tournament data: {e}")

    def get_tournament_df(self) -> pd.DataFrame:
        """
        Converts the list of tournaments into a Pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame containing the tournament data.
        """
        if not self.list_tournaments:
            self.logger.warning("No tournaments available to process.")
            # Return an empty DataFrame if no tournaments are available
            return pd.DataFrame()

        # Convert each Tournaments instance in the list to a dictionary
        data: List[Dict[str,str]] = [tournament.to_dict() for tournament in self.list_tournaments]

        self.logger.info(f"Converting {len(data)} tournaments to DataFrame.")

        return pd.DataFrame(data)

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",)
    url = "https://www.flashscore.com/x/req/m_2_5724"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors.
    
    except Exception as fetch_error:
        logging.exception("Error fetching data:")

    data_str = response.text
    parser = FlashscoreTournamentProcessor()

    try:
        parser.process_data(data_str=data_str)
        df = parser.get_tournament_df()

        print("=== DF ===")
        print(df)
        
    except Exception as process_error:
        logging.exception("Error processing data:")
