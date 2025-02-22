#!/usr/bin/env python3

from dataclasses import replace
import re
import logging
from typing import Any, Dict, List, Set
from bs4 import BeautifulSoup, Tag
import pandas as pd

from prediction_tennis.src.dataset.flashscore.raw.models.tournaments import Tournaments, TournamentsMinimaliste
from prediction_tennis.src.dataset.flashscore.raw.utils.flashscore_client import validate_and_check_url, retrieve_flashscore_data
from prediction_tennis.src.dataset.flashscore.raw.utils.text_extraction import extract_year



class FlashscoreTournamentArchiveParser:
    """
    Parser for the FlashScore tournament archive page.

    Extracts tournament archive data for each date for a given tournament.
    """

    def __init__(self) -> None:
        """Initialize the parser"""
        self.logger = logging.getLogger("[FLASHSCORE][PARSER] [TOURNAMENT DATE]")

        # Base URL
        self.base_url = "https://www.flashscore.com/"

        # URL for archive tournament (to be set later)
        self.url_archive: str = ""

        # Lists to store tournament
        self.list_tournament_date: List[Tournaments] = []

    def initialize_variables(self, tournament : TournamentsMinimaliste) -> None:
        """
        Initialize tournament-related variables using the provided tournament object.

        Args:
            tournament (TournamentsMinimaliste): An instance containing tournament details.

        Raises:
            ValueError: If the provided object is not an instance of TournamentsMinimaliste.
        """
        self.logger.info(" ___ INIT ___")

        # Verify that match is an instance of the Match class
        if not isinstance(tournament, TournamentsMinimaliste):
            self.logger.error("Provided object is not an instance of the TournamentsMinimaliste class")
            raise ValueError("Provided object is not an instance of the TournamentsMinimaliste class")


        # reset value
        self.list_tournament_date: List[Tournaments] = []

        # Extract tournament details.
        self.current_minimaliste_tournament = replace(tournament)

        # Construct the URL for the tournament's archive page.
        self.url_archive = self.current_minimaliste_tournament.link_archives
        
        self.logger.info(f"{self.current_minimaliste_tournament}")

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
        archive_section: Any = soup.find("section", id="tournament-page-archiv")
        if archive_section is None:
            self.logger.error("The tournament archive section was not found")
            raise Exception("The tournament archive section was not found")
        
        self.logger.info("Tournament archive section found")
        return archive_section

    def parse_archive_row(self, row: Tag) -> Tournaments:
        """
        Extract tournament details from a single archive row.

        Args:
            row (Tag): A BeautifulSoup Tag representing one archive row.

        Returns:
            Tournaments: A dataclass instance representing tournament archive data.

        Raises:
            ValueError: If required HTML elements are not found in the row.
        """
        self.logger.debug("Parsing an archive row")
        
        # Initialize extracted data variables
        tournament_name        : str = ""
        tournament_link        : str = ""
        tournament_link_result : str = ""
        tournament_winner      : str = ""
        tournament_year        : str = ""

        # Locate the season div containing tournament information
        season_div: Any = row.find("div", class_="archive__season")
        if season_div is None:
            self.logger.error("Season div not found in archive row.")
            raise ValueError("Season div not found in archive row.")
            
        # Extract tournament name and link
        link_tag: Any = season_div.find("a", class_="archive__text--clickable")
        if link_tag is None:
            self.logger.error("Link tag not found in season div.")
            raise ValueError("Link tag not found in season div.")

        # ex : 'ATP Acapulco 2024', 'ATP Acapulco 2023', ...
        tournament_name = link_tag.get_text(strip=True)

        # ex : '/tennis/atp-singles/acapulco/' , '/tennis/atp-singles/acapulco-2023/'
        raw_link: str = link_tag.get("href")
        if not raw_link:
            self.logger.error("Href attribute missing in the link tag")
            raise ValueError("Href attribute missing in the link tag")

        try: # Construct full tournament link and validate
            tournament_link = validate_and_check_url(url=f"{self.base_url}{raw_link}")
            tournament_link_result = validate_and_check_url(url=f"{tournament_link}results/")
        except Exception as exc:
            self.logger.error("Failed to build full link: %s", exc)
            raise

        try: # Extract year from the tournament name
            tournament_year = extract_year(text=tournament_name)
        except Exception as exc:
            self.logger.error("Failed to extract year from tournament name '%s': %s", tournament_name, exc)
            raise
                
        self.logger.debug(f"[{tournament_year}] Tournament '{tournament_name}' found => {tournament_link}")
    

        # Extract winner information if available
        winner_div = row.find("div", class_="archive__winner")
        if winner_div:
            winner_tag = winner_div.find("a", class_="archive__text--clickable")
            if winner_tag:
                tournament_winner = winner_tag.get_text(strip=True)
                self.logger.debug("Winner found: %s", tournament_winner)



        # Create and return a 'Tournaments' dataclass instance with extracted data
        tournament_date = Tournaments(
            name         = tournament_name,
            year         = tournament_year,
            link         = tournament_link ,
            link_results = tournament_link_result,
            winner_name  = tournament_winner,
            **self.current_minimaliste_tournament.__dict__,
            )

        self.logger.info("TournamentsDate created for tournament '%s' (%s)", tournament_name, tournament_year)
        return tournament_date

    def found_all_date_in_archive(self, tournament: TournamentsMinimaliste) -> List[Tournaments]:
        """
        Retrieve all archived tournament dates for a given tournament.

        This method follows these steps:
          1. Initializes tournament variables.
          2. Retrieves and parses the tournament archive page.
          3. Extracts the tournament archive section from the HTML.
          4. Iterates through each tournament row, extracts details,
             and constructs a list of `Tournaments`.

        Args:
            tournament (TournamentsMinimaliste): A dataclass instance containing minimal
            tournament details.

        Returns:
            List[Tournaments]: A list of tournament instances representing archived tournaments.

        Raises:
            ValueError: If required HTML elements are missing or incorrectly structured.
            ConnectionError: If there is an issue retrieving the archive page.
            Exception: For any unexpected parsing errors.
        """
        # Step 1: Initialize tournament-specific variables.
        self.initialize_variables(tournament=tournament)

        # Step 2: Retrieve and parse the tournament archive page.
        self.logger.info("Starting to parse the tournament archive page")
        try:
            response_text = retrieve_flashscore_data(url=self.url_archive, return_as_text=True)
            soup = BeautifulSoup(response_text, "html.parser")
        except Exception as exc:
            self.logger.error("Error retrieving or parsing the tournament archive page: %s", exc)
            raise ConnectionError("Error retrieving or parsing the tournament archive page") from exc

        # Step 3: Extract the tournament archive section.
        archive_section = self.get_archive_section(soup=soup)

        # Step 4: Process each tournament row to extract details
        rows = archive_section.find_all("div", class_="archive__row")
        self.logger.info("Found %d archive rows.", len(rows))
        
        for row in rows:
            try:
                tournament_date: Tournaments = self.parse_archive_row(row=row)
                self.list_tournament_date.append(tournament_date)
            except Exception as exc:
                self.logger.error("Error parsing archive row: %s", exc)

        self.logger.info("Finished processing archive rows. Total records: %d", len(self.list_tournament_date))

        return self.list_tournament_date.copy()


if __name__ == "__main__":
    
    # Configure logging for the application.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    data = TournamentsMinimaliste(
        slug          = "acapulco",
        id            = "golem",
        link_archives ="https://www.flashscore.com/tennis/atp-singles/acapulco/archive/"
        )

    parser = FlashscoreTournamentArchiveParser()
    tournament_list: List[Tournaments] = parser.found_all_date_in_archive(tournament = data)

    for tournament in tournament_list:
        print(tournament)
