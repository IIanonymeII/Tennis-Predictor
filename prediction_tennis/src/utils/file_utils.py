"""
Module for managing CSV files and DataFrame operations.

Includes functions for:
- Ensuring output directories exist
- Saving DataFrames to CSV
- Logging DataFrame information
- Loading CSV files from directories
- Calculating file sizes
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Union
import pandas as pd
import io


def _ensure_output_directory_exists(directory_path: Union[str, Path]) -> None:
    """
    Create the output directory if it does not exist.

    Parameters
    ----------
    directory_path : Union[str, Path]
        Path to the directory to create.

    Raises
    ------
    OSError
        If the directory creation fails.
    """
    logger = logging.getLogger("DirectoryManager")

    try:
        path = Path(directory_path)
        if not path.exists():
            logger.info(f"Creating output directory: {path}")
            path.mkdir(parents=True, exist_ok=True)
        else:
            logger.debug(f"Output directory already exists: {path}")

    except Exception as exc:
        logger.error(f"Failed to create output directory {directory_path}: {exc}")
        raise OSError(f"Cannot create directory {directory_path}: {exc}")


def _save_dataframe_to_csv(dataframe: pd.DataFrame, csv_file_path: Union[str, Path]) -> None:
    """
    Save a DataFrame to a CSV file with proper error handling.

    Parameters
    ----------
    dataframe : pd.DataFrame
        DataFrame to save.
    csv_file_path : Union[str, Path]
        Path to save the CSV file.

    Raises
    ------
    IOError
        If writing to the CSV file fails.
    """
    logger = logging.getLogger("CSVWriter")

    try:
        path = Path(csv_file_path)
        logger.debug(f"Saving DataFrame to CSV: {path}")

        dataframe.to_csv(
            path,
            index=False,
            encoding="utf-8",
            na_rep="",  # Replace NaN with empty string
            float_format="%.6f",  # Limit float precision
        )

        logger.debug(f"Successfully wrote CSV file: {path}")

    except Exception as exc:
        logger.error(f"Failed to save DataFrame to CSV {csv_file_path}: {exc}")
        raise IOError(f"Cannot write CSV file {csv_file_path}: {exc}")


def _get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Return the size of a file in megabytes.

    Parameters
    ----------
    file_path : Union[str, Path]
        Path to the file.

    Returns
    -------
    float
        File size in megabytes. Returns 0.0 if the file does not exist or
        an error occurs.
    """
    try:
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size / (1024 * 1024)
        return 0.0
    except Exception:
        return 0.0


def _log_dataframe_information(dataframe: pd.DataFrame) -> None:
    """
    Log detailed information about a DataFrame.

    Parameters
    ----------
    dataframe : pd.DataFrame
        DataFrame to analyze and log.
    """
    logger = logging.getLogger("DataFrameAnalyzer")

    try:
        buffer = io.StringIO()
        dataframe.info(buf=buffer)
        dataframe_info = buffer.getvalue()

        logger.info(
            f"DataFrame Summary:\n"
            f"  Shape: {dataframe.shape}\n"
            f"  Columns: {len(dataframe.columns)}\n"
            f"  Memory usage: {dataframe.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n"
            f"  Non-null values per column:\n{dataframe.count().to_string()}"
        )
        logger.debug(f"Detailed DataFrame Info:\n{dataframe_info}")

    except Exception as exc:
        logger.warning(f"Failed to log DataFrame information: {exc}")


def load_csv_files_from_directory(
    directory_path: Union[str, Path], pattern: str
) -> List[pd.DataFrame]:
    """
    Load all CSV files from a directory that match a given filename pattern.
    Ensures the directory exists before loading files.

    Parameters
    ----------
    directory_path : Union[str, Path]
        Path to the directory containing CSV files.
    pattern : str
        Pattern to match file names (e.g., 'tournament_' for files starting
        with 'tournament_').

    Returns
    -------
    List[pd.DataFrame]
        List of loaded DataFrames.

    Raises
    ------
    FileNotFoundError
        If the directory does not exist and cannot be created.
    """
    logger = logging.getLogger("CSVLoader")
    dir_path = Path(directory_path)

    # Ensure the directory exists
    _ensure_output_directory_exists(dir_path)

    csv_files = [
        file_name
        for file_name in os.listdir(dir_path)
        if file_name.startswith(pattern) and file_name.endswith(".csv")
    ]

    if not csv_files:
        logger.warning(f"No CSV files matching pattern '{pattern}' found in {dir_path}")

    dataframes = []
    for file_name in csv_files:
        file_path = dir_path / file_name
        df = pd.read_csv(file_path, low_memory=False)
        dataframes.append(df)
        logger.info(f"Loaded CSV file: {file_name}")

    return dataframes


def combine_dataframes(dataframes: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """
    Combine a list of DataFrames into a single DataFrame.

    Parameters
    ----------
    dataframes : List[pd.DataFrame]
        List of DataFrames to combine

    Returns
    -------
    Optional[pd.DataFrame]
        Combined DataFrame or None if input list is empty
    """
    logger = logging.getLogger("CombinedDF")
    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)
        logger.info(f"Successfully combined {len(dataframes)} DataFrames")
        _log_dataframe_information(dataframe=combined_df)
        return combined_df
    else:
        logger.warning("No DataFrames to combine")
        return None
