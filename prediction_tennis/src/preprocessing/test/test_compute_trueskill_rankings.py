from typing import Callable
import numpy as np
import pandas as pd
import pytest

from prediction_tennis.src.preprocessing.features.trueskill_ranking_features import compute_trueskill_movement, compute_trueskill_ratings


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
        'trueskill_p1'     : [25, 29.4, 20.6 , 25.69, 33.39, 26.91],
        'trueskill_p2'     : [25, 25  , 24.95, 31   , 21.07, 23.86]
    }
    return pd.DataFrame(test_data)

# === [SIMPLE TRUESKILL] TEST TRUE VALUE ===
def test_compute_trueskill_ratings_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test simple TRUESKILL rankings computation with valid inputs and known outcomes.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        # trueskill_P1   | trueskill_P2
        [25              , 25          ],
        [29.39583202     , 25          ],
        [20.60416798     , 24.95424668 ],
        [25.69325383     , 30.99712719 ],
        [33.39287231     , 21.07020947 ],
        [26.91494024     , 23.85893865 ],
        ])
   
    result = compute_trueskill_ratings(matches_df=sample_matches_df)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [MOVEMENT TRUESKILL] TEST TRUE VALUE ===
def test_compute_trueskill_movement_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test movement TRUESKILL rankings computation with valid inputs and known outcomes.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    matches_lookback = 2

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        # trueskill_P1   | trueskill_P2
        [     0          ,     0       ],
        [     0          ,     0       ],
        [     0          ,     -0.05   ],
        [     0.69       ,     0       ],
        [     8.39       ,     -8.33   ],
        [    -4.09       ,     3.26    ],
        ])
   
    result = compute_trueskill_movement(matches_df=sample_matches_df, matches_lookback=matches_lookback)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === TEST LOOKBACK_MATCHES ===
@pytest.mark.parametrize("matches_lookback, should_raise_error", [
    pytest.param(-2 , True , id="lookback_matches_negative"),
    pytest.param(0  , True , id="lookback_matches_zero"),
    pytest.param(1  , False, id="lookback_matches_low"),
    pytest.param(5  , False, id="lookback_matches_standard"),
    pytest.param(15 , False, id="lookback_matches_high"),
])
def test_lookback_matches_validation(sample_matches_df: pd.DataFrame,
                                     matches_lookback: int,
                                     should_raise_error: bool) -> None:
    """
    Test matches_lookback parameter validation for TRUESKILL movement computation.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
        matches_lookback: Number of matches to look back for movement calculation.
        should_raise_error: Whether this value should raise a ValueError.
    """    
    function_kwargs = {"matches_lookback": matches_lookback}
    
    if should_raise_error:
        with pytest.raises(ValueError):
            compute_trueskill_movement(sample_matches_df, **function_kwargs)
    else:
        computed_result = compute_trueskill_movement(sample_matches_df, **function_kwargs)
        assert computed_result is not None

# === TEST MISSING COLUMNS ===
@pytest.mark.parametrize("missing_column", ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date'])
def test_ratings_raises_error_on_missing_columns(sample_matches_df: pd.DataFrame, missing_column: str):
    """
    Verifies that compute_trueskill_ratings raises a ValueError if a column is missing.
    """
    invalid_df = sample_matches_df.drop(columns=[missing_column])
    
    # We check that a ValueError is raised and that the message contains the name
    # of the missing column to be even more precise.
    with pytest.raises(ValueError, match=f"Missing required columns: \\['{missing_column}'\\]"):
        compute_trueskill_ratings(invalid_df)

@pytest.mark.parametrize("missing_column", ['player1_id_factor', 'player2_id_factor', 'match_date', 'trueskill_p1', 'trueskill_p2'])
def test_movement_raises_error_on_missing_columns(sample_matches_df: pd.DataFrame, missing_column: str):
    """
    Verifies that compute_trueskill_movement raises a ValueError if a column is missing.
    """
    # For this test, we first need to add the trueskill columns
    # before removing one for the test case.    
    invalid_df = sample_matches_df.drop(columns=[missing_column])
    
    with pytest.raises(ValueError, match=f"Missing required columns: \\['{missing_column}'\\]"):
        compute_trueskill_movement(invalid_df, matches_lookback=2)
