"""
Player Popularity Computation Module.

This module provides functionality to calculate tennis player popularity metrics
based on tournament performance history. It supports multiple calculation
methods (multiplicative, additive, geometric mean, harmonic mean, weighted sum)
and allows for customizable time windows and factor inclusion strategies.

The popularity calculation considers:
- Tournament prestige (type weights: 250, 500, 750, 1000, 1500, 2000)
- Match round progression (round weights: 128, 64, 32, 16, 8, 4, 2, 1)
- Temporal windows (3 months, 6 months, 1 year, 2 years, all-time)

Typical usage
-------------
>>> import pandas as pd
>>> from popularity_calculator import compute_player_popularity_before_match
>>> from popularity_calculator import PopularityMethod, PopularityPeriod
>>>
>>> df = pd.read_csv('match_data.csv')
>>> popularity = compute_player_popularity_before_match(
...     df,
...     methods=PopularityMethod.MULTIPLICATIVE,
...     time_window=PopularityPeriod.SIX_MONTHS
... )
"""

import logging
from datetime import timedelta
from enum import Enum
from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from prediction_tennis.src.utils.core_error_functions import (
    raise_runtime_error,
    validate_type,
)

# Configure module logger
logger = logging.getLogger("[ELO POPULARITY]")

# Initialize tqdm for pandas progress bars
tqdm.pandas()


class PopularityMethod(Enum):
    """
    Enumeration of supported popularity calculation methods.

    Attributes
    ----------
    MULTIPLICATIVE : str
        Product of type and round weights (default approach).
    ADDITIVE : str
        Sum of type and round weights.
    GEOMETRIC_MEAN : str
        Geometric mean of type and round weights.
    HARMONIC_MEAN : str
        Harmonic mean of type and round weights.
    WEIGHTED_SUM : str
        Weighted sum with 70% type weight and 30% round weight.
    """

    MULTIPLICATIVE = "multiplicative"
    ADDITIVE = "additive"
    GEOMETRIC_MEAN = "geometric_mean"
    HARMONIC_MEAN = "harmonic_mean"
    WEIGHTED_SUM = "weighted_sum"


class FactorInclusion(Enum):
    """
    Enumeration of factor inclusion options for popularity calculation.

    Attributes
    ----------
    BOTH : str
        Use both tournament type and round progression factors.
    TYPE_ONLY : str
        Use only tournament type factor.
    ROUND_ONLY : str
        Use only round progression factor.
    """

    BOTH = "both"
    TYPE_ONLY = "type_only"
    ROUND_ONLY = "round_only"


class PopularityPeriod(Enum):
    """
    Enumeration of time periods for popularity calculation windows.

    Attributes
    ----------
    THREE_MONTHS : timedelta
        90-day rolling window.
    SIX_MONTHS : timedelta
        180-day rolling window.
    ONE_YEAR : timedelta
        365-day rolling window.
    TWO_YEARS : timedelta
        730-day rolling window.
    ALL_TIME : None
        Complete historical accumulation (no time limit).
    """

    THREE_MONTHS = timedelta(days=90)
    SIX_MONTHS = timedelta(days=180)
    ONE_YEAR = timedelta(days=365)
    TWO_YEARS = timedelta(days=730)
    ALL_TIME = None


# Tournament type prestige mapping (ATP points level to weight multiplier)
TYPE_WEIGHTS: Dict[int, float] = {
    250: 1.0,  # ATP 250 tournaments
    500: 2.0,  # ATP 500 tournaments
    750: 3.0,  # ATP 750 tournaments
    1000: 4.0,  # ATP Masters 1000
    1500: 6.0,  # Grand Slam (alternative point system)
    2000: 8.0,  # Grand Slam (standard point system)
}

# Round progression importance mapping (remaining players to weight multiplier)
ROUND_WEIGHTS: Dict[int, float] = {
    128: 1.0,  # First round (large draw)
    64: 1.0,  # First round (standard draw)
    32: 1.2,  # Second round (Round of 32)
    16: 1.5,  # Third round (Round of 16)
    8: 2.0,  # Quarterfinals
    4: 2.5,  # Semifinals
    2: 3.0,  # Finals
    1: 4.0,  # Champion
}


def _calculate_multiplicative(type_weight: pd.Series, round_weight: pd.Series) -> pd.Series:
    """
    Calculate popularity as the product of type and round weights.

    This method emphasizes the combined importance of tournament prestige
    and match progression, with higher weights for prestigious tournaments
    at advanced stages.

    Parameters
    ----------
    type_weight : pd.Series
        Tournament type weight values.
    round_weight : pd.Series
        Round progression weight values.

    Returns
    -------
    pd.Series
        Popularity scores computed as type_weight × round_weight.
    """
    logger.debug("Computing multiplicative popularity scores")
    return type_weight * round_weight


