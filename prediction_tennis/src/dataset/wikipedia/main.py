"""
ATP Player Data Processing Module.

This module orchestrates the complete workflow for processing ATP tennis player data,
including fetching, matching, and saving player information from various sources.
The main function handles the entire pipeline from loading flashscore data to
saving processed player information to CSV files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Union
from tqdm import tqdm

from prediction_tennis.src.dataset.flashscore.utils.tournament_saver import (
    save_tournament_data_to_csv,
)
from prediction_tennis.src.dataset.wikipedia.models.tournaments import Tournaments
from prediction_tennis.src.dataset.wikipedia.parsers.season_links import ATPSeasonLinkExtractor
from prediction_tennis.src.dataset.wikipedia.parsers.season_tournament import ATPSeasonParser
from prediction_tennis.src.dataset.wikipedia.utils.config import TOURNAMENT_PARTICULAR_CASE
from prediction_tennis.src.utils.log_setup import initialize_logging


WIKIPEDIA_LOG_FILE = Path("log/wikipedia_processing.log")
DATA_DIR = Path("data/01_raw")
WIKIPEDIA_RAW_PATH = DATA_DIR / "wikipedia"


def main() -> None:
    """Main function to process ATP tournament data from Wikipedia and save it to CSV."""
    # Initialize logging.
    initialize_logging(WIKIPEDIA_LOG_FILE)
    logger = logging.getLogger("[DATASET] [MAIN]")

    # Wikipedia URL for ATP Tour data.
    wikipedia_url = "https://fr.wikipedia.org/wiki/ATP_Tour"

    # Initialize parsers for season links and tournament data.
    season_link_extractor = ATPSeasonLinkExtractor()
    tournament_parser = ATPSeasonParser()

    # List to accumulate tournament data dictionaries.
    tournament_data: List[Dict[str, Union[str, int]]] = []

    # Extract the season years from the Wikipedia page.
    season_years: Dict[str, str] = season_link_extractor.extract_season_years(wikipedia_url)

    # Process each tournament for each year.
    tournament_progress = tqdm(season_years.items(), desc="Processing Tournament: Unknown")
    for year, link in tournament_progress:
        tournament_progress.set_description(f"Processing Tournament: '{year}'")

        # Skip years before 1998.
        if int(year) < 1998:
            continue

        # Extract tournament data for the given year.
        tournament_list: List[Tournaments] = tournament_parser.parse(url=link, year=year)
        for tournament in tournament_list:
            tournament_data.append(tournament.to_dict())
    
    # add particular case
    tournament_data = tournament_data + TOURNAMENT_PARTICULAR_CASE

    # Save tournament data to CSV
    save_tournament_data_to_csv(
        tournament_data=tournament_data,
        output_directory_path=WIKIPEDIA_RAW_PATH,
        filename="tournament.csv",
    )
    logger.info("=== WIKIPEDIA Data Processing Successfully Completed ===")


if __name__ == "__main__":
    main()
