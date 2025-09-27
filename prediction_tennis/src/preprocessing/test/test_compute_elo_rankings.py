from typing import Callable
from prediction_tennis.src.preprocessing.features.compute_rating_movement import compute_rating_movement
from prediction_tennis.src.preprocessing.features.elo_ranking_features import compute_elo_rankings, compute_momentum_elo_rankings, compute_round_based_elo, compute_tournament_based_elo, compute_tournament_round_based_elo
import pytest
import pandas as pd
import numpy as np

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
        'elo_p1':           [1500, 1516, 1484, 1500.70246717, 1531.99844494, 1513.73701863],
        'elo_p2':           [1500, 1500, 1499.26369321, 1516.73630679, 1482.56122603, 1485.44032903]
    }
    return pd.DataFrame(test_data)

# === [SIMPLE ELO] TEST TRUE VALUE ===
def test_compute_elo_rankings_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test simple ELO rankings computation with valid inputs and known outcomes.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    k_factor = 32
    divisor = 400

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        #    ELO_P1   |    ELO_P2
        [1500         , 1500         ],
        [1516         , 1500         ],
        [1484         , 1499.26369321],
        [1500.70246717, 1516.73630679],
        [1531.99844494, 1482.56122603],
        [1513.73701863, 1485.44032903],
        ])
   
    result = compute_elo_rankings(matches_df=sample_matches_df,
                                  k_factor=k_factor,
                                  divisor=divisor)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [ROUND/TOURN ELO] TEST TRUE VALUE ===
def test_compute_tournament_round_based_elo_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test tournament and round-based ELO computation with valid inputs.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    k_factor = 32
    divisor = 400

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        #    ELO_P1   |    ELO_P2
        [1500         , 1500         ],
        [1512.8       , 1500         ],
        [1487.2       , 1499.52864381],
        [1500.45401348, 1513.27135619],
        [1528.06496309, 1486.27463033],
        [1501.19203085, 1485.66040658],
        ])
   
    result = compute_tournament_round_based_elo(matches_df=sample_matches_df,
                                                k_factor=k_factor,
                                                divisor=divisor)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [TOURN ELO] TEST TRUE VALUE ===
def test_compute_tournament_based_elo_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test tournament-based ELO computation with valid inputs.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    k_factor = 32
    divisor = 400

    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        #    ELO_P1   |    ELO_P2
        [1500         , 1500         ],
        [1512.8       , 1500         ],
        [1487.2       , 1499.52864381],
        [1500.45401348, 1513.27135619],
        [1525.59936194, 1486.27463033],
        [1507.79608515, 1488.12600773],
        ])
   
    result = compute_tournament_based_elo(matches_df=sample_matches_df,
                                          k_base=k_factor,
                                          divisor=divisor)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [ROUND ELO] TEST TRUE VALUE ===
def test_compute_round_based_elo_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test round-based ELO computation with valid inputs.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    """Test with valid inputs and known outcomes."""
    k_factor = 32
    divisor = 400
    # Expected ratings after each match for all players (P1, P2)
    expected_ratings = np.array([
        #    ELO_P1   |    ELO_P2
        [1500         , 1500         ],
        [1516         , 1500         ],
        [1484         , 1499.26369321],
        [1500.70246717, 1516.73630679],
        [1535.05087256, 1482.56122603],
        [1507.45235264, 1482.3879014 ],
        ])
   
    result = compute_round_based_elo(matches_df=sample_matches_df,
                                                k_base=k_factor,
                                                divisor=divisor)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [MOMENTUM ELO] TEST TRUE VALUE ===
def test_compute_momentum_elo_rankings_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test momentum ELO rankings computation with valid inputs.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    k_factor = 32
    divisor = 400

    # Expected ratings and momentum after each match for all players
    expected_ratings = np.array([[
        # ELO ratings (Player1, Player2)
        [1500         , 1500         ],
        [1516         , 1500         ],
        [1484         , 1499.26369321],
        [1500.70246717, 1516.73630679],
        [1531.99844494, 1482.56122603],
        [1513.73701863, 1485.44032903],
        ],
        # Momentum values (Player1, Player2)
        [[ 0          , 0           ],
         [ 16         , 0           ],
         [ -16        , -2.33630679 ], 
         [ 2.30246717 , 16.73630679 ], 
         [ 30.32481426, -18.80514329], 
         [ 9.03090653 , -13.18991769],

        ]])
   
    result = compute_momentum_elo_rankings(matches_df=sample_matches_df,
                                  k_base=k_factor,
                                  divisor=divisor)
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === [MOVEMENT ELO] TEST TRUE VALUE ===
def test_compute_elo_movement_valid_inputs(sample_matches_df: pd.DataFrame) -> None:
    """
    Test ELO movement computation with valid inputs.
    
    Args:
        sample_matches_df: Sample tennis match data for testing.
    """
    lookback_matches = 2

    # Expected ELO movement after each match for all players
    expected_ratings = np.array([
        #    ELO_P1   |    ELO_P2
        [  0          , 0           ], 
        [  0          , 0           ], 
        [  0          , -0.73630679 ], 
        [  0.70246717 , 0.          ],
        [ 31.99844494 , -33.43877397],
        [ -2.99928816 , 1.44032903  ],
        ])
   
    result = compute_rating_movement(matches_df      = sample_matches_df,
                                    lookback_matches = lookback_matches,
                                    rating_prefix    = "elo"
                                    )
    np.testing.assert_array_almost_equal(result, expected_ratings, decimal=2)

