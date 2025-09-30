"""
Module for computing recent match activity metrics for tennis players.

This module provides functionality to calculate player activity in terms of matches played
or matches won during a defined period prior to each match. These metrics can be expressed
as either raw counts or normalized ratios. The resulting features are useful for modeling
match outcomes or analyzing player form.
"""

import logging
from typing import Literal

import numpy as np
import pandas as pd
from tqdm import tqdm

from prediction_tennis.src.utils.core_error_functions import validate_type

# --------------------------------------------------------------------------------------------------
# Logging configuration
# --------------------------------------------------------------------------------------------------
logger = logging.getLogger("[LAST MATCH METRICS]")

# --------------------------------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------------------------------
DEFAULT_PERIOD_DAYS: int = 5
DEFAULT_USE_RATIO: bool = True


def _compute_recent_metrics(
    matches_df: pd.DataFrame,
    period_days: int,
    use_ratio: bool,
    mode: Literal["played", "won"],
    verbose: bool = False,
) -> np.ndarray:
    """
    Internal function to compute recent match activity metrics for players.

    Parameters
    ----------
    matches_df : pd.DataFrame
        DataFrame containing match details with required columns:
        - 'player1_id_factor': Identifier for player 1.
        - 'player2_id_factor': Identifier for player 2.
        - 'winner_id': Identifier of the winning player (only required if mode="won").
        - 'timestamp': pandas Timestamp of the match.
        - 'match_date': Original date of the match.
    period_days : int
        Number of days to look back for activity calculation.
    use_ratio : bool
        If True, return counts normalized by period_days. Otherwise return raw counts.
    mode : {"played", "won"}
        Type of metric to compute:
        - "played": number of matches played in the period.
        - "won": number of matches won in the period.
    verbose : bool, optional
        If True, log detailed progress for each match.

    Returns
    -------
    np.ndarray
        2D array where each row corresponds to a match. The two columns represent player 1
        and player 2 metrics respectively.

    Raises
    ------
    ValueError
        If `period_days` is not strictly positive.
    """
    if period_days <= 0:
        raise ValueError("period_days must be positive")
    validate_type(value=use_ratio, expected_type=bool, logger=logger)

    logger.info(
        "Starting computation of '%s' metrics for last %d days (use_ratio=%s)",
        mode,
        period_days,
        use_ratio,
    )

    # Sort by timestamp for chronological processing
    matches_df = matches_df.copy()
    matches_df["original_index"] = matches_df.index
    sorted_matches = matches_df.sort_values("timestamp").reset_index(drop=True)

    # Initialize result array
    metrics: np.ndarray = np.zeros((len(matches_df), 2), dtype=float)

    # History of timestamps per player
    player_histories: dict[int, list[pd.Timestamp]] = {}
    # Left index for sliding window per player
    left_indices: dict[int, int] = {}

    description = f"Processing LAST {period_days} DAYS MATCH {mode.upper()}: Unknown"
    pbar = tqdm(sorted_matches.iterrows(), total=len(sorted_matches), desc=description)

    for _, row in pbar:
        current_ts = row.timestamp
        player1_id = row.player1_id_factor
        player2_id = row.player2_id_factor
        match_winner = row.winner
        match_date = row.match_date
        original_idx = row.original_index

        # Initialize history and index if not present
        for player_id in (player1_id, player2_id):
            if player_id not in player_histories:
                player_histories[player_id] = []
                left_indices[player_id] = 0

        # Define time window
        start_ts = current_ts - pd.Timedelta(days=period_days)

        # --- Player 1 ---
        p1_history = player_histories[player1_id]
        left_idx_p1 = left_indices[player1_id]
        while left_idx_p1 < len(p1_history) and p1_history[left_idx_p1] < start_ts:
            left_idx_p1 += 1
        left_indices[player1_id] = left_idx_p1
        p1_count = len(p1_history) - left_idx_p1

        # --- Player 2 ---
        p2_history = player_histories[player2_id]
        left_idx_p2 = left_indices[player2_id]
        while left_idx_p2 < len(p2_history) and p2_history[left_idx_p2] < start_ts:
            left_idx_p2 += 1
        left_indices[player2_id] = left_idx_p2
        p2_count = len(p2_history) - left_idx_p2

        # Normalize if required
        if use_ratio:
            p1_metric = p1_count / period_days
            p2_metric = p2_count / period_days
        else:
            p1_metric = p1_count
            p2_metric = p2_count

        # Record results
        metrics[original_idx, 0] = p1_metric
        metrics[original_idx, 1] = p2_metric

        # Update player history
        if mode == "played":
            player_histories[player1_id].append(current_ts)
            player_histories[player2_id].append(current_ts)
        elif mode == "won":
            if match_winner == 1:
                player_histories[player1_id].append(current_ts)
            elif match_winner == 2:
                player_histories[player2_id].append(current_ts)
            else:
                logger.warning(
                    "Unexpected match_winner value (%s) at index %s",
                    match_winner,
                    original_idx,
                )

        # Verbose logging
        if verbose:
            metric_type = "RATIO" if use_ratio else "COUNT"
            pbar.set_description(
                f"Processing {metric_type} LAST {period_days} DAYS MATCH {mode.upper()}: {match_date}"
            )
            logger.debug(
                "%s metrics for match %s: P1=%.3f, P2=%.3f",
                mode.capitalize(),
                match_date,
                p1_metric,
                p2_metric,
            )

    logger.info("Completed computation of recent '%s' metrics", mode)
    return metrics


def compute_match_count_ratios(
    matches_df: pd.DataFrame,
    period_days: int = DEFAULT_PERIOD_DAYS,
    use_ratio: bool = DEFAULT_USE_RATIO,
    verbose: bool = False,
) -> np.ndarray:
    """
    Compute metrics for matches played in a recent time window.

    Parameters
    ----------
    matches_df : pd.DataFrame
        DataFrame containing match details with required columns:
        - 'player1_id_factor': Identifier for player 1.
        - 'player2_id_factor': Identifier for player 2.
        - 'timestamp': pandas Timestamp of the match.
        - 'match_date': Original date of the match.
    period_days : int, optional
        Number of days to look back, by default 5.
    use_ratio : bool, optional
        If True, return counts normalized by period_days, by default True.
    verbose : bool, optional
        If True, log detailed progress, by default False.

    Returns
    -------
    np.ndarray
        2D array of pre-match played metrics for player 1 and player 2.
    """
    return _compute_recent_metrics(
        matches_df, period_days, use_ratio, mode="played", verbose=verbose
    )


def compute_win_count_ratios(
    matches_df: pd.DataFrame,
    period_days: int = DEFAULT_PERIOD_DAYS,
    use_ratio: bool = DEFAULT_USE_RATIO,
    verbose: bool = False,
) -> np.ndarray:
    """
    Compute metrics for matches won in a recent time window.

    Parameters
    ----------
    matches_df : pd.DataFrame
        DataFrame containing match details with required columns:
        - 'player1_id_factor': Identifier for player 1.
        - 'player2_id_factor': Identifier for player 2.
        - 'winner_id': Identifier of the winning player.
        - 'timestamp': pandas Timestamp of the match.
        - 'match_date': Original date of the match.
    period_days : int, optional
        Number of days to look back, by default 5.
    use_ratio : bool, optional
        If True, return counts normalized by period_days, by default True.
    verbose : bool, optional
        If True, log detailed progress, by default False.

    Returns
    -------
    np.ndarray
        2D array of pre-match win metrics for player 1 and player 2.
    """
    return _compute_recent_metrics(matches_df, period_days, use_ratio, mode="won", verbose=verbose)
