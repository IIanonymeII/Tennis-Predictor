from datetime import timedelta
import itertools
import numpy as np
import pandas as pd
import pytest

from prediction_tennis.src.preprocessing.features.popularity_player_features import FactorInclusion, PopularityMethod, PopularityPeriod, compute_player_popularity_before_match


@pytest.fixture
def sample_matches_df() -> pd.DataFrame:
    """
    Create a DataFrame with sample tennis match data for testing.
    
    Returns:
        pd.DataFrame: Test dataset containing player IDs, winners, tournament
                     types, rounds, match dates, and expected ELO ratings.
    """
    test_data = {
        'match_id'         : [1  , 2  , 3  , 4  , 5  , 6   ],
        'player1_id_factor': [1  , 1  , 2  , 2  , 3  , 3   ],
        'player2_id_factor': [2  , 3  , 1  , 3  , 1  , 2   ],
        'winner'           : [1  , 2  , 1  , 2  , 2  , 2   ],
        'type'             : [250, 250, 250, 250, 500, 1000],
        'round'            : [32 , 16 , 8  , 4  , 2  , 1   ],
        'match_date'       : ['2023-01-01', '2023-01-02', '2023-01-03',
                              '2023-01-04', '2023-01-05', '2023-01-06']
    }
    return pd.DataFrame(test_data)

# === [SIMPLE POPULARITY] TEST TRUE VALUE ===
def test_compute_player_popularity_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test player popularity computation with valid input data.

    Verifies that `compute_player_popularity_before_match` returns the expected
    ratings for each player before each match in a sample DataFrame.

    Parameters
    ----------
    sample_matches_df : pd.DataFrame
        Sample tennis match data used for testing. Must include required 
        player and match information.

    Returns
    -------
    None

    Raises
    ------
    AssertionError
        If the computed ratings do not match the expected ratings.
    """
    # Define computation parameters
    method: PopularityMethod = PopularityMethod.MULTIPLICATIVE
    factor_inclusion: FactorInclusion = FactorInclusion.BOTH
    time_window: PopularityPeriod = PopularityPeriod.ALL_TIME

    # Expected ratings after each match (rows = matches, columns = [P1, P2])
    expected_ratings: np.ndarray = np.array([
        [0.0, 0.0],
        [1.2, 0.0],
        [1.2, 2.7],
        [3.2, 1.5],
        [4.0, 4.7],
        [10.0, 5.7],
    ])

    # Compute player popularity ratings using the function under test
    result: np.ndarray = compute_player_popularity_before_match(
        df=sample_matches_df,
        methods=method,
        factor_inclusion=factor_inclusion,
        time_window=time_window
    )

    # Assert that the computed ratings match the expected ratings within 2 decimals
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === TEST PARAMETERS ===
METHODS = [
    (None                           , True , "None"),
    ("multiplicative"               , True , "str"),
    (PopularityMethod.MULTIPLICATIVE, False, "MULTIPLICATIVE"),
    (PopularityMethod.HARMONIC_MEAN , False, "HARMONIC_MEAN"),
]

FACTOR_INCLUSION = [
    (None                      , True , "None"),
    ("multiplicative"          , True , "str"),
    (FactorInclusion.BOTH      , False, "BOTH"),
    (FactorInclusion.ROUND_ONLY, False, "ROUND_ONLY"),
]

TIME_WINDOW = [
    (None                         , True , "None"),
    (90                           , True , "int"),
    (timedelta(days=90)           , True , "timedelta"),
    (PopularityPeriod.THREE_MONTHS, False, "THREE_MONTHS"),
    (PopularityPeriod.ALL_TIME    , False, "ALL_TIME"),
]

# === BUILD ALL TEST COMBINATIONS ===
params = []
for (m_val, m_err, m_id), (fi_val, fi_err, fi_id), (tw_val, tw_err, tw_id) in itertools.product(
    METHODS, FACTOR_INCLUSION, TIME_WINDOW
):
    # If ANY parameter is invalid, expect an exception
    should_raise = m_err or fi_err or tw_err
    test_id = f"{m_id}__{fi_id}__{tw_id}"
    params.append(pytest.param(m_val, fi_val, tw_val, should_raise, id=test_id))

# === PARAMETRIZED TEST FUNCTION ===
@pytest.mark.parametrize("methods, factor_inclusion, time_window, should_raise", params)
def test_compute_simple_ranking(
    sample_matches_df: pd.DataFrame,
    methods,
    factor_inclusion,
    time_window,
    should_raise: bool,
) -> None:
    """
    Test compute_player_popularity_before_match for valid and invalid inputs.

    - Checks that valid inputs return a non-empty numpy array.
    - Checks that invalid inputs raise ValueError or TypeError.
    """
    kwargs = {
        "methods": methods,
        "factor_inclusion": factor_inclusion,
        "time_window": time_window,
    }

    if should_raise:
        with pytest.raises((ValueError, TypeError)):
            compute_player_popularity_before_match(sample_matches_df, **kwargs)
    else:
        result = compute_player_popularity_before_match(sample_matches_df, **kwargs)
        assert isinstance(result, np.ndarray), "Result should be a numpy array"
        assert result.size > 0, "Result array should not be empty"

if __name__ == "__main__":
    test_data = {
        'match_id'         : [1  , 2  , 3  , 4  , 5  , 6   ],
        'player1_id_factor': [1  , 1  , 2  , 2  , 3  , 3   ],
        'player2_id_factor': [2  , 3  , 1  , 3  , 1  , 2   ],
        'winner'           : [1  , 2  , 1  , 2  , 2  , 2   ],
        'type'             : [250, 250, 250, 250, 500, 1000],
        'round'            : [32 , 16 , 8  , 4  , 2  , 1   ],
        'match_date'       : ['2023-01-01', '2023-01-02', '2023-01-03',
                              '2023-01-04', '2023-01-05', '2023-01-06']
    }
    test_df = pd.DataFrame(test_data)



    methods          = PopularityMethod.HARMONIC_MEAN
    factor_inclusion = FactorInclusion.ROUND_ONLY
    time_window      = PopularityPeriod.ALL_TIME
    
    test_compute_player_popularity_valid_inputs(sample_matches_df = test_df,)