def _calculate_additive(type_weight: pd.Series, round_weight: pd.Series) -> pd.Series:
    """
    Calculate popularity as the sum of type and round weights.

    This method treats tournament prestige and round progression as
    independent contributions to overall popularity.

    Parameters
    ----------
    type_weight : pd.Series
        Tournament type weight values.
    round_weight : pd.Series
        Round progression weight values.

    Returns
    -------
    pd.Series
        Popularity scores computed as type_weight + round_weight.
    """
    logger.debug("Computing additive popularity scores")
    return type_weight + round_weight


def _calculate_geometric_mean(type_weight: pd.Series, round_weight: pd.Series) -> pd.Series:
    """
    Calculate popularity as the geometric mean of type and round weights.

    The geometric mean provides a balanced measure that penalizes extreme
    imbalances between tournament prestige and round progression.

    Parameters
    ----------
    type_weight : pd.Series
        Tournament type weight values.
    round_weight : pd.Series
        Round progression weight values.

    Returns
    -------
    pd.Series
        Popularity scores computed as √(type_weight × round_weight).
    """
    logger.debug("Computing geometric mean popularity scores")
    return (type_weight * round_weight) ** 0.5


def _calculate_harmonic_mean(type_weight: pd.Series, round_weight: pd.Series) -> pd.Series:
    """
    Calculate popularity as the harmonic mean of type and round weights.

    The harmonic mean is particularly sensitive to low values, making it
    useful when both factors should contribute meaningfully to popularity.

    Parameters
    ----------
    type_weight : pd.Series
        Tournament type weight values.
    round_weight : pd.Series
        Round progression weight values.

    Returns
    -------
    pd.Series
        Popularity scores computed as 2 / (1/type_weight + 1/round_weight).
        Returns infinity for zero weights to avoid division errors.
    """
    logger.debug("Computing harmonic mean popularity scores")
    # Identify valid entries (no zero weights)
    mask = (type_weight != 0) & (round_weight != 0)
    result = pd.Series(float("inf"), index=type_weight.index)
    result[mask] = 2 / ((1 / type_weight[mask]) + (1 / round_weight[mask]))
    return result


def _calculate_weighted_sum(type_weight: pd.Series, round_weight: pd.Series) -> pd.Series:
    """
    Calculate popularity as a weighted sum with 70% type and 30% round.

    This method emphasizes tournament prestige over round progression,
    reflecting the conventional wisdom that tournament tier matters more
    than individual match advancement.

    Parameters
    ----------
    type_weight : pd.Series
        Tournament type weight values.
    round_weight : pd.Series
        Round progression weight values.

    Returns
    -------
    pd.Series
        Popularity scores computed as 0.7 × type_weight + 0.3 × round_weight.
    """
    logger.debug("Computing weighted sum popularity scores")
    return 0.7 * type_weight + 0.3 * round_weight


# Registry mapping calculation methods to their implementation functions
POPULARITY_CALCULATORS: Dict[PopularityMethod, Callable] = {
    PopularityMethod.MULTIPLICATIVE: _calculate_multiplicative,
    PopularityMethod.ADDITIVE: _calculate_additive,
    PopularityMethod.GEOMETRIC_MEAN: _calculate_geometric_mean,
    PopularityMethod.HARMONIC_MEAN: _calculate_harmonic_mean,
    PopularityMethod.WEIGHTED_SUM: _calculate_weighted_sum,
}


def _apply_factor_inclusion(
    df: pd.DataFrame,
    factor_inclusion: FactorInclusion,
    type_weights: Dict[int, float],
    round_weights: Dict[int, float],
) -> pd.DataFrame:
    """
    Apply factor inclusion strategy to assign appropriate weight columns.

    This function maps tournament types and rounds to their corresponding
    weights based on the selected inclusion strategy. When only one factor
    is used, the other is set to 1.0 to maintain compatibility with
    multiplicative methods.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame containing 'type' and 'round' columns.
    factor_inclusion : FactorInclusion
        Strategy determining which factors to include in calculation.
    type_weights : Dict[int, float]
        Mapping of tournament type identifiers to weight multipliers.
    round_weights : Dict[int, float]
        Mapping of round identifiers to weight multipliers.

    Returns
    -------
    pd.DataFrame
        DataFrame with added 'type_weight' and 'round_weight' columns.

    Notes
    -----
    - Missing type/round values are filled with 0.0
    - When using TYPE_ONLY, round_weight is set to 1.0
    - When using ROUND_ONLY, type_weight is set to 1.0
    """
    logger.debug(f"Applying factor inclusion strategy: {factor_inclusion.value}")
    df = df.copy()

    # Initialize weight columns with zeros
    df["type_weight"] = 0.0
    df["round_weight"] = 0.0

    # Map type values to weights if type factor is included
    if factor_inclusion in [FactorInclusion.BOTH, FactorInclusion.TYPE_ONLY]:
        df["type_weight"] = df["type"].map(type_weights).fillna(0)
        logger.debug(f"Applied type weights: {df['type_weight'].describe()}")

    # Map round values to weights if round factor is included
    if factor_inclusion in [FactorInclusion.BOTH, FactorInclusion.ROUND_ONLY]:
        df["round_weight"] = df["round"].map(round_weights).fillna(0)
        logger.debug(f"Applied round weights: {df['round_weight'].describe()}")

    # Set neutral weight (1.0) for excluded factors in multiplicative contexts
    if factor_inclusion == FactorInclusion.TYPE_ONLY:
        df["round_weight"] = 1.0
    elif factor_inclusion == FactorInclusion.ROUND_ONLY:
        df["type_weight"] = 1.0

    return df


