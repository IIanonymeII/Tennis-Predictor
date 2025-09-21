
from pathlib import Path

import pandas as pd
import logging

from prediction_tennis.src.dataset.atptour.processors.player_data_fetcher import PlayerDataFetcher
from prediction_tennis.src.dataset.atptour.processors.player_data_processor import collect_detailed_player_objects, extract_unique_players_from_flashscore, process_players_data_with_matching
from prediction_tennis.src.dataset.atptour.processors.player_data_saver import save_players_data_to_csv
from prediction_tennis.src.dataset.atptour.utils.flashscore_utils import extract_df_from_flashscore
from prediction_tennis.src.utils.log_setup import initialize_logging

# Constants for paths (using pathlib for better path handling)
DATA_DIR = Path("data/01_raw")
FLASHSCORE_RAW_PATH = DATA_DIR / "flashscore"
ATPTOUR_RAW_PATH = DATA_DIR / "atptour"
ATPTOUR_LOG_FILE = Path("log/atp_tour_processing.log")

def main():
    # Initialize logging
    initialize_logging(log_file=ATPTOUR_LOG_FILE)
    main_logger = logging.getLogger("[DATASET] [MAIN]")

    try:
        main_logger.info("=== Starting ATP Player Data Processing ===")

        # Load source data
        main_logger.info("Loading flashscore data from source...")
        flashscore_dataframe = extract_df_from_flashscore(str(FLASHSCORE_RAW_PATH))
        main_logger.info(f"Loaded flashscore data: {len(flashscore_dataframe)} records")

        # Extract unique players
        main_logger.info("Extracting unique players from flashscore data...")
        unique_players_df = extract_unique_players_from_flashscore(flashscore_dataframe)

        # Initialize data fetcher and process players
        main_logger.info("Initializing ATP data fetcher...")
        player_fetcher = PlayerDataFetcher("ATPDataFetcher")

        player_names_list = unique_players_df["player_name"].tolist()
        main_logger.info(f"Starting data fetch for {len(player_names_list)} unique players")

        # Fetch comprehensive player data
        comprehensive_player_data = player_fetcher.fetch_multiple_players_data(player_names=player_names_list)

        # Log initial fetch results
        total_entries = sum(len(entries) for entries in comprehensive_player_data.values())
        successful_players = sum(
            1 for entries in comprehensive_player_data.values() if entries
        )
        
        main_logger.info(f"=== Initial Data Fetch Complete ===\n"
                         f"Players processed: {len(comprehensive_player_data)}\n"
                         f"Successful fetches: {successful_players}\n"
                         f"Total player entries: {total_entries}"
                         )
        
        # Process player data with fuzzy matching to assign ATP URLs
        main_logger.info("Processing player data with fuzzy matching...")
        updated_players_df = process_players_data_with_matching(
            players_dataframe=unique_players_df,
            fetched_player_data=comprehensive_player_data
        )


        # Collect detailed player objects from ATP URLs
        main_logger.info("Collecting detailed player objects...")
        detailed_player_objects = collect_detailed_player_objects(
            players_dataframe=updated_players_df
        )

        # Final processing summary
        players_with_urls = len(updated_players_df.dropna(subset=['url_atptour']))
        main_logger.info(
            f"=== Complete Processing Summary ===\n"
            f"Total unique players: {len(unique_players_df)}\n"
            f"Players with ATP URLs: {players_with_urls}\n"
            f"Detailed player objects: {len(detailed_player_objects)}\n"
            f"Overall success rate: {len(detailed_player_objects)/len(unique_players_df)*100:.1f}%"
        )


        # Save comprehensive player data to CSV
        if detailed_player_objects:
            main_logger.info("Saving player data to CSV file...")
            save_players_data_to_csv(players_dataframe=updated_players_df,
                                     detailed_player_objects=detailed_player_objects,
                                     output_directory_path=ATPTOUR_RAW_PATH
                                     )
        else:
            main_logger.warning("No player objects to save - skipping CSV output")
        
        main_logger.info("=== ATP Player Data Processing Successfully Completed ===")

    except FileNotFoundError as exc:
        main_logger.error(f"Required file not found: {exc}")
        raise
    except pd.errors.EmptyDataError as exc:
        main_logger.error(f"Source data file is empty or corrupted: {exc}")
        raise
    except Exception as exc:
        main_logger.error(f"Unexpected error during processing: {exc}")
        raise
    finally:
        main_logger.info("=== ATP Player Data Processing Session Ended ===")

if __name__ == "__main__":
    main()
