"""
Module for computing rating movements in tennis matches.

This module provides functionality to calculate the rating movement for each player
by comparing their current rating with their rating from a specified number of matches ago.
"""
import logging
from typing import List, Tuple

import numpy as np
import pandas as pd
from tqdm import tqdm

from prediction_tennis.src.preprocessing.utils.ranking_systems import (
    calculate_rating_movement_from_history,
)

logger = logging.getLogger("[MOVEMENT]")

# Constants
DEFAULT_LOOKBACK_MATCHES = 5
RATING_PREFIX = "rating"


def compute_rating_movement(
    matches_df: pd.DataFrame,
    lookback_matches: int = DEFAULT_LOOKBACK_MATCHES,
    rating_prefix: str = RATING_PREFIX,
) -> np.ndarray:
    """
    Calculate rating movement for each match using the specified rating type from 'lookback_matches' games ago.

    This function iterates through matches and computes the rating movement for each player
    by comparing their current rating with the rating from a specified number of matches ago.
    It maintains a history of ratings for each player to enable this calculation.

    Parameters
    ----------
    matches_df : pd.DataFrame
        DataFrame with match info, including player IDs, dates, and pre-match ratings.
    lookback_matches : int, optional
        How many matches back to consider for the previous rating (default: 5).
    rating_prefix : str, optional
        Prefix for the rating type (e.g., 'elo', 'glicko', 'trueskill') (default: 'rating').

    Returns
    -------
    np.ndarray
        A 2D numpy array of shape (n_matches, 2), each row is the movement for player 1 and player 2.

    Raises
    ------
    ValueError
        If lookback_matches is not positive.
    """
    if lookback_matches <= 0:
        raise ValueError("lookback_matches must be positive")

    # Convert match date to datetime if not already
    matches_df["match_date"] = pd.to_datetime(matches_df["match_date"])

    # Calculate total number of unique players
    total_players = int(
        max(matches_df["player1_id_factor"].max(), matches_df["player2_id_factor"].max()) + 1
    )

    # Initialize rating history for each player
    # Each player gets a list of (timestamp, rating) tuples
    player_rating_history: List[List[Tuple[pd.Timestamp, float]]] = [
        [] for _ in range(total_players)
    ]

    # Initialize result array to store rating movements
    match_movements = np.zeros((len(matches_df), 2), dtype=float)

    # Define column names for player ratings based on prefix
    col_p1 = f"{rating_prefix}_p1"
    col_p2 = f"{rating_prefix}_p2"

    # Process each match with progress tracking
    for row in tqdm(
        matches_df.itertuples(),
        total=len(matches_df),
        desc=f"Calculating last {lookback_matches} movements ({rating_prefix})",
    ):
        match_index = row.Index
        player1_id = int(row.player1_id_factor)
        player2_id = int(row.player2_id_factor)
        match_date = row.match_date

        # Get current pre-match ratings for both players
        current_rating_player1 = getattr(row, col_p1)
        current_rating_player2 = getattr(row, col_p2)

        # Calculate rating movement for player 1
        movement_player1 = calculate_rating_movement_from_history(
            rating_history=player_rating_history[player1_id],
            current_pre_match_rating=current_rating_player1,
            matches_lookback=lookback_matches,
        )

        # Calculate rating movement for player 2
        movement_player2 = calculate_rating_movement_from_history(
            rating_history=player_rating_history[player2_id],
            current_pre_match_rating=current_rating_player2,
            matches_lookback=lookback_matches,
        )

        # Store movements in result array
        match_movements[match_index, 0] = movement_player1
        match_movements[match_index, 1] = movement_player2

        # Update rating history for both players with current match data
        player_rating_history[player1_id].append((match_date, current_rating_player1))
        player_rating_history[player2_id].append((match_date, current_rating_player2))

    logger.info(f"Successfully computed rating movements for {len(matches_df)} matches")
    return match_movements