# === TEST K FACTOR ===
@pytest.mark.parametrize("elo_function, parameter_name", [
    (compute_elo_rankings              , "k_factor"),
    (compute_tournament_round_based_elo, "k_factor"),
    (compute_tournament_based_elo      , "k_base"),
    (compute_round_based_elo           , "k_base"),
    (compute_momentum_elo_rankings     , "k_base")
])
@pytest.mark.parametrize("k_value, should_raise_error", [   
    pytest.param(-10    , True, id="k_factor_negative"),
    pytest.param(0      , True, id="k_factor_zero"),
    pytest.param(16     , False, id="k_factor_low"),
    pytest.param(32     , False, id="k_factor_standard"),
    pytest.param(64     , False, id="k_factor_high"),
])
def test_k_factor_validation(elo_function: Callable,
                             parameter_name: str,
                             sample_matches_df: pd.DataFrame,
                             k_value: int,
                             should_raise_error: bool) -> None:
    """
    Test K-factor parameter validation across different ELO functions.
    
    Args:
        elo_function: The ELO computation function to test.
        parameter_name: Name of the K-factor parameter for this function.
        sample_matches_df: Sample tennis match data for testing.
        k_value: K-factor value to test.
        should_raise_error: Whether this K-factor should raise a ValueError.
    """
    function_kwargs = {parameter_name: k_value}
    
    if should_raise_error:
        with pytest.raises(ValueError):
            elo_function(sample_matches_df, **function_kwargs)
    else:
        computed_result = elo_function(sample_matches_df, **function_kwargs)
        assert computed_result is not None

# === TEST DIVISOR ===
@pytest.mark.parametrize("elo_function, parameter_name", [
    (compute_elo_rankings              , "k_factor"),
    (compute_tournament_round_based_elo, "k_factor"),
    (compute_tournament_based_elo      , "k_base"),
    (compute_round_based_elo           , "k_base"),
    (compute_momentum_elo_rankings     , "k_base")
])
@pytest.mark.parametrize("divisor_value, should_raise_error", [
    pytest.param(-100, True , id="divisor_negative"),
    pytest.param(0   , True , id="divisor_zero"),
    pytest.param(200 , False, id="divisor_low"),
    pytest.param(400 , False, id="divisor_standard"),
    pytest.param(800 , False, id="divisor_high"),
])
def test_divisor_validation(elo_function: Callable,
                            parameter_name: str,
                            sample_matches_df: pd.DataFrame,
                            divisor_value: int,
                            should_raise_error: bool) -> None:
    """
    Test divisor parameter validation across different ELO functions.
    
    Args:
        elo_function: The ELO computation function to test.
        parameter_name: Name of the K-factor parameter for this function.
        sample_matches_df: Sample tennis match data for testing.
        divisor_value: Divisor value to test.
        should_raise_error: Whether this divisor should raise a ValueError.
    """
    function_kwargs = {parameter_name: 32, "divisor": divisor_value}
    
    if should_raise_error:
        with pytest.raises(ValueError):
            elo_function(sample_matches_df, **function_kwargs)
    else:
        computed_result = elo_function(sample_matches_df, **function_kwargs)
        assert computed_result is not None

# === TEST MISSING COLUMNS ===
# Generate test cases
test_cases = []

# elo base
for missing_column in ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date']:
    test_cases.append((compute_elo_rankings              , "k_factor", missing_column))
    test_cases.append((compute_tournament_round_based_elo, "k_factor", missing_column))
    test_cases.append((compute_tournament_based_elo      , "k_base"  , missing_column))
    test_cases.append((compute_round_based_elo           , "k_base"  , missing_column))

# compute_momentum_elo_rankings
for missing_column in ['player1_id_factor', 'player2_id_factor', 'winner', 'match_date']:
    test_cases.append((compute_momentum_elo_rankings, "k_base", missing_column))

@pytest.mark.parametrize("elo_function, parameter_name, missing_column", test_cases)
def test_compute_elo_rankings_missing_columns(elo_function: Callable,
                                             parameter_name: str,
                                             sample_matches_df: pd.DataFrame,
                                             missing_column: str) -> None:
    """
    Test error handling when required columns are missing from DataFrame.
    
    Args:
        elo_function: The ELO computation function to test.
        parameter_name: Name of the K-factor parameter for this function.
        sample_matches_df: Sample tennis match data for testing.
        missing_column: Name of the column to remove from the DataFrame.
    """
    # Create DataFrame copy with the specified column removed
    invalid_dataframe = sample_matches_df.drop(columns=[missing_column])
    function_kwargs = {parameter_name: 32}

    with pytest.raises((KeyError, AttributeError)):
        elo_function(invalid_dataframe, **function_kwargs)
