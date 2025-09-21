# Tennis-Predictor – Dataset

This module provides the tools to parse, model, and standardize raw tennis data from multiple sources into structured datasets ready for analysis and machine learning prediction. It ensures that heterogeneous data (ATP Tour, Flashscore, Wikipedia) can be transformed into a consistent format suitable for downstream pipelines.

---
## 📂 Structure
```dataset/
│── Readme.md        # You are here
│── atptour/         # ATP Tour-specific parsing and models
│   ├── models/      # Dataclasses for tournaments, matches, players...
│   ├── parser/      # Extract tournament, match, player info from raw data
│   ├── test/        # Unit tests (pytest)
│   ├── utils/       # Helper functions for parsing & formatting
│   ├── main.py      # Entry point for running parsers
│   └── README.md    # Module-specific documentation
│
│── flashscore/      # Flashscore odds & match data parsing
│── wikipedia/       # Wikipedia player & historical data parsing
```

---
## ⚙️ Responsibilities
- **`models/`**  
  Defines dataclasses for tennis entities (`Tournament`, `Match`, `Player`).  
  Provides conversion methods (e.g., dict or JSON) for further processing.

- **`parser/`**  
  Implements parsing logic per source.  
  - Extracts tournament info, player metadata (e.g., age, nationality), and match results.  
  - Handles raw file reading, requests, and transformations.  

- **`utils/`**  
  Reusable helpers for data normalization, date handling, and formatting.

- **`test/`**  
  Unit tests written with **pytest** to ensure correctness and reproducibility of parsing and modeling.

- **`main.py`**  
  Script to orchestrate the parsing workflow for ATP Tour data.

---

## 💻 Usage

### Run ATP Tour Parser
From the repository root:
```bash
python dataset.atptour.main.py
```