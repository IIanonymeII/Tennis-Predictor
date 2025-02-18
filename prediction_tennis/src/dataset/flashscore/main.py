
import datetime
import logging
import os
import time
from typing import Dict, List
import pandas as pd
import requests
from tqdm import tqdm

from prediction_tennis.src.dataset.flashscore.parsers.match_status_parser import FlashscoreMatchStatusProcessor
from prediction_tennis.src.dataset.flashscore.parsers.matchs_in_tournament_parser import FlashscoreMatchInTournamentParser
from prediction_tennis.src.dataset.flashscore.parsers.odds_parser import FlashscoreOddsParser
from prediction_tennis.src.dataset.flashscore.parsers.match_score_parser import FlashscoreMatchScoreProcessor
from prediction_tennis.src.dataset.flashscore.parsers.tournament_dates_parser import FlashscoreTournamentArchiveParser
from prediction_tennis.src.dataset.flashscore.parsers.tournaments_parser import FlashscoreTournamentProcessor
from prediction_tennis.src.dataset.flashscore.utils.flashscore_client import retrieve_flashscore_data
from prediction_tennis.src.dataset.flashscore.utils.log_setup import initialize_logging

def save_to_csv(data: List[Dict[str, str]], file_path: str) -> None:
    """
    Saves a list of dictionaries to a CSV file.
    
    :param data: List of dictionaries containing tournament data.
    :param file_path: Path to save the CSV file.
    """
    try:
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        logging.info(f"Data successfully saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save data to {file_path}: {e}")

def main():
    """
    Main function to fetch tournament data from Flashscore, process it, 
    and save it as CSV files.
    """
    # Initialize logging.
    initialize_logging("log/flashscore.log")
    logger = logging.getLogger("[DATASET] [MAIN]")

    url = "https://www.flashscore.com/x/req/m_2_5724"
    response_txt: str = retrieve_flashscore_data(url=url, return_as_text=True)

    # Initialize parsers
    parser_global_tournament   = FlashscoreTournamentProcessor()
    parser_tournament          = FlashscoreTournamentArchiveParser()
    parser_match_in_tournament = FlashscoreMatchInTournamentParser()
    parser_match_status        = FlashscoreMatchStatusProcessor()
    parser_match_score         = FlashscoreMatchScoreProcessor()
    parser_match_odd           = FlashscoreOddsParser()

    # Process global tournament data
    tourn_global_list: List["TournamentsMinimaliste"] = parser_global_tournament.process_data(data_str=response_txt)

    # Iterate over each minimal tournament to process detailed tournaments
    minimal_tournament_bar = tqdm(tourn_global_list, desc="Processing Minimal Tournament: Unknown")
    for tournament_minimaliste in minimal_tournament_bar:
        minimal_slug = getattr(tournament_minimaliste, "slug", "Unknown")
        minimal_tournament_bar.set_description(f"Processing Minimal Tournament: '{minimal_slug}'")

        # Initialize an empty list to accumulate tournament dictionaries
        tournament_dicts: List[Dict[str, str]] = []

        tournaments_list: List["Tournaments"] = parser_tournament.found_all_date_in_archive(tournament = tournament_minimaliste)

        # Process each detailed tournament
        tournament_bar = tqdm(tournaments_list, desc="Processing Tournament: Unknown", leave=False)
        for tournament in tournament_bar:
            tournament_name = getattr(tournament, "name", "Unknown")
            tournament_bar.set_description(f"Processing Tournament: '{tournament_name}'")
        
            match_list: list["Matchs"] = parser_match_in_tournament.find_all_matches_in_tournament(tournament=tournament)
            
            # Process each match in the tournament
            match_bar = tqdm(match_list, desc=f"Processing {tournament_name} match: Unknown", leave=False)
            for match_instance in match_bar:
                match_round = getattr(match_instance, "round", "Unknown")
                match_bar.set_description(f"Processing {tournament_name} match: '{match_round}'")
                
                # Process match data sequentially
                processed_match = parser_match_status.process_data(match=match_instance)
                processed_match = parser_match_score.process_data(match=processed_match)
                processed_match = parser_match_odd.process_data(match=processed_match)
                
                # Add processed match to the tournament
                tournament.add_match(match=processed_match)

            # Extend the overall tournament dictionary list with the current tournament's data
            tournament_dicts.extend(tournament.to_dict())

        # Save tournament data to CSV
        csv_filename = f"data/flashscore/tournament_{minimal_slug}.csv"
        save_to_csv(tournament_dicts, csv_filename)
        logger.info(f"Tournament data saved to {csv_filename}")

if __name__ == "__main__":
    main()