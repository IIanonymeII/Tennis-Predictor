# Tennis-Predictor – Preprocessing / Features

This folder contains **feature engineering functions** used to transform raw tennis match data into model-ready features.  
These features are used to capture player strength and momentum, making them critical inputs for predictive models.
---
## 📂 Structure

```
features/
│
├── __init__.py
├── elo_ranking_features.py       # Functions for Elo rating 
├── trueskill_ranking_features.py # Functions for Trueskill rating 
├── glicko_ranking_features.py    # Functions for Trueskill rating 
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

>**`trueskill_ranking_features.py`**
 Implements TrueSkill ratings for tennis match data.
  Supported variants include:
>
>   - **Standard Trueskill**: Classic rating update system  
>   - **Movement during last *n* matches**: Tracks Trueskill variations over a rolling match window  

>**`glicko_ranking_features.py`**
 Implements Glicko ratings for tennis match data.
  Supported variants include:
>
>   - **Standard Glicko**: Classic rating update system  
>   - **Movement during last *n* matches**: Tracks Glicko variations over a rolling match window  


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