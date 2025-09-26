# SIMPLE RATING
import logging
from typing import List, Tuple
import numpy as np
import pandas as pd
from tqdm import tqdm
import trueskill

from prediction_tennis.src.preprocessing.utils.ranking_systems import calculate_rating_movement_from_history

# Configure logging
logger = logging.getLogger("[TRUESKILL RANTING]")


# TRUESKILL RANKING
def compute_trueskill_ratings(matches_df: pd.DataFrame,
                              surface: str = "all",
                              verbose: bool = False) -> np.ndarray:    
    """
    Compute pre-match TrueSkill ratings for all players across all matches.

    This function processes matches chronologically, recording each player's
    TrueSkill rating (mu value) before each match, then updates their ratings
    based on the match outcome using TrueSkill's head-to-head algorithm.

    Args:
        matches_df: DataFrame containing match data with required columns:
            - 'player1_id_factor': Factorized ID for player 1
            - 'player2_id_factor': Factorized ID for player 2
            - 'winner': Match winner (1 for player 1, 2 for player 2)
            - 'match_date': Date or timestamp of the match
        surface: Surface type identifier for logging purposes
        verbose: Whether to show detailed progress information

    Returns:
        2D numpy array of shape (num_matches, 2) containing pre-match
        TrueSkill mu values for [player1, player2] in each match

    Raises:
        ValueError: If required columns are missing from matches_df
        TypeError: If matches_df is not a pandas DataFrame
    """
    logger.info(f"Starting TrueSkill rating computation for {len(matches_df)} matches")
    
    # Validate input
    if not isinstance(matches_df, pd.DataFrame): raise TypeError("matches_df must be a pandas DataFrame")

    required_columns = ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date']
    missing_columns = [col for col in required_columns if col not in matches_df.columns]
    if missing_columns: raise ValueError(f"Missing required columns: {missing_columns}")
    

    # Calculate total number of unique players
    max_player_id: int = max(
        matches_df['player1_id_factor'].max(),
        matches_df['player2_id_factor'].max()
        )    
    total_players = int(max_player_id + 1)

    logger.info(f"Initializing TrueSkill ratings for {total_players} players")

    # Initialize TrueSkill ratings for each player using default settings.
    # Each player's rating is represented as a trueskill.Rating object.
    player_ratings: list[trueskill.Rating] = [trueskill.Rating() for _ in range(total_players)]

    # Prepare an array to store pre-match ratings (mu values) for each match.
    pre_match_ratings: np.ndarray = np.zeros((len(matches_df), 2), dtype=float)

    # Configure progress bar description
    progress_desc = f"Processing '{surface}' TrueSkill ratings"
    if not verbose:
        progress_desc = "Processing TrueSkill ratings"

    # Process each match chronologically
    progress_bar = tqdm(
        matches_df.itertuples(),
        total=len(matches_df),
        desc=progress_desc
    )

    for match_data in progress_bar:
        match_index = match_data.Index
        player1_id = match_data.player1_id_factor
        player2_id = match_data.player2_id_factor
        winner = match_data.winner
        match_date = match_data.match_date  # Could be str, datetime, etc.

        # Record pre-match TrueSkill mu values
        pre_match_ratings[match_index, 0] = player_ratings[player1_id].mu
        pre_match_ratings[match_index, 1] = player_ratings[player2_id].mu

        # Update ratings based on match outcome
        if winner == 1:
            # Player 1 wins
            updated_rating1, updated_rating2 = trueskill.rate_1vs1(
                player_ratings[player1_id], player_ratings[player2_id]
            )
        elif winner == 2:
            # Player 2 wins
            updated_rating2, updated_rating1 = trueskill.rate_1vs1(
                player_ratings[player2_id], player_ratings[player1_id]
            )
        else:
            logger.error(f"Invalid winner value {winner} at match {match_index}")
            continue

        # Update player ratings with new values
        player_ratings[player1_id] = updated_rating1
        player_ratings[player2_id] = updated_rating2
        
        # Update progress bar with current match date if verbose
        if verbose:
            progress_bar.set_description(f"Processing '{surface}' TrueSkill ratings: '{match_date}'")

    logger.info("TrueSkill rating computation completed successfully")
    return pre_match_ratings

