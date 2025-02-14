#!/usr/bin/env python3
import logging
from typing import Dict, List
import pandas as pd
import requests

from prediction_tennis.src.dataset.flashscore.models.tournaments import TournamentsMinimaliste
from prediction_tennis.src.dataset.flashscore.utils.flashscore_client import validate_and_check_url
from prediction_tennis.src.dataset.flashscore.utils.text_extraction import extract_pattern_from_text

class FlashscoreTournamentProcessor:
    """
    A processor for handling Flashscore tournament data.

    This class is responsible for processing data from Flashscore to extract and manage
    information about various tournaments, including their names (slugs) and unique identifiers (IDs).
    """
    def __init__(self):
        """Initialize the parser state and set up logging."""
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [TOURNAMENT]")

        # Set Base url
        self.base_url = "https://www.flashscore.com/tennis/atp-singles/"

        # Lists to store tournaments
        self.list_tournaments: List[TournamentsMinimaliste] = []

    def _tournament_slug(self, text: str) -> str:
        """
        Extracts the tournament slug from the given text.

        Args:
            text (str): The input text from which to extract the tournament slug.

        Returns:
            str: The extracted tournament slug.
        """
        self.logger.debug("Extracting tournament slug from text: %s", text)

        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        tournament_slug_pattern = r"¬MU÷([^¬÷]+)¬MT÷"
        tournament_slug = extract_pattern_from_text(text=text, pattern=tournament_slug_pattern)

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

        # Define regex pattern ensuring no '¬' or '÷' inside the captured group
        tournament_id_pattern = r"¬MTI÷([^¬÷]+)¬"
        tournament_id = extract_pattern_from_text(text=text, pattern=tournament_id_pattern)

        self.logger.info("Tournament ID extracted: %s", tournament_id)

        return tournament_id

    def process_data(self, data_str: str) -> List[TournamentsMinimaliste]:
        """
        Processes tournament data to extract each tournament's slug and ID.

        Args:
            data_str (str): The input data string containing tournament information.

        Returns:
            List[TournamentsMinimaliste]: A list of processed tournament objects.
        """
        # Split the input data string to extract individual tournament segments
        tournament_segments = data_str.split("~MN÷")[1:]

        for tournament_data in tournament_segments:
            try:
                # Extract the tournament slug and ID
                tournament_slug = self._tournament_slug(text=tournament_data)
                tournament_id = self._tournament_id(text=tournament_data)

                self.logger.info(f"[{tournament_slug} ({tournament_id})]")

                # Validate and construct archive URL
                url_archive = validate_and_check_url(url=f"{self.base_url}{tournament_slug}/archive/")

                # Create a tournament object
                tournament = TournamentsMinimaliste(
                    slug          = tournament_slug,
                    id            = tournament_id,
                    link_archives = url_archive,
                    )

                self.list_tournaments.append(tournament)

            except Exception as e:
                self.logger.error(f"Error processing tournament data: {e}")
        return self.list_tournaments.copy()

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

    tourn_list: List[TournamentsMinimaliste] = parser.process_data(data_str=data_str)

    for tourn in tourn_list:
        print(tourn)
