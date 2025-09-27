"""
Ranking Systems Utility Module

This module provides utility functions for various ranking systems, including
Glicko rating calculations, rating movement analysis, and transformation
functions for rating adjustments. The functions support different rating
systems and provide tools for tracking and updating player ratings based on
match outcomes.
"""

import logging
from typing import List, Tuple

import numpy as np
import pandas as pd

# Constants
GLICKO_CONSTANT_3_SQUARED = 9  # 3^2 for optimization
PI_SQUARED = np.pi**2


def calculate_rating_movement_from_history(
    rating_history: List[Tuple[pd.Timestamp, float]],
    current_pre_match_rating: float,
    matches_lookback: int,
) -> float:
    """
    Calculate the change in rating over a specified number of past matches.

    This function computes the difference between the current pre-match rating
    and the rating from 'matches_lookback' matches ago. If insufficient history
    exists, it returns 0.0.

    Parameters
    ----------
    rating_history : List[Tuple[pd.Timestamp, float]]
        List of (timestamp, rating) tuples in chronological order
    current_pre_match_rating : float
        Current pre-match rating
    matches_lookback : int
        Number of matches to look back for comparison

    Returns
    -------
    float
        Rating movement as difference between current and historical rating.
        Returns 0.0 if insufficient history exists.

    Raises
    ------
    TypeError
        If rating_history is not a list or contains invalid elements
    """
    if not rating_history:
        logging.debug("Empty rating history, returning 0.0 movement")
        return 0.0

    # Check if we have enough history for the requested lookback
    if len(rating_history) < matches_lookback:
        logging.debug(
            f"Insufficient history: {len(rating_history)} < {matches_lookback}, returning 0.0 movement"
        )
        return 0.0

    # Get rating from 'matches_lookback' matches ago
    historical_index = len(rating_history) - matches_lookback
    _, historical_rating = rating_history[historical_index]

    movement = current_pre_match_rating - historical_rating
    logging.debug(f"Rating movement: {movement:.3f}")

    return movement


def _update_player_glicko_rating(
    player_rating: float,
    player_rd: float,
    opponent_rating: float,
    opponent_rd: float,
    player_score: float,
    q_factor: float,
) -> Tuple[float, float]:
    """
    Update a single player's Glicko rating and rating deviation.

    This is a helper function that implements the core Glicko update equations
    for a single player based on the outcome of one match.

    Parameters
    ----------
    player_rating : float
        Current rating of the player
    player_rd : float
        Current rating deviation of the player
    opponent_rating : float
        Current rating of the opponent
    opponent_rd : float
        Current rating deviation of the opponent
    player_score : float
        Score achieved by player (1 for win, 0 for loss)
    q_factor : float
        Glicko system constant

    Returns
    -------
    Tuple[float, float]
        Tuple containing updated (rating, rating_deviation)

    Raises
    ------
    ValueError
        If any input parameters are invalid (e.g., negative RD values)
    """
    # Calculate g(RD) for opponent
    g_opponent_rd = _calculate_g_function(rating_deviation=opponent_rd, q_factor=q_factor)

    # Calculate expected score
    expected_score = _calculate_expected_score(
        player_rating=player_rating, opponent_rating=opponent_rating
    )

    # Calculate d²
    d_squared_inverse = q_factor**2 * g_opponent_rd**2 * expected_score * (1 - expected_score)
    d_squared = 1 / d_squared_inverse if d_squared_inverse != 0 else float("inf")

    # Update rating
    rating_update_factor = q_factor / (1 / (player_rd**2) + 1 / d_squared)
    updated_rating = player_rating + rating_update_factor * g_opponent_rd * (
        player_score - expected_score
    )

    # Update rating deviation
    updated_rd = np.sqrt(1 / (1 / (player_rd**2) + 1 / d_squared))

    return updated_rating, updated_rd


def _calculate_g_function(rating_deviation: float, q_factor: float) -> float:
    """
    Calculate the g(RD) function used in Glicko rating updates.

    Parameters
    ----------
    rating_deviation : float
        Rating deviation value
    q_factor : float
        Glicko system constant

    Returns
    -------
    float
        g(RD) value

    Raises
    ------
    ValueError
        If rating_deviation is negative
    """
    return 1 / np.sqrt(
        1 + (GLICKO_CONSTANT_3_SQUARED * (q_factor**2) * (rating_deviation**2)) / PI_SQUARED
    )


