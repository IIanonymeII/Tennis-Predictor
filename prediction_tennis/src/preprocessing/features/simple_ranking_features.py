# SIMPLE RATING
import logging
import math
from typing import Any
import numpy as np
import pandas as pd
from tqdm import tqdm

from prediction_tennis.src.preprocessing.utils.ranking_systems import _apply_transformation, _calculate_update_values

logger = logging.getLogger("[SIMPLE RANKING]")


# Constants
DEFAULT_WIN_STEP  = 1.0
DEFAULT_LOSE_STEP = 1.0
DEFAULT_TRANSFORMATION_METHOD = "power"
DEFAULT_TRANSFORMATION_FACTOR = 1.0


"""
Simple ranking system for player match outcomes.

This module provides functions to compute player rankings based on match
outcomes using customizable update steps and various transformation methods.
"""

import logging
import math
from typing import Any, Union
import numpy as np
import pandas as pd
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_WIN_STEP = 1.0
DEFAULT_LOSE_STEP = 1.0
DEFAULT_TRANSFORMATION_METHOD = "power"
DEFAULT_TRANSFORMATION_FACTOR = 1.0

# Valid transformation methods
VALID_TRANSFORMATION_METHODS = [
    "power", "exp", "log", "power-log", "power-exp", "log-exp",
    "log-power", "exp-log", "exp-power"]

# SIMPLE RATING
def compute_simple_ranking(matches_df           : pd.DataFrame,
                           surface              : str   = "all",
                           win_step             : float = DEFAULT_WIN_STEP,
                           lose_step            : float = DEFAULT_LOSE_STEP,
                           transformation_method: str   = DEFAULT_TRANSFORMATION_METHOD,
                           transformation_factor: float = DEFAULT_TRANSFORMATION_FACTOR,
                           verbose              : bool  = False) -> np.ndarray:
    """
    Compute player rankings based on match outcomes using customizable 
    update steps and transformation methods.
    
    For each match, this function records the current scores of both players
    before the match, then updates their scores based on the match result.
    The update steps (win and lose) can be transformed using various
    mathematical functions.
    
    Args:
        matches_df: DataFrame containing match details with columns:
            - 'player1_id_factor': Identifier for player 1
            - 'player2_id_factor': Identifier for player 2  
            - 'winner': Winning player (1 for player1, 2 for player2)
            - 'match_date': Date or timestamp of the match
        surface: Playing surface identifier for display purposes
        win_step: Base score increment for the winning player
        lose_step: Base score decrement for the losing player
        transformation_method: Method to transform update steps. Options:
            - "power": Use step ** transformation_factor
            - "exp": Use math.exp(step * transformation_factor)
            - "log": Use math.log(step + transformation_factor)
            - Hybrid methods: "power-log", "power-exp", "log-exp",
              "log-power", "exp-log", "exp-power"
        transformation_factor: Factor used in the transformation
        verbose: Whether to display detailed progress information
        
    Returns:
        2D numpy array where each row contains pre-match scores 
        for player1 and player2
        
    Raises:
        ValueError: If transformation method is invalid or would cause
                   mathematical errors (e.g., log of negative number)
    """
    logger.info(f"Computing simple ranking for surface '{surface}' using method '{transformation_method}'")
    if win_step              <= 0 : raise ValueError("win_step must be positive")
    if lose_step             <= 0 : raise ValueError("lose_step must be positive")
    if transformation_factor <= 0 : raise ValueError("transformation_factor must be positive")
    
    if transformation_method not in VALID_TRANSFORMATION_METHODS:
        raise ValueError(f"transformation_method must be in {VALID_TRANSFORMATION_METHODS}")
    
    # Validate inputs
    required_columns = ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date']
    missing_columns  = [col for col in required_columns if col not in matches_df.columns]
    if missing_columns: raise ValueError(f"Missing required columns: {missing_columns}")

    # Determine total number of players
    max_player_id = max(matches_df["player1_id_factor"].max(),matches_df["player2_id_factor"].max())
    num_players = int(max_player_id + 1)
    logger.debug(f"Number of players: {num_players}")

    # Initialize player scores and match rankings arrays
    player_scores = np.zeros(num_players, dtype=float)
    match_rankings = np.zeros((len(matches_df), 2), dtype=float)

    # Calculate transformed update values
    update_win, update_lose = _calculate_update_values(win_step, lose_step, transformation_method, transformation_factor)

    logger.info(f"Update values - Win: {update_win:.4f}, Lose: {update_lose:.4f}")

    # Process each match
    progress_bar = tqdm(matches_df.itertuples(), total=len(matches_df), desc="Processing simple ranking")
    for row in progress_bar:
        match_index = row.Index
        player1_id  = row.player1_id_factor
        player2_id  = row.player2_id_factor
        winner      = row.winner
        match_date  = row.match_date
        
        # Record current scores before updating
        match_rankings[match_index, 0] = player_scores[player1_id]
        match_rankings[match_index, 1] = player_scores[player2_id]
        
        # Update scores based on match outcome
        if winner == 1:
            player_scores[player1_id] += update_win
            player_scores[player2_id] -= update_lose
        elif winner == 2:
            player_scores[player1_id] -= update_lose
            player_scores[player2_id] += update_win
        else:
            logger.warning(f"Invalid winner value: {winner} at match {match_index}")
        
        if verbose:
            progress_description = (
                f"Processing '{surface}' "
                f"('{transformation_method}'({transformation_factor}) "
                f"win={win_step} lose={lose_step}): '{match_date}'"
            )
            progress_bar.set_description(progress_description)
    
    logger.info(f"Processed {len(matches_df)} matches successfully")
    return match_rankings

