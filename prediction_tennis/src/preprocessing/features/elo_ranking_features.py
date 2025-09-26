# SIMPLE RATING
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from tqdm import tqdm

from prediction_tennis.src.preprocessing.utils.ranking_systems import calculate_rating_movement_from_history

# Configure logging
logger = logging.getLogger("[ELO RANTING]")

# Constants
DEFAULT_STARTING_RATING = 1500.0
DEFAULT_DIVISOR = 400
DEFAULT_SET_DIVISOR = 600
MAX_EXPONENT = 100
MOMENTUM_DECAY_FACTOR = 0.9

# Tournament level multipliers for ATP tournaments
TOURNAMENT_MULTIPLIERS: Dict[float, float] = {
    250.0: 0.8,    # ATP 250
    500.0: 1.0,    # ATP 500
    750.0: 1.0,    # ATP 750
    1000.0: 1.0,   # ATP 1000 (Masters)
    1500.0: 1.0,   # ATP Finals
    2000.0: 1.5    # Grand Slams
}

# Round multipliers based on tournament round importance
ROUND_MULTIPLIERS: Dict[int, float] = {
    1: 2.0,    # Final
    2: 1.5,    # Semifinal
    3: 1.3,    # Quarterfinal
    4: 1.2,    # Round of 16
    8: 1.0,    # Round of 32
    16: 1.0,   # Round of 64
    32: 1.0,   # Round of 128
    64: 0.8,   # Qualifying rounds
    128: 0.5,  # Early qualifying
}

# ELO RANKING
def compute_elo_rankings(matches_df: pd.DataFrame, 
                         k_factor: int, 
                         surface: str = "all", 
                         divisor: int = DEFAULT_DIVISOR, 
                         verbose: bool = False) -> np.ndarray:
    """
    Compute standard ELO rankings for players based on match outcomes.

    This function processes each match in the provided DataFrame, records the
    pre-match ratings for both players, and updates their ratings using the
    standard ELO formula.

    Args:
        matches_df: DataFrame containing match details with columns:
            - 'player1_id_factor': Factorized ID for player 1
            - 'player2_id_factor': Factorized ID for player 2
            - 'winner': Match winner (1 for player 1, 2 for player 2)
            - 'match_date': Date/timestamp of the match
        k_factor: K factor controlling magnitude of rating changes
        surface: Surface type for progress display (default: "all")
        divisor: Divisor for ELO expected score formula (default: 400)
        verbose: Whether to show detailed progress information

    Returns:
        2D numpy array (matches x 2) containing pre-match ratings
        for player 1 and player 2

    Raises:
        KeyError: If required columns are missing from matches_df
        ValueError: If k_factor or divisor are not positive
    """
    if k_factor <= 0: raise ValueError("k_factor must be positive")
    if divisor  <=0  : raise ValueError("divisor must be positive")

    logger.info(f"Computing ELO rankings for {len(matches_df)} matches with k_factor={k_factor}")

    # Determine total number of unique players
    total_players: int = int(
        max(matches_df['player1_id_factor'].max(), matches_df['player2_id_factor'].max()) + 1
    )

    # Initialize player ratings at default starting rating
    current_ratings: np.ndarray = np.full(total_players, DEFAULT_STARTING_RATING, dtype=float)

    # Store pre-match ratings for each match
    match_ratings: np.ndarray = np.zeros((len(matches_df), 2), dtype=float)

    # Process matches with progress bar
    progress_description = f"Processing '{surface}' ELO RANKING"
    progress_bar = tqdm(
        matches_df.itertuples(),
        total=len(matches_df),
        desc=progress_description
    )

    for row in progress_bar:
        match_index = row.Index
        player1_id = row.player1_id_factor
        player2_id = row.player2_id_factor
        winner = row.winner
        match_date = row.match_date # Could be a string, datetime, etc.

        # Get current ratings for both players
        rating_player1: float = current_ratings[player1_id]
        rating_player2: float = current_ratings[player2_id]

        # Store pre-match ratings
        match_ratings[match_index, 0] = rating_player1
        match_ratings[match_index, 1] = rating_player2

        # Calculate expected scores with overflow protection
        rating_diff_1 = (rating_player2 - rating_player1) / divisor
        rating_diff_2 = (rating_player1 - rating_player2) / divisor

        exponent_1 = np.clip(rating_diff_1, -MAX_EXPONENT, MAX_EXPONENT)
        exponent_2 = np.clip(rating_diff_2, -MAX_EXPONENT, MAX_EXPONENT)

        expected_player1: float = 1 / (1 + 10 ** exponent_1)
        expected_player2: float = 1 / (1 + 10 ** exponent_2)

        # Determine actual scores based on match outcome
        actual_score_player1 : int = 1 if winner == 1 else 0
        actual_score_player2 : int = 1 if winner == 2 else 0

        # Update ratings using ELO formula
        rating_change_1 = k_factor * (actual_score_player1 - expected_player1)
        rating_change_2 = k_factor * (actual_score_player2 - expected_player2)

        current_ratings[player1_id] += rating_change_1
        current_ratings[player2_id] += rating_change_2

        if verbose:
            progress_bar.set_description(
                f"Processing '{surface}' ELO (k={k_factor}, "
                f"div={divisor}): '{match_date}'"
            )

    logger.info(f"Completed ELO ranking computation for {surface} surface")
    return match_ratings

