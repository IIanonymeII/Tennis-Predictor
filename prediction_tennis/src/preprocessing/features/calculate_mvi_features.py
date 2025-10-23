"""
Calculates player performance volatility metrics from match data.

This script transforms a match-level DataFrame into a player-centric,
long-format DataFrame. It then computes a rolling mean (mu) and variance (v)
of player performance using an exponential moving average. Finally, it
calculates the Match Volatility Index (MVI) for each player and merges this
information back into the original match DataFrame.
"""


import logging
import numpy as np
import pandas as pd

from prediction_tennis.src.preprocessing.features.match_features import _align_dataframes


logger = logging.getLogger("[FEATURE MVI]")

# --- Constants ---
ALPHA: float = 0.1
EPSILON: float = 1e-8

def create_player_centric_view(match_data: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms match data from wide format to a long, player-centric format.

    In the original DataFrame, each row represents a single match with columns
    for both players. This function creates two separate views (one for each
    player) and concatenates them to produce a long-format DataFrame where
    each row represents one player's participation in a match.

    Parameters
    ----------
    match_data : pd.DataFrame
        The input DataFrame containing match results. Expected columns include
        'player1_id', 'player2_id', 's_t_p1', 's_t_p2', 'winner',
        'timestamp', and 'match_id'.

    Returns
    -------
    pd.DataFrame
        A new DataFrame in long format, sorted by timestamp, with one row per
        player per match. Columns are standardized to 'player_id', 's_t', etc.

    Raises
    ------
    KeyError
        If required columns are missing from the input DataFrame.
    """
    logging.info("Creating player-centric views from match data.")

    # Create a view for player 1 & 2.
    p1_view = match_data.rename(columns={"player1_id": "player_id", "p1_set_success_rate": "s_t"})
    p2_view = match_data.rename(columns={"player2_id": "player_id", "p2_set_success_rate": "s_t"})

    relevant_columns = ["timestamp", "match_id", "player_id", "s_t"]

    # Concatenate both views into a single long-format DataFrame.
    player_centric_df = pd.concat(
        [p1_view[relevant_columns], p2_view[relevant_columns]],
        ignore_index=False,
    )

    # Sort by timestamp to ensure chronological order for rolling calculations.
    player_centric_df = player_centric_df.sort_values(by="timestamp")
    logger.info("Successfully created and sorted player-centric DataFrame.")
    logger.debug("Sample data from player-centric view:\n%s", player_centric_df.head())

    return player_centric_df

def calculate_volatility_metrics(player_history: pd.DataFrame, 
                                 alpha: float, 
                                 epsilon: float) -> pd.DataFrame:
    """
    Calculates rolling performance metrics for a single player's history.

    This function applies an exponential moving average to compute the rolling
    mean (mu_t) and variance (v_t) of a player's performance score ('s_t').
    It then calculates the Match Volatility Index (MVI) from the variance.

    Parameters
    ----------
    player_history : pd.DataFrame
        A DataFrame containing the match history for a single player, sorted
        chronologically.
    alpha : float
        The smoothing factor (learning rate) for the exponential moving average.
    epsilon : float
        A small constant added to the variance to ensure numerical stability when
        taking the square root.

    Returns
    -------
    pd.DataFrame
        The input DataFrame with added columns: 'mu_t', 'v_t', and 'MVI'.
    """
    mu_previous = 0.5  # Neutral expectation (50% performance score).
    v_previous = 0.25  # Max variance for a Bernoulli-like variable [0, 1].

    # Lists to store the calculated values for each match.
    mus = []
    vs = []

    for _, row in player_history.iterrows():
        performance_score = row["s_t"]

        # Update the rolling mean (mu).
        mu_current = (1 - alpha) * mu_previous + alpha * performance_score

        # Update the rolling variance (v) using the *previous* mean.
        v_current = (1 - alpha) * v_previous + alpha * (performance_score - mu_previous) ** 2

        mus.append(mu_current)
        vs.append(v_current)

        # Update the state for the next iteration.
        mu_previous = mu_current
        v_previous = v_current

    # Assign new columns safely using .loc to avoid SettingWithCopyWarning.
    player_history.loc[:, "mu_t"] = mus
    player_history.loc[:, "v_t"] = vs
    player_history.loc[:, "MVI"] = np.sqrt(player_history["v_t"] + epsilon)

    return player_history

def add_mvi_features_to_matches(match_data: pd.DataFrame) -> np.ndarray:
    """
    Orchestrates MVI calculation and returns the MVI values as a NumPy array.

    This is the main function that coordinates the entire workflow:
    1. Transforms the data to a player-centric view.
    2. Calculates volatility metrics for each player.
    3. Re-aligns the results and extracts the MVI values.

    Parameters
    ----------
    match_data : pd.DataFrame
        The original DataFrame with one row per match.

    Returns
    -------
    np.ndarray
        A NumPy array of shape (n_matches, 2) where the first column is
        'MVI_p1' and the second column is 'MVI_p2'.
    """
    # Create the long-format DataFrame for calculations.
    player_centric_df = create_player_centric_view(match_data)

    # Initialize columns for the rolling metrics.
    player_centric_df["mu_t"] = 0.5
    player_centric_df["v_t"] = 0.25

    logger.info("Calculating volatility metrics for all players...")
    # Apply the calculation to each player's history group.
    player_metrics_df = player_centric_df.groupby("player_id", group_keys=False).apply(
        lambda group: calculate_volatility_metrics(group, ALPHA, EPSILON))

    logger.info("Aligning dataframes to merge MVI features.")
    # This step requires the original player views for proper alignment.
    # Recreate them here to pass to the alignment function.
    p1_view = match_data.rename(columns={"player1_id": "player_id", "s_t_p1": "s_t"})
    p2_view = match_data.rename(columns={"player2_id": "player_id", "s_t_p2": "s_t"})

    # Align the calculated metrics back to the match-centric format.
    p1_final_df, p2_final_df = _align_dataframes(player_metrics_df, p1_view, p2_view, match_data)

    # Extract the MVI columns as NumPy arrays.
    mvi_p1 = p1_final_df["MVI"].to_numpy()
    mvi_p2 = p2_final_df["MVI"].to_numpy()

    # Stack the arrays column-wise to create a (n_matches, 2) array.
    mvi_array = np.stack((mvi_p1, mvi_p2), axis=1)

    logging.info("MVI features successfully extracted as a NumPy array.")
    return mvi_array