def compute_trueskill_movement(matches_df: pd.DataFrame,
                               matches_lookback: int = 5) -> np.ndarray:
    """
    Calculate TrueSkill rating movements for each match based on historical performance.

    For each match, this function computes how much each player's TrueSkill rating
    has changed compared to their rating 'matches_lookback' matches ago. This
    provides insight into recent performance trends.

    Args:
        matches_df: DataFrame containing match data with required columns:
            - 'player1_id_factor': Factorized ID for player 1
            - 'player2_id_factor': Factorized ID for player 2
            - 'match_date': Date or timestamp of the match
            - 'trueskill_p1': Pre-match TrueSkill rating for player 1
            - 'trueskill_p2': Pre-match TrueSkill rating for player 2
        matches_lookback: Number of matches to look back for movement calculation

    Returns:
        2D numpy array of shape (num_matches, 2) containing rating movements
        for [player1, player2] in each match

    Raises:
        ValueError: If required columns are missing from matches_df
        TypeError: If matches_df is not a pandas DataFrame
    """
    logger.info("Computing TrueSkill movements for {len(matches_df)} matches with {matches_lookback} match lookback")

    if matches_lookback <= 0: raise ValueError("lookback_matches must be positive")

    # Validate input
    if not isinstance(matches_df, pd.DataFrame): raise TypeError("matches_df must be a pandas DataFrame")

    required_columns = ['player1_id_factor', 'player2_id_factor', 'match_date', 'trueskill_p1', 'trueskill_p2']
    missing_columns  = [col for col in required_columns if col not in matches_df.columns]
    if missing_columns: raise ValueError(f"Missing required columns: {missing_columns}")

    # Ensure 'match_date' column is in datetime format
    matches_df['match_date'] = pd.to_datetime(matches_df['match_date'])

    # Calculate total number of unique players
    max_player_id = max(
        matches_df['player1_id_factor'].max(),
        matches_df['player2_id_factor'].max()
        )
    total_players = int(max_player_id + 1)

    logger.info(f"Tracking rating history for {total_players} players")

    # Initialize rating history for each player as an empty list
    player_rating_histories: List[List[Tuple[pd.Timestamp, float]]] = [[] for _ in range(total_players)]

    # Initialize array to store rating movements
    rating_movements = np.zeros((len(matches_df), 2), dtype=np.float64)

    # Process matches chronologically with progress tracking
    progress_desc = f"Computing {matches_lookback}-match TrueSkill movements"

    # Process matches with a progress bar for visual feedback
    for match_data in tqdm(matches_df.itertuples(), total=len(matches_df), desc=progress_desc):
        match_index = match_data.Index
        player1_id = match_data.player1_id_factor
        player2_id = match_data.player2_id_factor
        match_date = match_data.match_date
        player1_current_rating = match_data.trueskill_p1 # Current pre-match rating for player 1
        player2_current_rating = match_data.trueskill_p2 # Current pre-match rating for player 2

        # Calculate rating movements for both players
        player1_movement = calculate_rating_movement_from_history(
            rating_history           = player_rating_histories[player1_id],
            current_pre_match_rating = player1_current_rating,
            matches_lookback         = matches_lookback
        )

        player2_movement = calculate_rating_movement_from_history(
            rating_history           = player_rating_histories[player2_id],
            current_pre_match_rating = player2_current_rating,
            matches_lookback         = matches_lookback
        )
        
        # Store the movements
        rating_movements[match_index, 0] = player1_movement
        rating_movements[match_index, 1] = player2_movement

        # Update rating histories with current pre-match ratings
        player_rating_histories[player1_id].append((match_date, player1_current_rating))
        player_rating_histories[player2_id].append((match_date, player2_current_rating))

    logger.info("TrueSkill movement computation completed successfully")
    return rating_movements
