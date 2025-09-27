import logging
from pathlib import Path
from typing import Dict, List, Union

import pandas as pd

from prediction_tennis.src.dataset.atptour.models.players import Player
from prediction_tennis.src.utils.file_utils import (
    _ensure_output_directory_exists,
    _get_file_size_mb,
    _log_dataframe_information,
    _save_dataframe_to_csv,
)


def _convert_player_objects_to_dicts(player_objects: List[Player]) -> List[Dict]:
    """
    Convert Player objects to dictionaries for DataFrame creation.

    Args:
        player_objects (List[Player]): List of Player objects

    Returns:
        List[Dict]: List of player data dictionaries

    Raises:
        AttributeError: If Player objects don't have expected attributes
    """
    logger = logging.getLogger("PlayerConverter")

    try:
        player_data_dicts = []

        for player_index, player_obj in enumerate(player_objects):
            try:
                # Convert Player object to dictionary
                if hasattr(player_obj, "__dict__"):
                    player_dict = player_obj.__dict__.copy()
                else:
                    # Fallback for objects without __dict__
                    player_dict = {
                        attr: getattr(player_obj, attr)
                        for attr in dir(player_obj)
                        if not attr.startswith("_") and not callable(getattr(player_obj, attr))
                    }

                player_data_dicts.append(player_dict)

            except Exception as exc:
                logger.warning(f"Failed to convert player object at index {player_index}: {exc}")
                continue

        logger.debug(f"Successfully converted {len(player_data_dicts)} player objects")
        return player_data_dicts

    except Exception as exc:
        logger.error(f"Failed to convert player objects to dictionaries: {exc}")
        raise


def save_players_data_to_csv(
    players_dataframe: pd.DataFrame,
    detailed_player_objects: List[Player],
    output_directory_path: Union[str, Path],
) -> None:
    """
    Save comprehensive player data to CSV file with validation and logging.

    This function converts Player objects to a structured DataFrame and saves
    the data to a CSV file, creating the output directory if needed.

    Args:
        players_dataframe (pd.DataFrame): Original player DataFrame (for reference)
        detailed_player_objects (List[Player]): List of Player objects with complete data
        output_directory_path (Union[str, Path]): Directory path where CSV will be saved

    Raises:
        ValueError: If no player objects provided or conversion fails
        IOError: If file writing fails
        OSError: If directory creation fails
    """
    logger = logging.getLogger("PlayerDataSaver")

    if not detailed_player_objects:
        raise ValueError("No player objects provided for saving")

    logger.info(f"Starting to save data for {len(detailed_player_objects)} players")

    try:
        # Convert Player objects to dictionaries for DataFrame creation
        logger.debug("Converting Player objects to dictionaries...")
        player_data_dicts = _convert_player_objects_to_dicts(detailed_player_objects)

        # Create DataFrame from player data
        logger.debug("Creating DataFrame from player data...")
        output_dataframe = pd.DataFrame(player_data_dicts)

        # Log DataFrame information
        _log_dataframe_information(output_dataframe)

        # Ensure output directory exists
        output_directory = Path(output_directory_path)
        _ensure_output_directory_exists(output_directory)

        # Save DataFrame to CSV
        csv_file_path = output_directory / "players.csv"
        _save_dataframe_to_csv(output_dataframe, csv_file_path)

        logger.info(
            f"Successfully saved player data:\n"
            f"  Players saved: {len(detailed_player_objects)}\n"
            f"  Output file: {csv_file_path}\n"
            f"  File size: {_get_file_size_mb(csv_file_path):.2f} MB"
        )

    except Exception as exc:
        logger.error(f"Failed to save player data: {exc}")
        raise
