# Tennis-Predictor – Preprocessing

This module handles all **data preparation steps** required before training and evaluating models.  
It transforms raw match data into **clean, structured, and feature-rich datasets**, ensuring consistency across the pipeline.

---
## 📂 Structure

```
── preprocessing/
|    ├── features/
|    ├── test/
|    ├── utils/
|    ├── __init.py__ 
|    └── README.md   
```

---
## ⚙️ Responsibilities
- **`features/`**  
 Implements domain-specific feature engineering:
  - Match statistics (games won/lost per set, tiebreak ratios, etc.)
  - Ranking-based metrics (Elo, Trueskill, Glicko, momentum, round/tournament adjustments)
  - Head-to-head derived features

- **`test/`**
 Contains **pytest** suites ensuring:
  - Data integrity checks  
  - Correctness of feature calculations  
  - Robustness against missing/invalid values 

- **`utils/`**
 Provides reusable tools such as:
  - Data cleaning pipelines  
  - Standardization/scaling utilities  
  - Helper functions for column pairing (p1 vs. p2)  

## 💻 Usage

### Run preprocessing

>**WORK IN PROGRESS....**