def compute_player_popularity_before_match(
    df: pd.DataFrame,
    methods: PopularityMethod = PopularityMethod.MULTIPLICATIVE,
    factor_inclusion: FactorInclusion = FactorInclusion.BOTH,
    time_window: PopularityPeriod = PopularityPeriod.ALL_TIME,
    custom_type_weights: Optional[Dict[int, float]] = None,
    custom_round_weights: Optional[Dict[int, float]] = None,
) -> np.ndarray:
    """
    Compute cumulative player popularity scores before each match.

    This function calculates historical popularity metrics for both players
    in each match, considering their performance up to (but not including)
    the current match. Popularity can be computed using various methods
    and time windows.

    Parameters
    ----------
    df : pd.DataFrame
        Match data with required columns:
        - match_id : Unique match identifier
        - match_date : Match date/time (will be converted to datetime)
        - player1_id_factor : First player identifier
        - player2_id_factor : Second player identifier
        - type : Tournament type identifier (e.g., 250, 500, 1000)
        - round : Round identifier (e.g., 128, 64, 32, 16, 8, 4, 2, 1)
    methods : PopularityMethod, default=PopularityMethod.MULTIPLICATIVE
        Calculation method for combining type and round weights.
    factor_inclusion : FactorInclusion, default=FactorInclusion.BOTH
        Strategy for including tournament type and/or round factors.
    time_window : PopularityPeriod, default=PopularityPeriod.ALL_TIME
        Temporal window for popularity accumulation.
    custom_type_weights : Dict[int, float], optional
        Custom tournament type weight mapping. Uses TYPE_WEIGHTS if None.
    custom_round_weights : Dict[int, float], optional
        Custom round weight mapping. Uses ROUND_WEIGHTS if None.

    Returns
    -------
    np.ndarray
        Array with shape (n_matches, 2) containing popularity scores:
        - Column 0: Player 1 popularity before match
        - Column 1: Player 2 popularity before match

    Raises
    ------
    ValueError
        If methods, factor_inclusion, or time_window are not proper enum types.
    RuntimeError
        If popularity calculation fails for the specified method.

    Notes
    -----
    - Popularity is computed from historical matches only (excluding current)
    - First-time players receive a popularity score of 0
    - Progress bars display computation progress for large datasets
    - All-time calculations use cumulative sums for efficiency
    - Rolling window calculations iterate through matches for accuracy

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({
    ...     'match_id': [1, 2, 3],
    ...     'match_date': ['2024-01-01', '2024-01-15', '2024-02-01'],
    ...     'player1_id_factor': [101, 102, 101],
    ...     'player2_id_factor': [102, 103, 103],
    ...     'type': [500, 1000, 500],
    ...     'round': [32, 16, 8]
    ... })
    >>> popularity = compute_player_popularity_before_match(
    ...     df,
    ...     methods=PopularityMethod.MULTIPLICATIVE,
    ...     time_window=PopularityPeriod.SIX_MONTHS
    ... )
    >>> print(popularity.shape)
    (3, 2)
    """
    # Input validation
    validate_type(value=methods, expected_type=PopularityMethod, logger=logger)
    validate_type(value=factor_inclusion, expected_type=FactorInclusion, logger=logger)
    validate_type(value=time_window, expected_type=PopularityPeriod, logger=logger)

    logger.info(
        f"Computing popularity with method={methods.value}, "
        f"factors={factor_inclusion.value}, window={time_window.name}"
    )

    # Prepare data
    df_processed = df.copy()
    df_processed["match_date"] = pd.to_datetime(df_processed["match_date"])
    logger.info(f"Processing {len(df_processed)} matches")

    # Determine weight mappings
    type_weights = custom_type_weights or TYPE_WEIGHTS
    round_weights = custom_round_weights or ROUND_WEIGHTS

    # Apply factor inclusion strategy to create weight columns
    df_processed = _apply_factor_inclusion(
        df=df_processed,
        factor_inclusion=factor_inclusion,
        type_weights=type_weights,
        round_weights=round_weights,
    )

    # Extract calculation details
    method = methods
    method_name = method.value
    factor_suffix = factor_inclusion.value
    column_suffix = f"{method_name}_{factor_suffix}"

    # Get appropriate calculator function
    calculator = POPULARITY_CALCULATORS[method]

    # Calculate popularity scores for each match
    try:
        df_processed[f"popularity_{column_suffix}"] = calculator(
            df_processed["type_weight"], df_processed["round_weight"]
        )
        df_processed[f"popularity_{column_suffix}"] = df_processed[
            f"popularity_{column_suffix}"
        ].fillna(0)
        logger.debug(
            f"Calculated popularity scores: "
            f"{df_processed[f'popularity_{column_suffix}'].describe()}"
        )
    except Exception as e:
        raise_runtime_error(f"Error calculating popularity with method {method_name}: {e}", logger)

    # Transform to long format for player-centric calculation
    popularity_column = f"popularity_{column_suffix}"

    # Player 1 records
    pop_p1 = df_processed[
        ["match_id", "match_date", "player1_id_factor", popularity_column]
    ].rename(columns={"player1_id_factor": "player_id", popularity_column: "popularity"})

    # Player 2 records
    pop_p2 = df_processed[
        ["match_id", "match_date", "player2_id_factor", popularity_column]
    ].rename(columns={"player2_id_factor": "player_id", popularity_column: "popularity"})

    # Combine player records
    pop_long = pd.concat([pop_p1, pop_p2], ignore_index=True)
    pop_long = pop_long.sort_values(by=["player_id", "match_date"])
    logger.debug(f"Created long format with {len(pop_long)} player-match records")

    # Compute historical popularity based on time window
    time_window_delta = time_window.value
    time_window_name = time_window.name.lower()
    column_suffix_with_window = f"{column_suffix}_{time_window_name}"

    if time_window_delta is None:
        # All-time cumulative calculation (efficient vectorized approach)
        logger.info("Computing all-time cumulative popularity")
        grouped = pop_long.groupby("player_id")
        results = []

        progress_desc = "Computing all-time cumulative popularity"
        with tqdm(total=len(grouped), desc=progress_desc) as pbar:
            for _, group in grouped:
                # Shift to exclude current match, then compute cumulative sum
                cumulative = group["popularity"].shift(1).fillna(0).cumsum()
                results.append(cumulative)
                pbar.update(1)

        pop_long["popularity_before_match"] = pd.concat(results).sort_index()

    else:
        # Rolling window calculation (iterative for accuracy)
        logger.info(
            f"Computing rolling {time_window.name} popularity ({time_window_delta.days} days)"
        )
        results = []

        progress_desc = f"Computing rolling {time_window.name} popularity"
        with tqdm(total=len(pop_long), desc=progress_desc) as pbar:
            for _, row in pop_long.iterrows():
                current_time = row["match_date"]
                player = row["player_id"]

                # Filter matches within time window before current match
                mask = (
                    (pop_long["player_id"] == player)
                    & (pop_long["match_date"] < current_time)
                    & (pop_long["match_date"] >= current_time - time_window_delta)
                )
                result = pop_long.loc[mask, "popularity"].sum()
                results.append(result)
                pbar.update(1)

        pop_long["popularity_before_match"] = results

    # Separate player 1 and player 2 popularity scores
    pop_p1_before = pop_long[["match_id", "player_id", "popularity_before_match"]].rename(
        columns={
            "player_id": "player1_id_factor",
            "popularity_before_match": (f"popularity_{column_suffix_with_window}_p1"),
        }
    )

    pop_p2_before = pop_long[["match_id", "player_id", "popularity_before_match"]].rename(
        columns={
            "player_id": "player2_id_factor",
            "popularity_before_match": (f"popularity_{column_suffix_with_window}_p2"),
        }
    )

    # Merge popularity scores back to original DataFrame
    df_processed = df_processed.merge(
        pop_p1_before, on=["match_id", "player1_id_factor"], how="left"
    )
    df_processed = df_processed.merge(
        pop_p2_before, on=["match_id", "player2_id_factor"], how="left"
    )

    # Extract final popularity columns as numpy array
    result_columns = [
        f"popularity_{column_suffix_with_window}_p1",
        f"popularity_{column_suffix_with_window}_p2",
    ]

    result_array = df_processed[result_columns].fillna(0).to_numpy()

    logger.info(
        f"Computation complete. Result shape: {result_array.shape}, "
        f"mean values: {result_array.mean(axis=0)}"
    )

    return result_array
