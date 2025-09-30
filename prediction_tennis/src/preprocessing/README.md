# Tennis-Predictor – Preprocessing

This module handles all **data preparation steps** required before training and evaluating models.  
It transforms raw match data into **clean, structured, and feature-rich datasets**, ensuring consistency across the pipeline.

## 📂 Structure

```
preprocessing/
  ├── __init.py__ 
  ├── features/
  ├── test/
  ├── utils/
  ├── main_cleaning.ipynb
  ├── main_feature.ipynb
  └── README.md   
```

---
## ⚙️ Responsibilities
> - **`features/`**  
 Implements domain-specific feature engineering:
>  - Match statistics (games won/lost per set, tiebreak ratios, etc.)
>  - Ranking-based metrics (Elo, Trueskill, Glicko, momentum, round/tournament adjustments)
>  - Head-to-head derived features

>- **`test/`**
 Contains **pytest** suites ensuring:
>  - Data integrity checks  
>  - Correctness of feature calculations  
>  - Robustness against missing/invalid values 

>- **`utils/`**
 Provides reusable tools such as:
>  - Data cleaning pipelines  
>  - Standardization/scaling utilities  
>  - Helper functions for column pairing (p1 vs. p2)  

> - **`main_cleaning.ipynb`**  
  Entry point for raw data cleaning. It concatenates all raw data and starts the cleaning process.  
  Uses [fuzzywuzzy](https://pypi.org/project/fuzzywuzzy/) to match and link tournaments between `Flashscore` and `Wikipedia`, as well as to reconcile player data between `ATPTour` and `Flashscore`.

> - **`main_feature.ipynb`**  
  Main notebook for feature engineering. Generates advanced features from the cleaned dataset. 
  Includes Elo, Trueskill, Glicko ratings. Adds last-match statistics, match-level stats (sets, scores, etc.), and derived metrics

## 💻 Usage

### Run Preprocessing & Feature Engineering

1. Open and execute all cells in **`main_cleaning.ipynb`** to perform data concatenation and cleaning.  
2. Open and execute all cells in **`main_feature.ipynb`** to generate engineered features from the cleaned data.
3. ...