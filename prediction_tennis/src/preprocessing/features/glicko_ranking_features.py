# SIMPLE RATING
import logging
from typing import Any, List, Tuple
import numpy as np
import pandas as pd
from tqdm import tqdm

from prediction_tennis.src.preprocessing.utils.ranking_systems import _update_player_glicko_rating, calculate_rating_movement_from_history


# Configure logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_INITIAL_RATING = 1500.0
DEFAULT_INITIAL_RD = 350.0
DEFAULT_Q_FACTOR = np.log(10) / 400  # Glicko system constant

def compute_glicko_ratings(matches_df: pd.DataFrame,
                           surface: str = "all",
                           initial_rating: float = DEFAULT_INITIAL_RATING,
                           initial_rating_deviation: float = DEFAULT_INITIAL_RD,
                           q_factor: float = DEFAULT_Q_FACTOR,
                           verbose: bool = False) -> np.ndarray:
    """
    Compute pre-match Glicko ratings for players using the Glicko rating system.
    
    The Glicko system is a method for assessing a player's strength in games
    of skill, such as chess or tennis. It extends the Elo rating system by
    incorporating rating deviation (uncertainty) into the calculations.
    
    Args:
        matches_df: DataFrame containing match details with required columns:
            - 'player1_id_factor': Numeric ID for player 1
            - 'player2_id_factor': Numeric ID for player 2
            - 'winner': Match winner (1 for player1, 2 for player2)
            - 'match_date': Date of the match
        surface: Surface type for matches (used for verbose output)
        initial_rating: Starting rating for new players
        initial_rating_deviation: Starting rating deviation for new players
        q_factor: Glicko system constant for calculations
        verbose: Enable detailed progress information
    
    Returns:
        2D numpy array of shape (n_matches, 2) containing pre-match ratings
        for [player1, player2] in each row
        
    Raises:
        ValueError: If required columns are missing from the DataFrame
        
    Example:
        >>> matches_df = pd.DataFrame({
        ...     'player1_id_factor': [0, 1],
        ...     'player2_id_factor': [1, 0],
        ...     'winner': [1, 2],
        ...     'match_date': ['2023-01-01', '2023-01-02']
        ... })
        >>> ratings = compute_glicko_ratings(matches_df)
        >>> ratings.shape
        (2, 2)
    """
    logger.info(f"Starting Glicko rating computation for {len(matches_df)} matches on surface: {surface}")
    
    if initial_rating <= 0          : raise ValueError("initial_rating must be positive")
    if initial_rating_deviation <= 0: raise ValueError("initial_rating_deviation must be positive")
    if q_factor <= 0                : raise ValueError("q_factor must be positive")

    # Validate required columns
    required_columns = ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date']
    missing_columns = [col for col in required_columns if col not in matches_df.columns]
    
    if missing_columns: raise ValueError(f"Missing required columns: {missing_columns}")

    # Determine total number of players
    max_player1_id = matches_df['player1_id_factor'].max()
    max_player2_id = matches_df['player2_id_factor'].max()
    total_players = int(max(max_player1_id, max_player2_id) + 1)
    
    logger.debug(f"Total players identified: {total_players}")

    # Initialize player ratings and rating deviations
    player_ratings = np.full(total_players, initial_rating, dtype=float)
    player_rating_deviations = np.full(total_players, initial_rating_deviation, dtype=float)

    # Initialize array to store pre-match ratings
    pre_match_ratings = np.zeros((len(matches_df), 2), dtype=float)

    # Set up progress bar
    progress_description = f"Processing Glicko ratings for {surface}"
    progress_bar = tqdm(matches_df.itertuples(), total=len(matches_df), desc=progress_description)
    
    for match_row in progress_bar:
        match_index = match_row.Index
        player1_id = match_row.player1_id_factor
        player2_id = match_row.player2_id_factor
        winner = match_row.winner
        match_date = match_row.match_date

        # Store pre-match ratings
        pre_match_ratings[match_index] = [player_ratings[player1_id], player_ratings[player2_id]]

        # Get current ratings and deviations
        player1_rating = player_ratings[player1_id]
        player2_rating = player_ratings[player2_id]

        player1_rd     = player_rating_deviations[player1_id]
        player2_rd     = player_rating_deviations[player2_id]

        # Determine match scores
        player1_score, player2_score = (1, 0) if winner == 1 else (0, 1)

        # Update Player 1's rating
        updated_p1_rating, updated_p1_rd = _update_player_glicko_rating(
                                player_rating   = player1_rating,
                                player_rd       = player1_rd,
                                opponent_rating = player2_rating,
                                opponent_rd     = player2_rd,
                                player_score    = player1_score,
                                q_factor        = q_factor)
        
        # Update Player 2's rating
        updated_p2_rating, updated_p2_rd = _update_player_glicko_rating(
                                player_rating   = player2_rating,
                                player_rd       = player2_rd,
                                opponent_rating = player1_rating,
                                opponent_rd     = player1_rd,
                                player_score    = player2_score,
                                q_factor        = q_factor)
        
        # Apply updates to global arrays
        player_ratings[player1_id] = updated_p1_rating
        player_ratings[player2_id] = updated_p2_rating

        player_rating_deviations[player1_id] = updated_p1_rd
        player_rating_deviations[player2_id] = updated_p2_rd

        # Update progress bar description if verbose
        if verbose:
            verbose_description = (
                f"Processing Glicko '{surface}' "
                f"(rating={initial_rating}, RD={initial_rating_deviation}, "
                f"q={q_factor:.6f}) - Date: '{match_date}'"
            )
            progress_bar.set_description(verbose_description)

    logger.info(f"Completed Glicko rating computation for {len(matches_df)} matches")
    return pre_match_ratings
