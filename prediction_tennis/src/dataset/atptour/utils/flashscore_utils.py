"""
FlashScore data extraction module.

This module provides functionality to extract and combine tournament data
from multiple FlashScore CSV files into a single DataFrame.
"""

import logging
import os
import pandas as pd


# Configure logging
logger = logging.getLogger("[FLASCORE UTILS]")


def extract_df_from_flashscore(folder_path: str) -> pd.DataFrame:
    """
    Extract and combine tournament data from Flashscore CSV files.

    This function reads all CSV files matching the pattern "tournament_*.csv"
    from the specified folder and concatenates them into a single DataFrame.

    Parameters
    ----------
    folder_path : str
        Path to the folder containing Flashscore CSV files

    Returns
    -------
    pd.DataFrame
        Combined DataFrame containing all tournament data,
        or empty DataFrame if no files are found

    Raises
    ------
    FileNotFoundError
        If the specified folder does not exist
    PermissionError
        If there are insufficient permissions to read the folder or files
    """
    # Get all CSV files that match the pattern "tournament_xx.csv"
    flashscore_csv_files = [
        f for f in os.listdir(folder_path) if f.startswith("tournament_") and f.endswith(".csv")
    ]

    # Initialize an empty list to store DataFrames
    df_flashscore = []

    # Read and concatenate all matching CSV files
    for file in flashscore_csv_files:
        file_path = os.path.join(folder_path, file)
        try:
            df = pd.read_csv(
                file_path, low_memory=False
            )  # Adjust parameters if needed (e.g., encoding, delimiter)
            df_flashscore.append(df)
            logger.debug(f"Successfully read file: {file}")
        except Exception as e:
            logger.error(f"Error reading file {file}: {e}")
            continue

    # Concatenate all DataFrames into one
    if df_flashscore:
        combined_flashscore_df = pd.concat(df_flashscore, ignore_index=True)
        logger.info(f"Successfully combined {len(flashscore_csv_files)} CSV files")
        return combined_flashscore_df
    else:
        logger.warning("No matching CSV files found")
        return pd.DataFrame()  # Return empty DataFrame instead of empty list