def compute_transformed_winloss_rankings(matches_df: pd.DataFrame,
                                         surface: str = "all",
                                         win_step: float = DEFAULT_WIN_STEP,
                                         lose_step: float = DEFAULT_LOSE_STEP,
                                         transformation_method: str = DEFAULT_TRANSFORMATION_METHOD,
                                         verbose: bool = False
                                         ) -> np.ndarray:
    """
    Compute match-by-match transformed player ratings based on win-loss
    records with on-the-fly transformations.
    
    This function maintains separate win and loss counters for each player
    and applies transformations to compute ratings as:
    rating = transform(wins) - transform(losses)
    
    Args:
        matches_df: DataFrame containing match history
        surface: Surface type for display purposes only
        win_step: Base increment for winners
        lose_step: Base increment for losers  
        transformation_method: Transformation method or hybrid method
            (e.g., "exp-log", "power-log", etc.)
            
    Returns:
        2D numpy array of shape (num_matches, 2) with transformed ratings
        for player1 and player2 before each match
        
    Raises:
        ValueError: If parameters are invalid
    """
    logger.info(f"Computing transformed win-loss rankings for surface '{surface}' using method '{transformation_method}'")
    if win_step  <= 0 : raise ValueError("win_step must be positive")
    if lose_step <= 0 : raise ValueError("lose_step must be positive")
    
    if transformation_method not in VALID_TRANSFORMATION_METHODS:
        raise ValueError(f"transformation_method must be in {VALID_TRANSFORMATION_METHODS}")
    
    # Validate inputs
    required_columns = ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date']
    missing_columns  = [col for col in required_columns if col not in matches_df.columns]
    if missing_columns: raise ValueError(f"Missing required columns: {missing_columns}")

    # Determine number of players
    max_player_id = max(matches_df["player1_id_factor"].max(), matches_df["player2_id_factor"].max())
    num_players = int(max_player_id + 1)

    # Initialize counters and results array
    win_counts     = np.zeros(num_players, dtype=float)
    lose_counts    = np.zeros(num_players, dtype=float)
    match_rankings = np.zeros((len(matches_df), 2), dtype=float)

    # Parse transformation methods for wins and losses
    if "-" in transformation_method:
        win_transform_method, lose_transform_method = transformation_method.split("-")
    else:
        win_transform_method = lose_transform_method = transformation_method

    # Process each match
    progress_bar = tqdm(matches_df.itertuples(), total=len(matches_df), desc="Computing transformed win-loss rankings")

    for row in progress_bar:
        match_index = row.Index
        player1_id  = row.player1_id_factor
        player2_id  = row.player2_id_factor
        winner      = row.winner
        match_date  = row.match_date

        # Compute transformed ratings before the match
        player1_rating = (
            _apply_transformation(win_counts[player1_id], win_transform_method) -
            _apply_transformation(lose_counts[player1_id], lose_transform_method)
        )
        player2_rating = (
            _apply_transformation(win_counts[player2_id], win_transform_method) -
            _apply_transformation(lose_counts[player2_id], lose_transform_method)
        )
        
        match_rankings[match_index, 0] = player1_rating
        match_rankings[match_index, 1] = player2_rating
        
        # Update win/loss counters
        if winner == 1:
            win_counts[player1_id]  += win_step
            lose_counts[player2_id] += lose_step
        elif winner == 2:
            win_counts[player2_id]  += win_step
            lose_counts[player1_id] += lose_step
        else:
            logger.warning(f"Invalid winner value: {winner} at match {match_index}")
        
        if verbose:
            # Update progress bar description
            progress_description = (
                f"Surface '{surface}' | Method '{transformation_method}' | "
                f"win({win_step}), lose({lose_step}) | Date: {match_date}"
                )
            progress_bar.set_description(progress_description)
    
    logger.info(f"Computed transformed rankings for {len(matches_df)} matches")
    return match_rankings
