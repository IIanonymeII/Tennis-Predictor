# Tennis-Predictor – Preprocessing / Features

This folder contains **feature engineering functions** used to transform raw tennis match data into model-ready features.  
Currently, it focuses on [**Elo ranking features**](https://en.wikipedia.org/wiki/Elo_rating_system).

---
## 📂 Structure

```
features/
│
├── __init__.py
├── elo_ranking_features.py # Functions for Elo rating 
└── README.md               
```

---

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
>   - **Movement during last *n* matches**: Tracks Elo variations over a rolling match window  

---

## 💻 Usage

Import simple Elo feature functions into your pipeline:

```python
from prediction_tennis.src.preprocessing.features.elo_ranking_features import compute_elo_rankings

# Example usage
elo_df = compute_elo_rankings(matches_df, k_factor=32)
```