#!/usr/bin/env python3

import re
import logging
from typing import Dict, List
from bs4 import BeautifulSoup, Tag
import pandas as pd

from prediction_tennis.src.dataset.flashscore.models.tournaments import Tournaments, TournamentsDate
from prediction_tennis.src.dataset.flashscore.utils.flashscore_client import build_full_links, retrieve_flashscore_data
from prediction_tennis.src.dataset.flashscore.utils.text_extraction import extract_year



class FlashscoreTournamentArchiveParser:
    """
    Parser for the FlashScore tournament archive page.

    Extracts tournament archive data for each date for a given tournament.
    """

    def __init__(self) -> None:
        """Initialize the parser"""
        self.logger = logging.getLogger("[FLASHSCORE][TOURNAMENT DATE]")
        self.base_url = "https://www.flashscore.com/"
        self.url: str = ""  # This will be set after initializing tournament variables.
        self.list_tournament_date: List[TournamentsDate] = []

    def _init_variable(self, tournament : Dict[str, str]) -> None:
        """
        Initialize tournament-related variables using the provided dictionary.

        Args:
            tournament (Dict[str, str]): A dictionary with tournament details.
                It must include the keys defined in the Tournaments dataclass ('slug' and 'id').

        Raises:
            ValueError: If any required tournament keys are missing.
        """
        self.logger.info(" ___ INIT ___")

        # reset value
        self.list_tournament_date: List[TournamentsDate] = []
        
        # Verify that the required keys exist in the tournament dictionary.
        required_keys = set(Tournaments.__annotations__.keys())
        missing_keys = required_keys - tournament.keys()
        if missing_keys:
            self.logger.error(f"Missing required tournament keys: {missing_keys}")
            raise ValueError(f"Missing required tournament keys: {missing_keys}")
        
        # Extract tournament details.
        self.tournament_slug: str = tournament["slug"]
        self.tournament_id: str = tournament["id"]

        # Construct the URL for the tournament's archive page.
        self.url = f"https://www.flashscore.com/tennis/atp-singles/{self.tournament_slug}/archive/"
        self.logger.info(f"[{self.tournament_slug} ({self.tournament_id})] : {self.url}")

    def get_archive_section(self, soup: BeautifulSoup) -> Tag:
        """
        Retrieve the tournament archive section from the parsed HTML.

        Args:
            soup (BeautifulSoup): The parsed HTML document.

        Returns:
            Tag: The HTML tag containing the tournament archive section.

        Raises:
            Exception: If the tournament archive section is not found.
        """
        self.logger.debug("Searching for the archive section in the HTML")

        # Attempt to locate the archive 'section' by its id.
        archive_section = soup.find("section", id="tournament-page-archiv")
        if archive_section is None:
            self.logger.error("The tournament archive section was not found")
            raise Exception("The tournament archive section was not found")
        
        self.logger.info("Tournament archive section found")
        return archive_section

    def parse_archive_row(self, row: Tag) -> TournamentsDate:
        """
        Extract tournament details from a single archive row.

        Args:
            row (Tag): A BeautifulSoup Tag representing one archive row.

        Returns:
            TournamentsDate: A dataclass instance representing tournament archive data.

        Raises:
            ValueError: If required HTML elements are not found in the row.
        """
        self.logger.debug("Parsing an archive row")
        
        # Initialize variables
        tournament_name: str = ""
        link           : str = ""
        winner         : str = ""
        year           : str = ""

        # Extract tournament season div
        season_div = row.find("div", class_="archive__season")
        if season_div is None:
            self.logger.error("Season div not found in archive row")
            raise ValueError("Season div not found in archive row")
            
        # Extract the clickable link tag from the season div
        link_tag = season_div.find("a", class_="archive__text--clickable")
        if link_tag is None:
            self.logger.error("Link tag not found in season div")
            raise ValueError("Link tag not found in season div")

        # Get tournament name from the link tag.
        # ex : 'ATP Acapulco 2024', 'ATP Acapulco 2023', ...
        tournament_name = link_tag.get_text(strip=True)

        # Get the href attribute to build the full link
        # ex : '/tennis/atp-singles/acapulco/' , '/tennis/atp-singles/acapulco-2023/'
        raw_link = link_tag.get("href")
        if not raw_link:
            self.logger.error("Href attribute missing in the link tag")
            raise ValueError("Href attribute missing in the link tag")

        try: # Build the full link and test if exist
            link = build_full_links(base_url=self.base_url, add_slug=raw_link)
        except Exception as e:
            self.logger.error("Failed to build full link: %s", e)
            raise

        try: # Extract the year from the tournament name using the helper function
            year = extract_year(text=tournament_name)
        except Exception as e:
            self.logger.error("Failed to extract year from tournament name '%s': %s", tournament_name, e)
            raise
                
        self.logger.debug(f"[{year}] Tournament '{tournament_name}' found => {link}")
    

        # Extract winner information if available
        winner_div = row.find("div", class_="archive__winner")
        if winner_div:
            winner_tag = winner_div.find("a", class_="archive__text--clickable")
            if winner_tag:
                winner = winner_tag.get_text(strip=True)
                self.logger.debug("Winner found: %s", winner)

        # Create and return a 'TournamentsDate' dataclass instance with the extracted data
        tournament_date = TournamentsDate(
            slug            = self.tournament_slug,
            id              = self.tournament_id,
            tournament_name = tournament_name,
            year            = year,
            link            =link ,    
            winner          = winner)
        self.logger.info("TournamentsDate created for tournament '%s' (%s)", tournament_name, year)
        return tournament_date

    def found_all_date_in_archive(self, tournament: Dict[str, str]) -> pd.DataFrame:
        """
        Retrieve all tournament archive dates for a given tournament.

        This method performs the following steps:
          0. Initializes tournament variables.
          1. Retrieves and parses the tournament archive page.
          2. Extracts the tournament archive section from the HTML.
          3. Finds and processes each tournament row to extract details.
          4. Converts the extracted data into a pandas DataFrame.

        Args:
            tournament (Dict[str, str]): A dictionary containing tournament details, which must
                                         include the required keys as defined in the Tournaments dataclass.

        Returns:
            pd.DataFrame: A DataFrame containing all extracted tournament archive dates.

        Raises:
            Exception: If there is an error retrieving or parsing the archive page.
        """

        # 0. Initialize tournament-specific variables.
        self._init_variable(tournament=tournament)


        # 1. Retrieve and parse the tournament archive page.
        self.logger.info("Starting to parse the tournament archive page")
        try:
            response_text = retrieve_flashscore_data(url=self.url, return_as_text=True)
            soup = BeautifulSoup(response_text, "html.parser")
        except Exception as e:
            self.logger.error(f"Error retrieving or parsing the tournament archive page: {e}")
            raise Exception(f"Error retrieving or parsing the tournament archive page: {e}") from e

        # 2. Extract the tournament archive section.
        archive_section = self.get_archive_section(soup=soup)

        # 3. Find all tournament rows in the archive section and process each row.
        rows = archive_section.find_all("div", class_="archive__row")
        self.logger.info("Found %d archive rows.", len(rows))
        
        for row in rows:
            try:
                tournament_date = self.parse_archive_row(row=row)
                self.list_tournament_date.append(tournament_date)
            except Exception as e:
                self.logger.error("Error parsing archive row: %s", e)

        self.logger.info("Finished processing archive rows. Total records: %d", len(self.list_tournament_date))

        # 4. Convert the extracted data into a pandas DataFrame.
        df = pd.DataFrame(self.list_tournament_date)
        self.logger.info("DataFrame created with %d records.", len(df))
        return df


if __name__ == "__main__":
    
    # Configure logging for the application.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    dict_data = {"slug" : "acapulco",
                 "id"   : "nanana",}

    try:
        parser = FlashscoreTournamentArchiveParser()
        df = parser.found_all_date_in_archive(tournament = dict_data)

        print(" === DF ===")
        print(df)
        

    except Exception as err:
        logging.exception("Exception occurred while processing the response: %s", err)
