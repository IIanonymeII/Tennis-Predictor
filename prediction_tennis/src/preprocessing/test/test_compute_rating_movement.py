# === TEST LOOKBACK_MATCHES ===
import pandas as pd
import pytest

from prediction_tennis.src.preprocessing.features.compute_rating_movement import compute_rating_movement

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

@pytest.mark.parametrize("lookback_matches, should_raise_error", [
    pytest.param(-2 , True , id="lookback_matches_negative"),
    pytest.param(0  , True , id="lookback_matches_zero"),
    pytest.param(1  , False, id="lookback_matches_low"),
    pytest.param(5  , False, id="lookback_matches_standard"),
    pytest.param(15 , False, id="lookback_matches_high"),
])
def test_lookback_matches_validation(sample_matches_df: pd.DataFrame,
                                     lookback_matches: int,
                                     should_raise_error: bool) -> None:
    """
    Test lookback_matches parameter validation movement computation.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
        lookback_matches: Number of matches to look back for movement calculation.
        should_raise_error: Whether this value should raise a ValueError.
    """    
    function_kwargs = {"lookback_matches": lookback_matches,
                       "rating_prefix": "trueskill"}
    
    if should_raise_error:
        with pytest.raises(ValueError):
            compute_rating_movement(sample_matches_df, **function_kwargs)
    else:
        computed_result = compute_rating_movement(sample_matches_df, **function_kwargs)
        assert computed_result is not None