def compute_tournament_round_based_elo(matches_df: pd.DataFrame, 
                                       k_factor: int, 
                                       surface: str = "all", 
                                       divisor: int = DEFAULT_DIVISOR) -> np.ndarray:
    """
    Compute ELO rankings with tournament and round-based adjustments.

    This function calculates ELO ratings using an effective K-factor that
    considers both tournament importance and round significance:
    effective_k = k_base × tournament_multiplier × round_multiplier

    Args:
        matches_df: DataFrame with match data including:
            - Standard match columns (as in compute_elo_rankings)
            - 'tournament_level': Numeric tournament level
            - 'round_number': Numeric round identifier
        k_factor: Base K factor for rating updates
        surface: Surface type for progress display
        divisor: Divisor for ELO expected score formula

    Returns:
        2D numpy array containing pre-match ratings for each player pair

    Raises:
        KeyError: If required columns are missing from matches_df
        ValueError: If k_factor or divisor are not positive
    """
    if k_factor <= 0: raise ValueError("k_factor must be positive")
    if divisor  <=0 : raise ValueError("divisor must be positive")

    logger.info(f"Computing tournament/round-based ELO for {len(matches_df)} matches")

    # Determine the total number of players.
    total_players: int = int(
        max(matches_df['player1_id_factor'].max(), matches_df['player2_id_factor'].max()) + 1
    )

    # Initialize player ratings, starting at DEFAULT_STARTING_RATING Elo points.
    current_ratings: np.ndarray = np.full(total_players, DEFAULT_STARTING_RATING, dtype=float)

    # Record pre-match ratings for each match.
    match_ratings: np.ndarray = np.zeros((len(matches_df), 2), dtype=float)

    # Process each match with a progress bar.
    progress_bar = tqdm(
        matches_df.itertuples(),
        total=len(matches_df),
        desc="Processing Tournament/Round ELO"
    )

    for row in progress_bar:
        match_index = row.Index
        player1_id = row.player1_id_factor
        player2_id = row.player2_id_factor
        winner = row.winner
        match_date = row.match_date  # Could be string, datetime, etc.

        # Get current ratings
        rating_player1: float = current_ratings[player1_id]
        rating_player2: float = current_ratings[player2_id]

        # Record the pre-match ratings.
        match_ratings[match_index, 0] = rating_player1
        match_ratings[match_index, 1] = rating_player2

        # Get tournament and round multipliers
        tournament_level = getattr(row, 'type', None)
        round_number     = getattr(row, 'round', None)

        # Get multipliers using the dictionaries; default to 1.0 if the provided key is not found.
        tournament_multiplier = TOURNAMENT_MULTIPLIERS.get(tournament_level, 1.0)
        round_multiplier      = ROUND_MULTIPLIERS.get(round_number, 1.0)

        # Calculate effective K factor
        effective_k = k_factor * tournament_multiplier * round_multiplier

        # Calculate expected scores with overflow protection
        rating_diff_1 = (rating_player2 - rating_player1) / divisor
        rating_diff_2 = (rating_player1 - rating_player2) / divisor

        exponent_1 = np.clip(rating_diff_1, -MAX_EXPONENT, MAX_EXPONENT)
        exponent_2 = np.clip(rating_diff_2, -MAX_EXPONENT, MAX_EXPONENT)

        expected_player1 = 1 / (1 + 10 ** exponent_1)
        expected_player2 = 1 / (1 + 10 ** exponent_2)

        # Determine actual scores and update ratings
        actual_score_player1: int = 1 if winner == 1 else 0
        actual_score_player2: int = 1 if winner == 2 else 0

        rating_change_1 = effective_k * (actual_score_player1 - expected_player1)
        rating_change_2 = effective_k * (actual_score_player2 - expected_player2)

        current_ratings[player1_id] += rating_change_1
        current_ratings[player2_id] += rating_change_2

        progress_bar.set_description(
            f"Processing '{surface}' ELO (k_base={k_factor}, "
            f"divisor={divisor}): {match_date}"
        )

    logger.info("Completed tournament/round-based ELO computation")
    return match_ratings