def _calculate_expected_score(player_rating: float, opponent_rating: float) -> float:
    """
    Calculate expected score for a player against an opponent.

    Parameters
    ----------
    player_rating : float
        Player's current rating
    opponent_rating : float
        Opponent's current rating

    Returns
    -------
    float
        Expected score (probability of winning)

    Raises
    ------
    ValueError
        If ratings are not finite numbers
    """
    return 1 / (1 + 10 ** ((opponent_rating - player_rating) / 400))


def _calculate_update_values(
    win_step: float, lose_step: float, transformation_method: str, transformation_factor: float
) -> tuple[float, float]:
    """
    Calculate transformed update values based on the specified method.

    Parameters
    ----------
    win_step : float
        Base win step value
    lose_step : float
        Base lose step value
    transformation_method : str
        Transformation method to apply
    transformation_factor : float
        Factor for the transformation

    Returns
    -------
    Tuple[float, float]
        Tuple of (transformed_win_step, transformed_lose_step)

    Raises
    ------
    ValueError
        If transformation method is invalid or would cause
        mathematical errors
    """
    try:
        if transformation_method == "power":
            update_win = win_step**transformation_factor
            update_lose = lose_step**transformation_factor

        elif transformation_method == "exp":
            update_win = np.exp(win_step * transformation_factor)
            update_lose = np.exp(lose_step * transformation_factor)

        elif transformation_method == "log":
            # Ensure arguments to log are positive
            if win_step + transformation_factor <= 0:
                raise ValueError("Log transformation requires positive argument")
            if lose_step + transformation_factor <= 0:
                raise ValueError("Log transformation requires positive argument")
            update_win = np.log(win_step + transformation_factor)
            update_lose = np.log(lose_step + transformation_factor)

        elif transformation_method == "power-log":
            if lose_step + transformation_factor <= 0:
                raise ValueError("Log transformation requires positive argument")
            update_win = win_step**transformation_factor
            update_lose = np.log(lose_step + transformation_factor)

        elif transformation_method == "power-exp":
            update_win = win_step**transformation_factor
            update_lose = np.exp(lose_step * transformation_factor)

        elif transformation_method == "log-exp":
            if win_step + transformation_factor <= 0:
                raise ValueError("Log transformation requires positive argument")
            update_win = np.log(win_step + transformation_factor)
            update_lose = np.exp(lose_step * transformation_factor)

        elif transformation_method == "log-power":
            if win_step + transformation_factor <= 0:
                raise ValueError("Log transformation requires positive argument")
            update_win = np.log(win_step + transformation_factor)
            update_lose = lose_step**transformation_factor

        elif transformation_method == "exp-log":
            if lose_step + transformation_factor <= 0:
                raise ValueError("Log transformation requires positive argument")
            update_win = np.exp(win_step * transformation_factor)
            update_lose = np.log(lose_step + transformation_factor)

        elif transformation_method == "exp-power":
            update_win = np.exp(win_step * transformation_factor)
            update_lose = lose_step**transformation_factor

        else:
            logging.warning(
                f"Unknown transformation method '{transformation_method}', "
                f"using default (no transformation)"
            )
            update_win = win_step
            update_lose = lose_step

    except (ValueError, OverflowError) as e:
        logging.error(f"Error calculating update values: {e}")
        raise ValueError(f"Invalid transformation parameters: {e}") from e

    return update_win, update_lose


def _apply_transformation(value: float, method: str) -> float:
    """
    Apply a single transformation to a value.

    Parameters
    ----------
    value : float
        Value to transform
    method : str
        Transformation method ("power", "exp", or "log")

    Returns
    -------
    float
        Transformed value

    Raises
    ------
    ValueError
        If transformation would cause mathematical errors
    """
    try:
        if method == "power":
            return value**2

        elif method == "exp":
            # Scale and clamp to avoid overflow
            scaled_value = min(50, value / 100)
            return np.exp(scaled_value)

        elif method == "log":
            # Handle negative values using reciprocal transformation
            if value < 0:
                return np.log1p(1 / abs(value))
            else:
                return np.log1p(value)

        else:
            logging.warning(f"Unknown transformation method '{method}', returning original value")
            return value

    except (ValueError, OverflowError) as e:
        logging.error(f"Error applying transformation '{method}' to value {value}: {e}")
        return value  # Return original value on error
