import itertools
import numpy as np
import pandas as pd
import pytest

from prediction_tennis.src.preprocessing.features.last_match_played import compute_match_count_ratios

@pytest.fixture
def sample_matches_df() -> pd.DataFrame:
    """
    Create a DataFrame with sample tennis match data for testing.
    
    Returns:
        pd.DataFrame: Test dataset containing player IDs, winners, tournament
                     types, rounds, match dates, and expected ELO ratings.
    """
    test_data = {
        'player1_id_factor': [1  , 1  , 2  , 2  , 3  , 3   ],
        'player2_id_factor': [2  , 3  , 1  , 3  , 1  , 2   ],
        'winner'           : [1  , 2  , 1  , 2  , 2  , 2   ],
        'type'             : [250, 250, 250, 250, 500, 1000],
        'round'            : [32 , 16 , 8  , 4  , 2  , 1   ],
        'match_date'       : ['2023-01-01', '2023-01-02', '2023-01-03',
                              '2023-01-04', '2023-01-05', '2023-01-06'],
    }
    df_test = pd.DataFrame(test_data)
    df_test["timestamp"] = pd.to_datetime(df_test["match_date"])
    return df_test


# === [SIMPLE POPULARITY] TEST TRUE VALUE ===
def test_compute_player_popularity_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    
    # Define computation parameters
    period_days: int = 2
    use_ratio  : bool = False

    # Expected ratings after each match (rows = matches, columns = [P1, P2])
    expected_ratings: np.ndarray = np.array([[ 0 , 0 ],
                                             [ 1 , 0 ],
                                             [ 1 , 2 ],
                                             [ 1 , 1 ],
                                             [ 1 , 1 ],
                                             [ 2 , 1 ]])

    # Compute player popularity ratings using the function under test
    result: np.ndarray = compute_match_count_ratios(
        matches_df=sample_matches_df,
        period_days=period_days,
        use_ratio=use_ratio,
    )

    # Assert that the computed ratings match the expected ratings within 2 decimals
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === TEST PARAMETERS ===
PERIOD_DAYS = [ 
    (None, True , "None"),
    ("3" , True , "str"),
    (-1  , True , "negative"),
    (0   , True , "zero"),
    (1   , False, "positive"),
    (30  , False, "large_positive"),
]

USE_RATIO = [
    (None , True , "None"),
    ("3"  , True , "str"),
    (0    , True , "int"),
    (True , False, "True"),
    (False, False, "False"),
]

# === BUILD ALL TEST COMBINATIONS ===
params = []
for (pd_val, pd_err, pd_id), (ur_val, ur_err, ur_id) in itertools.product(
    PERIOD_DAYS, USE_RATIO ):
    # If ANY parameter is invalid, expect an exception
    should_raise = pd_err or ur_err
    test_id = f"{pd_id}__{ur_id}"
    params.append(pytest.param(pd_val, ur_val, should_raise, id=test_id))

# === PARAMETRIZED TEST FUNCTION ===
@pytest.mark.parametrize("period_days, use_ratio, should_raise", params)
def test_compute_match_input_value(
    sample_matches_df: pd.DataFrame,
    period_days,
    use_ratio,
    should_raise: bool) -> None:

    kwargs = {"period_days": period_days, "use_ratio": use_ratio }
    if should_raise:
        with pytest.raises((ValueError, TypeError)):
            compute_match_count_ratios(sample_matches_df, **kwargs)
    else:
        result = compute_match_count_ratios(sample_matches_df, **kwargs)
        assert isinstance(result, np.ndarray), "Result should be a numpy array"
        assert result.size > 0, "Result array should not be empty"