def compute_tournament_based_elo( matches_df: pd.DataFrame,
                                 k_base: int,
                                 surface: str = "all",
                                 divisor: int = DEFAULT_DIVISOR,
                                 tournament_multipliers: Optional[Dict[float, float]]=None
                                 ) -> np.ndarray:
    """
    Compute ELO rankings with tournament-level adjustments only.

    This function applies different K-factors based on tournament importance:
    effective_k = k_base × tournament_multiplier

    Args:
        matches_df: DataFrame with match data including 'tournament_level'
        k_base: Base K factor for rating updates
        surface: Surface type for progress display
        divisor: Divisor for ELO expected score formula
        tournament_multipliers: Custom tournament multipliers (optional)

    Returns:
        2D numpy array containing pre-match ratings for each player pair
    """
    if k_base <= 0: raise ValueError("k_factor must be positive")
    if divisor  <=0  : raise ValueError("divisor must be positive")
    
    # Tournament multipliers
    if tournament_multipliers is None:
        tournament_multipliers = TOURNAMENT_MULTIPLIERS.copy()

    logger.info(f"Computing tournament-based ELO for {len(matches_df)} matches")

    total_players = int(
        max(matches_df['player1_id_factor'].max(), matches_df['player2_id_factor'].max()) + 1
    )
    current_ratings: np.ndarray = np.full(total_players, DEFAULT_STARTING_RATING, dtype=float)
    match_ratings  : np.ndarray = np.zeros((len(matches_df), 2), dtype=float)

    progress_bar = tqdm(
        matches_df.itertuples(),
        total=len(matches_df),
        desc="Processing Tournament-based ELO"
    )

    for row in progress_bar:
        match_index = row.Index
        player1_id = row.player1_id_factor
        player2_id = row.player2_id_factor
        winner = row.winner
        match_date = row.match_date

        # Record pre-match ratings
        rating_player1 = current_ratings[player1_id]
        rating_player2 = current_ratings[player2_id]
        match_ratings[match_index] = [rating_player1, rating_player2]

        # Determine K-factor based on tournament level
        tournament_level = getattr(row, 'type', None)
        multiplier = tournament_multipliers.get(tournament_level, 1.0)
        effective_k = k_base * multiplier

        # Calculate expected scores with overflow protection
        rating_diff_1 = (rating_player2 - rating_player1) / divisor
        rating_diff_2 = (rating_player1 - rating_player2) / divisor

        exponent_1 = np.clip(rating_diff_1, -MAX_EXPONENT, MAX_EXPONENT)
        exponent_2 = np.clip(rating_diff_2, -MAX_EXPONENT, MAX_EXPONENT)

        expected_player1 = 1 / (1 + 10 ** exponent_1)
        expected_player2 = 1 / (1 + 10 ** exponent_2)

        # Update ratings based on match outcome
        actual_score_player1, actual_score_player2 = (1, 0) if winner == 1 else (0, 1)

        current_ratings[player1_id] += effective_k * (actual_score_player1 - expected_player1)
        current_ratings[player2_id] += effective_k * (actual_score_player2 - expected_player2)

        progress_bar.set_description(
            f"Processing '{surface}' ELO (k_base={k_base}, "
            f"divisor={divisor}): {match_date}"
        )

    logger.info("Completed tournament-based ELO computation")
    return match_ratings

