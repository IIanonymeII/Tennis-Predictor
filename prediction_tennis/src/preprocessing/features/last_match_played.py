"""Module for computing recent match metrics for players based on historical data.

This module provides functionality to calculate either the count or ratio of matches
played by players in a specified period before each match, aiding in analysis or modeling tasks.
"""

import logging

import numpy as np
import pandas as pd
from tqdm import tqdm

from prediction_tennis.src.utils.core_error_functions import validate_type

logger = logging.getLogger("[LAST MATCH PLAYED]")

# Constant
DEFAULT_PERIOD_DAYS: int = 5
DEFAULT_USE_RATIO: bool = True


def compute_match_count_ratios(
    matches_df: pd.DataFrame,
    period_days: int = DEFAULT_PERIOD_DAYS,
    use_ratio: bool = DEFAULT_USE_RATIO,
    verbose: bool = False,
) -> np.ndarray:
    """
    Compute either the ratio or count of matches each player has played in the last
    'period_days' days before each match.

    Parameters
    ----------
    matches_df : pd.DataFrame
        DataFrame containing match details with columns:
        - 'player1_id_factor': Identifier for player 1.
        - 'player2_id_factor': Identifier for player 2.
        - 'match_date': Date or timestamp of the match.
        - 'timestamp': pandas Timestamp for the match.
    period_days : int, optional
        Number of days to look back for counting matches, by default 5.
    use_ratio : bool, optional
        If True, return match count as a ratio of matches per day (for LSTM or Linear models).
        If False, return raw match count (for Decision Tree models), by default
        True.
    verbose : bool, optional
        If True, log additional information during processing, by default False.

    Returns
    -------
    np.ndarray
        A 2D array where each row holds the pre-match values for player1 and player2.
        - If use_ratio=True: Returns match count divided by period_days (ratio between 0 and 1)
        - If use_ratio=False: Returns raw match count (integers)
    """
    if period_days <= 0:
        raise ValueError("period_days must be positive")
    validate_type(value=use_ratio, expected_type=bool, logger=logger)

    logger.info(
        f"Starting computation of recent match metrics for {period_days} days,use_ratio={use_ratio}"
    )

    # Ensure the DataFrame is sorted by timestamp for chronological processing
    matches_df = matches_df.copy()
    matches_df["original_index"] = matches_df.index
    sorted_df = matches_df.sort_values("timestamp").reset_index(drop=True)

    # Initialize a 2D array to record the metrics of both players before each match
    match_metrics: np.ndarray = np.zeros((len(matches_df), 2), dtype=float)

    # Dictionary to store sorted match timestamps for each player
    player_match_timestamps: dict[int, list[int]] = {}

    # Dictionary to store the left index for the sliding window for each player
    left_indices: dict[int, int] = {}

    # Process each match with a progress bar
    description_bar = f"Processing LAST {period_days} DAYS MATCH PLAY: Unknown"
    pbar = tqdm(sorted_df.iterrows(), total=len(sorted_df), desc=description_bar)

    for _, row in pbar:
        current_timestamp = row.timestamp
        player1_id = row.player1_id_factor
        player2_id = row.player2_id_factor
        match_date = row.match_date
        original_index = row.original_index

        # Initialize player's timestamp list and left index if not exists
        if player1_id not in player_match_timestamps:
            player_match_timestamps[player1_id] = []
            left_indices[player1_id] = 0
        if player2_id not in player_match_timestamps:
            player_match_timestamps[player2_id] = []
            left_indices[player2_id] = 0

        # Define the start timestamp for the time window (exclusive)
        start_timestamp = current_timestamp - pd.Timedelta(days=period_days)

        # Count matches for player1 in the last 'period_days' days
        p1_timestamps = player_match_timestamps[player1_id]
        left_idx_p1 = left_indices[player1_id]
        while left_idx_p1 < len(p1_timestamps) and p1_timestamps[left_idx_p1] < start_timestamp:
            left_idx_p1 += 1
        left_indices[player1_id] = left_idx_p1
        p1_count = len(p1_timestamps) - left_idx_p1

        # Count matches for player2 in the last 'period_days' days
        p2_timestamps = player_match_timestamps[player2_id]
        left_idx_p2 = left_indices[player2_id]
        while left_idx_p2 < len(p2_timestamps) and p2_timestamps[left_idx_p2] < start_timestamp:
            left_idx_p2 += 1
        left_indices[player2_id] = left_idx_p2
        p2_count = len(p2_timestamps) - left_idx_p2

        # Calculate either ratio or count based on use_ratio parameter
        if use_ratio:
            p1_metric = p1_count / period_days if period_days > 0 else 0.0
            p2_metric = p2_count / period_days if period_days > 0 else 0.0
        else:
            p1_metric = p1_count
            p2_metric = p2_count

        # Record the pre-match metrics using original index
        match_metrics[original_index, 0] = p1_metric
        match_metrics[original_index, 1] = p2_metric

        # Append the current match timestamp to both players' lists (since processing in order, remains sorted)
        p1_timestamps.append(current_timestamp)
        p2_timestamps.append(current_timestamp)

        # Update progress bar description and log if verbose
        metric_type = "RATIO" if use_ratio else "COUNT"
        if verbose:
            pbar.set_description(
                f"Processing {metric_type} LAST {period_days} DAYS MATCH PLAY: {match_date}"
            )
            logger.info(
                f"Processed {metric_type} for match on {match_date}: P1={p1_metric}, P2={p2_metric}"
            )

    logger.info("Computation of recent match metrics completed")
    return match_metrics
