import logging
from pathlib import Path
from typing import Union
import pandas as pd
import io

def _ensure_output_directory_exists(directory_path: Union[str, Path]) -> None:
    """
    Create output directory if it doesn't exist.
    
    Args:
        directory_path (Union[str, Path]): Directory path to create
        
    Raises:
        OSError: If directory creation fails
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
    Save DataFrame to CSV file with error handling.
    
    Args:
        dataframe (pd.DataFrame): DataFrame to save
        csv_file_path (Union[str, Path]): Path where CSV will be saved
        
    Raises:
        IOError: If file writing fails
    """
    logger = logging.getLogger("CSVWriter")
    
    try:
        path = Path(csv_file_path)
        logger.debug(f"Saving DataFrame to CSV: {path}")
        
        # Save DataFrame with optimal settings
        dataframe.to_csv(path,
                         index=False,
                         encoding='utf-8',
                         na_rep='',  # Replace NaN with empty string
                         float_format='%.3f'  # Limit float precision
                         )
        
        logger.debug(f"Successfully wrote CSV file: {path}")
        
    except Exception as exc:
        logger.error(f"Failed to save DataFrame to CSV {csv_file_path}: {exc}")
        raise IOError(f"Cannot write CSV file {csv_file_path}: {exc}")


def _get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path (Union[str, Path]): Path to the file
        
    Returns:
        float: File size in MB
    """
    try:
        path = Path(file_path)
        if path.exists():
            return path.stat().st_size / (1024 * 1024)
        else:
            return 0.0
    except Exception:
        return 0.0


def _log_dataframe_information(dataframe: pd.DataFrame) -> None:
    """
    Log comprehensive information about the DataFrame.
    
    Args:
        dataframe (pd.DataFrame): DataFrame to analyze and log
    """
    logger = logging.getLogger("DataFrameAnalyzer")
    
    try:
        # Capture DataFrame info to string
        buffer = io.StringIO()
        dataframe.info(buf=buffer)
        dataframe_info = buffer.getvalue()
        
        # Log DataFrame statistics
        logger.info(f"DataFrame Summary:\n"
                    f"  Shape: {dataframe.shape}\n"
                    f"  Columns: {len(dataframe.columns)}\n"
                    f"  Memory usage: {dataframe.memory_usage(deep=True).sum() / 1024**2:.2f} MB\n"
                    f"  Non-null values per column:\n{dataframe.count().to_string()}"
                    )
        
        # Log detailed DataFrame info
        logger.debug(f"Detailed DataFrame Info:\n{dataframe_info}")
        
    except Exception as exc:
        logger.warning(f"Failed to log DataFrame information: {exc}")