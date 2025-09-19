
import logging
from typing import Dict, List, Union
from tqdm import tqdm

from prediction_tennis.src.dataset.flashscore.main import save_to_csv
from prediction_tennis.src.dataset.flashscore.utils.log_setup import initialize_logging
from prediction_tennis.src.dataset.wikipedia.models.tournaments import Tournaments
from prediction_tennis.src.dataset.wikipedia.parsers.season_links import ATPSeasonLinkExtractor
from prediction_tennis.src.dataset.wikipedia.parsers.season_tournament import ATPSeasonParser

def main() -> None:
    """Main function to process ATP tournament data from Wikipedia and save it to CSV."""
    # Initialize logging.
    log_file = "log/flashscore.log"
    initialize_logging(log_file)
    logger = logging.getLogger("[DATASET] [MAIN]")

    # Wikipedia URL for ATP Tour data.
    wikipedia_url = "https://fr.wikipedia.org/wiki/ATP_Tour"

    # Initialize parsers for season links and tournament data.
    season_link_extractor = ATPSeasonLinkExtractor()
    tournament_parser     = ATPSeasonParser()

    # List to accumulate tournament data dictionaries.
    tournament_data: List[Dict[str, Union[str, int]]] = []

    # Extract the season years from the Wikipedia page.
    season_years: Dict[str, str] = season_link_extractor.extract_season_years(wikipedia_url)
    
    # Process each tournament for each year.
    tournament_progress = tqdm(season_years.items(), desc="Processing Tournament: Unknown")
    for year, link in tournament_progress:
        tournament_progress.set_description(f"Processing Tournament: '{year}'")

        # Skip years before 2000.
        if int(year) < 1998:
            continue

        # Extract tournament data for the given year.
        tournament_list: List[Tournaments] = tournament_parser.parse(url=link, year=year)
        for tournament in tournament_list:
            tournament_data.append(tournament.to_dict())

    # Save the accumulated tournament data to CSV.
    csv_filename = "data/01_raw/wikipedia/tournament.csv"
    save_to_csv(tournament_data, csv_filename)
    logger.info(f"Tournament data saved to {csv_filename}")

if __name__ == "__main__":
    main()