# SIMPLE RATING
import logging
import numpy as np
import pandas as pd
from tqdm import tqdm
import trueskill


# Configure logging
logger = logging.getLogger("[TRUESKILL RANTING]")


# TRUESKILL RANKING
def compute_trueskill_ratings(
    matches_df: pd.DataFrame, surface: str = "all", verbose: bool = False
) -> np.ndarray:
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
    if not isinstance(matches_df, pd.DataFrame):
        raise TypeError("matches_df must be a pandas DataFrame")

    required_columns = ["player1_id_factor", "player2_id_factor", "winner", "match_date"]
    missing_columns = [col for col in required_columns if col not in matches_df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Calculate total number of unique players
    max_player_id: int = max(
        matches_df["player1_id_factor"].max(), matches_df["player2_id_factor"].max()
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
    progress_bar = tqdm(matches_df.itertuples(), total=len(matches_df), desc=progress_desc)

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
            progress_bar.set_description(
                f"Processing '{surface}' TrueSkill ratings: '{match_date}'"
            )

    logger.info("TrueSkill rating computation completed successfully")
    return pre_match_ratings
