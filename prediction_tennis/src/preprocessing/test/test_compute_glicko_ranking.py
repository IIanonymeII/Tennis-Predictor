

import itertools
import numpy as np
import pandas as pd
import pytest

from prediction_tennis.src.preprocessing.features.compute_rating_movement import compute_rating_movement
from prediction_tennis.src.preprocessing.features.glicko_ranking_features import compute_glicko_ratings


@pytest.fixture
def sample_matches_df() -> pd.DataFrame:
    """
    Create a DataFrame with sample tennis match data for testing.
    
    Returns:
        pd.DataFrame: Test dataset containing player IDs, winners, tournament
                     types, rounds and match dates.
    """
    test_data = {
        'player1_id_factor': [1  , 1  , 2  , 2  , 3  , 3   ],
        'player2_id_factor': [2  , 3  , 1  , 3  , 1  , 2   ],
        'winner'           : [1  , 2  , 1  , 2  , 2  , 2   ],
        'type'             : [250, 250, 250, 250, 500, 1000],
        'round'            : [32 , 16 , 8  , 4  , 2  , 1   ],
        'match_date'       : ['2023-01-01', '2023-01-02', '2023-01-03',
                             '2023-01-04', '2023-01-05', '2023-01-06'],
        'glicko_p1'        : [1500, 1633.74, 1366.26, 1530.31, 1768.82, 1534.17],
        'glicko_p2'        : [1500, 1500   , 1475.26, 1696.91, 1335.06, 1472.12]
    }
    return pd.DataFrame(test_data)

# === [SIMPLE GLICKO] TEST TRUE VALUE ===
def test_compute_glicko_ratings_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test simple GLICKO rankings computation with valid inputs and known outcomes.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    initial_rating           = 1500.0
    initial_rating_deviation = 350.0
    q_factor                 = np.log(10) / 400

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        #    glicko_P1   |    glicko_P2   
        [ 1500           , 1500          ],
        [ 1633.7397715   , 1500          ],
        [ 1366.2602285   , 1475.26419237 ],
        [ 1530.31047181  , 1696.90666568 ],
        [ 1768.82248164  , 1335.05811361 ],
        [ 1534.17384111  , 1472.11700801 ],
        ])
   
    result = compute_glicko_ratings(matches_df               = sample_matches_df,
                                    initial_rating           = initial_rating,
                                    initial_rating_deviation = initial_rating_deviation,
                                    q_factor                 = q_factor)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [MOVEMENT GLICKO] TEST TRUE VALUE ===
def test_compute_glicko_movement_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test movement GLICKO rankings computation with valid inputs and known outcomes.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    lookback_matches = 2

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        #   glicko_P1    |   glicko_P2
        [  0             ,  0         ],
        [  0             ,  0         ],
        [  0             , -24.74     ],
        [  30.31         ,  0         ],
        [  268.82        , -298.68    ],
        [ -162.74        ,  105.86    ],
        ])
   
    result = compute_rating_movement(matches_df       = sample_matches_df, 
                                     lookback_matches = lookback_matches,
                                     rating_prefix    = "glicko")
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === TEST INPUT FUNCTION ===
# Define test value sets
INITIAL_RATINGS = [
    (-1_000, True , "initial_rating_negative"),
    (0     , True , "initial_rating_zero"),
    (1_000 , False, "initial_rating_low"),
    (1_500 , False, "initial_rating_standard"),
    (10_000, False, "initial_rating_high"),
]

INITIAL_DEVIATIONS = [
    (-200, True , "rating_dev_negative"),
    (0   , True , "rating_dev_zero"),
    (200 , False, "rating_dev_low"),
    (350 , False, "rating_dev_standard"),
    (1000, False, "rating_dev_high"),
]

Q_FACTORS = [
    (-1.0            , True , "q_factor_negative"),
    (0.0             , True , "q_factor_zero"),
    (1e-4            , False, "q_factor_low"),
    (np.log(10) / 400, False, "q_factor_standard"),
    (1.0             , False, "q_factor_high"),
]

# Build all combinations
params = []
for (ir_val, ir_err, ir_id), (rd_val, rd_err, rd_id), (q_val, q_err, q_id) in itertools.product(
    INITIAL_RATINGS, INITIAL_DEVIATIONS, Q_FACTORS
):
    # Error if ANY parameter is invalid
    should_raise = ir_err or rd_err or q_err
    test_id = f"{ir_id}__{rd_id}__{q_id}"
    params.append(pytest.param(ir_val, rd_val, q_val, should_raise, id=test_id))

@pytest.mark.parametrize("initial_rating, initial_rating_deviation, q_factor, should_raise_error", params)
def test_glicko_parameter_combinations(sample_matches_df: pd.DataFrame,
                                       initial_rating: int,
                                       initial_rating_deviation: int,
                                       q_factor: float,
                                       should_raise_error: bool) -> None:
    """
    Test all combinations of GLICKO parameters:
    - initial_rating
    - initial_rating_deviation
    - q_factor

    Ensures validation logic works for invalid values individually
    and in combination.
    """
    function_kwargs = {
        "initial_rating"          : initial_rating,
        "initial_rating_deviation": initial_rating_deviation,
        "q_factor"                : q_factor,
    }

    if should_raise_error:
        with pytest.raises(ValueError):
            compute_glicko_ratings(sample_matches_df, **function_kwargs)
    else:
        result = compute_glicko_ratings(sample_matches_df, **function_kwargs)
        assert result is not None

# === TEST MISSING COLUMNS ===
@pytest.mark.parametrize("missing_column", ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date'])
def test_ratings_raises_error_on_missing_columns(sample_matches_df: pd.DataFrame, missing_column: str):
    """
    Verifies that compute_glicko_ratings raises a ValueError if a column is missing.
    """
    invalid_df = sample_matches_df.drop(columns=[missing_column])
    
    # We check that a ValueError is raised and that the message contains the name
    # of the missing column to be even more precise.
    with pytest.raises(ValueError, match=f"Missing required columns: \\['{missing_column}'\\]"):
        compute_glicko_ratings(invalid_df)