def compute_round_based_elo(matches_df: pd.DataFrame,
                            k_base: int,
                            surface: str = "all",
                            divisor: int = DEFAULT_DIVISOR,
                            round_multipliers: Optional[Dict[int, float]] = None) -> np.ndarray:
    """
    Compute ELO rankings with round-level adjustments only.

    This function applies different K-factors based on tournament round:
    effective_k = k_base × round_multiplier

    Args:
        matches_df: DataFrame with match data including 'round_number'
        k_base: Base K factor for rating updates
        surface: Surface type for progress display
        divisor: Divisor for ELO expected score formula
        round_multipliers: Custom round multipliers (optional)

    Returns:
        2D numpy array containing pre-match ratings for each player pair
    """
    if k_base <= 0: raise ValueError("k_factor must be positive")
    if divisor  <=0  : raise ValueError("divisor must be positive")

    # Round multipliers
    if round_multipliers is None:
        round_multipliers = ROUND_MULTIPLIERS.copy()

    total_players: int = int(
        max(matches_df['player1_id_factor'].max(), matches_df['player2_id_factor'].max()) + 1
    )
    current_ratings : np.ndarray = np.full(total_players, DEFAULT_STARTING_RATING, dtype=float)
    match_ratings: np.ndarray = np.zeros((len(matches_df), 2), dtype=float)

    progress_bar = tqdm(
        matches_df.itertuples(),
        total=len(matches_df),
        desc="Processing Round-based ELO"
    )

    for row in progress_bar:
        match_index = row.Index
        player1_id = row.player1_id_factor
        player2_id = row.player2_id_factor
        winner = row.winner
        match_date = row.match_date

        # Record pre-match ratings
        rating_player1 = current_ratings[player1_id]
        rating_player2 = current_ratings[player2_id]
        match_ratings[match_index] = [rating_player1, rating_player2]

        # Determine K-factor based on round
        round_number = getattr(row, 'round', None)
        multiplier = round_multipliers.get(round_number, 1.0)
        effective_k = k_base * multiplier

        # Calculate expected scores with overflow protection
        rating_diff_1 = (rating_player2 - rating_player1) / divisor
        rating_diff_2 = (rating_player1 - rating_player2) / divisor

        exponent_1 = np.clip(rating_diff_1, -MAX_EXPONENT, MAX_EXPONENT)
        exponent_2 = np.clip(rating_diff_2, -MAX_EXPONENT, MAX_EXPONENT)

        expected_player1 = 1 / (1 + 10 ** exponent_1)
        expected_player2 = 1 / (1 + 10 ** exponent_2)

        # Update ratings based on match outcome
        actual_score_player1, actual_score_player2 = (1, 0) if winner == 1 else (0, 1)

        current_ratings[player1_id] += effective_k * (actual_score_player1 - expected_player1)
        current_ratings[player2_id] += effective_k * (actual_score_player2 - expected_player2)

        progress_bar.set_description(
            f"Processing '{surface}' ELO (k_base={k_base}, "
            f"divisor={divisor}): {match_date}"
        )

    logger.info("Completed round-based ELO computation")
    return match_ratings

