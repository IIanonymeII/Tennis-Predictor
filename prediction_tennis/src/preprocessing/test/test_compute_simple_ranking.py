import itertools
from typing import Callable, List, Optional, Tuple
import numpy as np
import pandas as pd
import pytest

from prediction_tennis.src.preprocessing.features.simple_ranking_features import compute_simple_ranking, compute_transformed_winloss_rankings


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
    }
    return pd.DataFrame(test_data)


# === [SIMPLE] TEST TRUE VALUE ===
def test_compute_simple_ranking_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test simple rankings computation with valid inputs and known outcomes.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    win_step              = 1.0
    lose_step             = 1.0
    transformation_method = "power"
    transformation_factor = 1.0

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        [ 0,  0 ],
        [ 1,  0 ],
        [-1,  0 ],
        [ 0,  1 ],
        [ 2, -1 ],
        [ 1, -1 ],
        ])
   
    result = compute_simple_ranking(matches_df = sample_matches_df,
                                    win_step= win_step,
                                    lose_step=lose_step,
                                    transformation_factor=transformation_factor,
                                    transformation_method=transformation_method)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [SIMPLE WINLOSS] TEST TRUE VALUE ===
def test_compute_transformed_winloss_rankings_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test simple rankings computation with valid inputs and known outcomes.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    win_step              = 5.0
    lose_step             = 3.2
    transformation_method = "log-exp"

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        [-1         , -1         ],
        [ 0.79175947, -1         ],
        [-1.03251751,  0.75924196],
        [ 0.75924196,  0.79175947],
        [ 1.39789527,  0.72566707],
        [ 1.36537777,  0.72566707],
        ])
   
    result = compute_transformed_winloss_rankings(matches_df = sample_matches_df,
                                    win_step= win_step,
                                    lose_step=lose_step,
                                    transformation_method=transformation_method)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === TEST INPUT FUNCTION ===
# === Parameter Value Sets ===
WIN_STEP: List[Tuple[Optional[float], bool, str]] = [
    (None, True , "None"),
    (-1  , True , "negative"),
    (0   , True , "zero"),
    (1   , False, "low"),
    (1.5 , False, "standard"),
    (20  , False, "high"),
]

LOSE_STEP: List[Tuple[Optional[float], bool, str]] = [
    (None, True , "None"),
    (-1  , True , "negative"),
    (0   , True , "zero"),
    (1   , False, "low"),
    (1.5 , False, "standard"),
    (20  , False, "high"),
]

TRANSFORMATION_METHOD: List[Tuple[Optional[str], bool, str]] = [
    (None           , True , "None"),
    (2              , True , "not_str"),
    ("exp power"    , True , "missing_dash"),
    ("power"        , False, "valid"),
    ("exp"          , False, "valid"),
    ("log"          , False, "valid"),
    ("power-log"    , False, "valid"),
    ("power-exp"    , False, "valid"),
    ("log-exp"      , False, "valid"),
    ("log-power"    , False, "valid"),
    ("exp-log"      , False, "valid"),
    ("exp-power"    , False, "valid"),
]

TRANSFORMATION_FACTOR: List[Tuple[Optional[float], bool, str]] = [
    (None, True , "None"),
    (-1  , True , "negative"),
    (0   , True , "zero"),
    (1   , False, "low"),
    (1.5 , False, "standard"),
    (2   , False, "high"),
]

# === Helper Function to Build Param Grid ===
def build_params(with_factor: bool = True) -> List[pytest.param]:
    """Generate parameter combinations for ranking functions with test IDs."""
    params = []
    if with_factor:
        for ws, ls, tm, tf in itertools.product(WIN_STEP, LOSE_STEP, TRANSFORMATION_METHOD, TRANSFORMATION_FACTOR):
            ws_val, ws_err, ws_id = ws
            ls_val, ls_err, ls_id = ls
            tm_val, tm_err, tm_id = tm
            tf_val, tf_err, tf_id = tf
            should_raise = ws_err or ls_err or tm_err or tf_err
            test_id = f"win_{ws_id}__lose_{ls_id}__method_{tm_id}__factor_{tf_id}"
            params.append(pytest.param(ws_val, ls_val, tm_val, tf_val, should_raise, id=test_id))
    else:
        for ws, ls, tm in itertools.product(WIN_STEP, LOSE_STEP, TRANSFORMATION_METHOD):
            ws_val, ws_err, ws_id = ws
            ls_val, ls_err, ls_id = ls
            tm_val, tm_err, tm_id = tm
            should_raise = ws_err or ls_err or tm_err
            test_id = f"win_{ws_id}__lose_{ls_id}__method_{tm_id}"
            params.append(pytest.param(ws_val, ls_val, tm_val, should_raise, id=test_id))
    return params

PARAMS_WITH_FACTOR = build_params(with_factor=True)
PARAMS_WITHOUT_FACTOR = build_params(with_factor=False)

# === Test Functions ===
@pytest.mark.parametrize(
    "win_step, lose_step, transformation_method, transformation_factor, should_raise",
    PARAMS_WITH_FACTOR,
)
def test_compute_simple_ranking(
    sample_matches_df: pd.DataFrame,
    win_step: Optional[float],
    lose_step: Optional[float],
    transformation_method: Optional[str],
    transformation_factor: Optional[float],
    should_raise: bool,
) -> None:
    """Test compute_simple_ranking with all valid/invalid parameter combinations."""
    kwargs = {
        "win_step": win_step,
        "lose_step": lose_step,
        "transformation_method": transformation_method,
        "transformation_factor": transformation_factor,
    }

    if should_raise:
        with pytest.raises((ValueError, TypeError)):
            compute_simple_ranking(sample_matches_df, **kwargs)
    else:
        result = compute_simple_ranking(sample_matches_df, **kwargs)
        assert isinstance(result, np.ndarray)
        assert result.size > 0

@pytest.mark.parametrize(
    "win_step, lose_step, transformation_method, should_raise",
    PARAMS_WITHOUT_FACTOR,
)
def test_compute_transformed_winloss_rankings(
    sample_matches_df: pd.DataFrame,
    win_step: Optional[float],
    lose_step: Optional[float],
    transformation_method: Optional[str],
    should_raise: bool,
) -> None:
    """Test compute_transformed_winloss_rankings with all valid/invalid parameter combinations."""
    kwargs = {
        "win_step": win_step,
        "lose_step": lose_step,
        "transformation_method": transformation_method,
    }

    if should_raise:
        with pytest.raises((ValueError, TypeError)):
            compute_transformed_winloss_rankings(sample_matches_df, **kwargs)
    else:
        result = compute_transformed_winloss_rankings(sample_matches_df, **kwargs)
        assert isinstance(result, np.ndarray)
        assert result.size > 0

# === TEST MISSING COLUMNS ===
@pytest.mark.parametrize("simple_func",[compute_simple_ranking, compute_transformed_winloss_rankings])
@pytest.mark.parametrize("missing_column", ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date'])
def test_ratings_raises_error_on_missing_columns(sample_matches_df: pd.DataFrame, 
                                                 simple_func: Callable,
                                                 missing_column: str):
    """
    Verifies that simple rating raises a ValueError if a column is missing.
    """
    invalid_df = sample_matches_df.drop(columns=[missing_column])
    
    # We check that a ValueError is raised and that the message contains the name
    # of the missing column to be even more precise.
    with pytest.raises(ValueError, match=f"Missing required columns: \\['{missing_column}'\\]"):
        simple_func(invalid_df)
