"""
Tournament data CSV saver module.

This module provides functionality to save tournament data to CSV files with
validation, logging, and error handling. It converts tournament data from
a list of dictionaries to a structured DataFrame and handles file operations safely.
"""

import logging
from pathlib import Path
from typing import Dict, List, Union
import pandas as pd

from prediction_tennis.src.utils.file_utils import (
    _ensure_output_directory_exists,
    _get_file_size_mb,
    _log_dataframe_information,
    _save_dataframe_to_csv,
)


def save_tournament_data_to_csv(
    tournament_data: List[Dict[str, str]],
    output_directory_path: Union[str, Path],
    filename: str = "tournament_data.csv",
) -> None:
    """
    Save tournament data to CSV file with validation and logging.

    This function converts tournament data from a list of dictionaries to a
    structured DataFrame and saves it to a CSV file, creating the output
    directory if needed.

    Parameters
    ----------
    tournament_data : List[Dict[str, str]]
        List of dictionaries containing tournament data
    output_directory_path : Union[str, Path]
        Directory path where CSV will be saved
    filename : str, optional
        Name of the output CSV file, by default "tournament_data.csv"

    Raises
    ------
    ValueError
        If no tournament data provided, data is invalid, or DataFrame creation fails
    IOError
        If file writing fails
    OSError
        If directory creation fails
    """
    logger = logging.getLogger("[SAVE TOURNAMENT]")

    # Validate input data
    if not tournament_data:
        error_msg = "No tournament data provided"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not isinstance(tournament_data, list):
        error_msg = "Tournament data must be a list of dictionaries"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        logger.debug(f"Processing {len(tournament_data)} tournament records...")

        # Create DataFrame from tournament data
        tournament_df = pd.DataFrame(tournament_data)

        if tournament_df.empty:
            error_msg = "Created DataFrame is empty"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Log DataFrame information for debugging
        _log_dataframe_information(tournament_df)

        # Ensure output directory exists
        output_directory = Path(output_directory_path)
        _ensure_output_directory_exists(output_directory)

        # Create full file path
        csv_file_path = output_directory / filename

        # Save DataFrame to CSV
        _save_dataframe_to_csv(tournament_df, csv_file_path)

        # Log success information
        file_size_mb = _get_file_size_mb(csv_file_path)
        logger.info(
            f"Successfully saved tournament data:\n"
            f"  Records saved: {len(tournament_data)}\n"
            f"  Columns: {list(tournament_df.columns)}\n"
            f"  Output file: {csv_file_path}\n"
            f"  File size: {file_size_mb:.2f} MB"
        )

    except pd.errors.EmptyDataError as e:
        error_msg = f"Failed to create DataFrame from tournament data: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    except (IOError, OSError) as e:
        error_msg = f"Failed to save tournament data to file: {e}"
        logger.error(error_msg)
        raise

    except Exception as e:
        error_msg = f"Unexpected error while saving tournament data: {e}"
        logger.error(error_msg)
        raise