def compute_momentum_elo_rankings(matches_df: pd.DataFrame, 
                                  k_base: float, 
                                  surface: str = "all", 
                                  divisor: int = DEFAULT_SET_DIVISOR, 
                                  verbose: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute both standard ELO and Momentum ELO rankings.

    Momentum ELO tracks recent performance trends using:
    momentum = Σ(ELO_change_i × decay_factor^(n-i)) for i=1 to n

    This can be updated recursively as:
    new_momentum = current_ELO_change + decay_factor × previous_momentum

    Args:
        matches_df: DataFrame with match data
        k_base: Base K factor for rating updates
        surface: Surface type for progress display
        divisor: Divisor for ELO expected score formula
        verbose: Whether to show detailed progress information

    Returns:
        Tuple containing:
        - match_ratings: Pre-match ELO ratings (matches x 2)
        - match_momentum: Pre-match Momentum ELO ratings (matches x 2)
    """
    if k_base  <= 0: raise ValueError("k_factor must be positive")
    if divisor <=0 : raise ValueError("divisor must be positive")

    logger.info(f"Computing momentum ELO for {len(matches_df)} matches")

    # Determine total number of players.
    total_players: int = int(
        max(matches_df['player1_id_factor'].max(), matches_df['player2_id_factor'].max()) + 1
    )
    
    # Initialize standard ELO ratings and momentum ratings
    current_ratings : np.ndarray = np.full(total_players, DEFAULT_STARTING_RATING, dtype=float)
    momentum_ratings: np.ndarray = np.zeros(total_players, dtype=float)
    
    # Arrays for storing pre-match values
    match_ratings : np.ndarray = np.zeros((len(matches_df), 2), dtype=float)
    match_momentum: np.ndarray = np.zeros((len(matches_df), 2), dtype=float)
    
    # Progress bar for visual feedback.
    progress_bar = tqdm(
        matches_df.itertuples(),
        total=len(matches_df),
        desc="Processing Momentum ELO"
    )
    
    
    for row in progress_bar:
        match_index = row.Index
        player1_id  = row.player1_id_factor
        player2_id  = row.player2_id_factor
        winner      = row.winner
        match_date  = row.match_date

        # Record pre-match ratings and momentum
        rating_player1 = current_ratings[player1_id]
        rating_player2 = current_ratings[player2_id]
        momentum_player1 = momentum_ratings[player1_id]
        momentum_player2 = momentum_ratings[player2_id]

        match_ratings[match_index, 0] = rating_player1
        match_ratings[match_index, 1] = rating_player2
        match_momentum[match_index, 0] = momentum_player1
        match_momentum[match_index, 1] = momentum_player2

        # Calculate expected scores with overflow protection
        rating_diff_1 = (rating_player2 - rating_player1) / divisor
        rating_diff_2 = (rating_player1 - rating_player2) / divisor

        exponent_1 = np.clip(rating_diff_1, -MAX_EXPONENT, MAX_EXPONENT)
        exponent_2 = np.clip(rating_diff_2, -MAX_EXPONENT, MAX_EXPONENT)

        expected_player1 = 1 / (1 + 10 ** exponent_1)
        expected_player2 = 1 / (1 + 10 ** exponent_2)

        # Determine match outcomes and calculate ELO changes
        actual_score_player1 = 1 if winner == 1 else 0
        actual_score_player2 = 1 if winner == 2 else 0

        elo_change_player1 = k_base * (actual_score_player1 - expected_player1)
        elo_change_player2 = k_base * (actual_score_player2 - expected_player2)

        # Update standard ELO ratings
        current_ratings[player1_id] += elo_change_player1
        current_ratings[player2_id] += elo_change_player2

        # Update momentum ELO recursively
        # New momentum = current_change + decay_factor * previous_momentum
        momentum_ratings[player1_id] = (elo_change_player1 + MOMENTUM_DECAY_FACTOR * momentum_player1)
        momentum_ratings[player2_id] = (elo_change_player2 + MOMENTUM_DECAY_FACTOR * momentum_player2)

        if verbose:
            progress_bar.set_description(
                f"Processing '{surface}' Momentum ELO (k_base={k_base}, "
                f"divisor={divisor}): {match_date}"
            )

    logger.info("Completed momentum ELO computation")
    return match_ratings, match_momentum

def compute_elo_movement(matches_df: pd.DataFrame, lookback_matches: int = 5) -> np.ndarray:
    """
    Calculate ELO movement for each match based on recent performance.

    Args:
        matches_df: DataFrame with match data including:
            - Standard match columns
            - 'elo_p1', 'elo_p2': Pre-match ELO ratings
        lookback_matches: Number of matches to look back (default: 5)

    Returns:
        2D numpy array (n_matches, 2) with ELO movement for each player

    Raises:
        KeyError: If required columns are missing
        ValueError: If lookback_matches is not positive
    """
    if lookback_matches <= 0: raise ValueError("lookback_matches must be positive")

    logger.info(f"Computing ELO movement with {lookback_matches} match lookback")

    # Ensure match_date is datetime
    matches_df['match_date'] = pd.to_datetime(matches_df['match_date'])

    # Determine the total number of players based on the highest player ID seen
    total_players = int(
        max(matches_df['player1_id_factor'].max(), matches_df['player2_id_factor'].max()) + 1
    )

    # Initialize rating history for each player
    player_rating_histories: List[List[Tuple[pd.Timestamp, float]]] = [[] for _ in range(total_players)]

    # Prepare an array to store the Elo movement for each match
    match_movements = np.zeros((len(matches_df), 2), dtype=float)

    # Process matches with a progress bar for visual feedback
    progress_description = f"Calculating last {lookback_matches} ELO Movement"
    for row in tqdm(matches_df.itertuples(), total=len(matches_df), desc=progress_description):
        match_index            = row.Index
        player1_id             = row.player1_id_factor
        player2_id             = row.player2_id_factor
        match_date             = row.match_date
        current_rating_player1 = row.elo_p1  # Current pre-match rating for player 1
        current_rating_player2 = row.elo_p2  # Current pre-match rating for player 2
        
        # Compute Elo movement using the last 'last_match' recorded ratings
        movement_player1 = calculate_rating_movement_from_history(
            rating_history          = player_rating_histories[player1_id],
            current_pre_match_rating= current_rating_player1,
            matches_lookback        = lookback_matches
            )
        movement_player2 = calculate_rating_movement_from_history(
            rating_history          = player_rating_histories[player2_id],
            current_pre_match_rating= current_rating_player2,
            matches_lookback        = lookback_matches
            )
        
        match_movements[match_index, 0] = movement_player1
        match_movements[match_index, 1] = movement_player2


        # Update rating histories
        player_rating_histories[player1_id].append((match_date, current_rating_player1))
        player_rating_histories[player2_id].append((match_date, current_rating_player2))

    logger.info("Completed ELO movement computation")
    return match_movements
