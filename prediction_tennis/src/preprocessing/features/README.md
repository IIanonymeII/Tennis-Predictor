# Tennis-Predictor – Preprocessing / Features

This folder contains **feature engineering functions** used to transform raw tennis match data into model-ready features.  
These features are used to capture player strength and momentum, making them critical inputs for predictive models.


## 📂 Structure

```
features/
│
├── __init__.py
├── elo_ranking_features.py       # Functions for Elo rating 
├── trueskill_ranking_features.py # Functions for Trueskill rating 
├── glicko_ranking_features.py    # Functions for Glicko rating 
├── simple_ranking_features.py    # Functions for Simple rating 
├── popularity_player_features.py # Functions for Popularity rating
├── compute_rating_movement.py    # Calculates rating movements between matches 
└── README.md               
```

## ⚙️ Responsibilities

>**`elo_ranking_features.py`**
 Implements Elo rating calculations adapted for tennis
  Supported variants include:
>
>   - **Standard Elo**: Classic rating update system  
>   - **Tournament and Round-based adjustments**: Weights matches by both level and round importance  
>   - **Tournament-based adjustments**: Scales Elo updates by event prestige (e.g., Grand Slam vs. ATP 250)  
>   - **Round-based weighting**: Adjusts K-factor based on round progression (e.g., final vs. round of 32)
>   - **Momentum-aware Elo**: Incorporates player momentum from recent performances  

>**`trueskill_ranking_features.py`**
 Implements TrueSkill ratings for tennis match data.
  Supported variants include:
>
>   - **Standard Trueskill**: Classic rating update system  

>**`glicko_ranking_features.py`**
 Implements Glicko ratings for tennis match data.
  Supported variants include:
>
>   - **Standard Glicko**: Classic rating update system  

>**`simple_ranking_features.py`**
 Implements Simple ratings for tennis match data.
  Supported variants include:
>
>   - **Standard rating**: Adds `win_step` for a win and subtracts `lose_step` for a loss.
>   - **Transformed ratings (exp, log, power):**: Applies a mathematical transformation to the standard rating. For example, the result can be `exp(value + step)`, `log(value + step)`, or `power(value + step)` depending on the chosen transformation method.

>**`popularity_player_features.py`** 
  calculates player popularity based on past tournament performance.
Players gain popularity by playing more matches and advancing further in important rounds or tournaments.
Players with few or no games are considered less popular.

>**`compute_rating_movement.py`**
 Computes the rating movement for tennis players by comparing their current pre-match rating with ratings from a specified number of matches ago. This module tracks how player ratings change over time based on match outcomes and provides insights into rating volatility.
  Supported variants include:
>
>   - **Movement during last *n* matches**: Tracks variations over a rolling match window  

---

## 📘 Documentation

### 1- Elo Rating  
- [🔗 Elo Rating System (Wikipedia)](https://en.wikipedia.org/wiki/Elo_rating_system)  

### 2- TrueSkill  
- [📄 Original Paper – NIPS 2006](https://proceedings.neurips.cc/paper_files/paper/2006/file/f44ee263952e65b3610b8ba51229d1f9-Paper.pdf)  
- [🔗 TrueSkill (Wikipedia)](https://en.wikipedia.org/wiki/TrueSkill) 

### 3- Glicko   
- [🔗 Glicko (Wikipedia)](https://en.wikipedia.org/wiki/Glicko_rating_system) 

---

## 💻 Usage

Import simple Elo feature functions into your pipeline:

```python
from prediction_tennis.src.preprocessing.features.elo_ranking_features import compute_elo_rankings

# Example usage
elo_df = compute_elo_rankings(matches_df, k_factor=32)
```