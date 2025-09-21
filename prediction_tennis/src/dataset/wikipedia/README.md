# Tennis-Predictor – Wikipedia Dataset

This module is dedicated to **extracting and organizing raw tennis data from Wikipedia**.  
It provides a modular parsing pipeline to transform unstructured HTML/text into clean, structured objects (dataclasses) for downstream use in the **Tennis-Predictor** project.

---

## 📂 Folder Structure

```
wikipedia/
├── README.md          # This file, explaining the overall project
├── models/            # Data models (dataclasses)
│   ├── README.md 
│   └── tournaments.py
├── parsers/           # Parsers to extract information for each domain
│   ├── README.md      # Details on parsing logic for each data type
│   ├── season_links.py
│   └── season_tournament.py
├── utils/             # Shared utility functions   
│   └── ...
└── main.py            # main script
```
## ⚙️ Files Overview

>- **`models/`**  
  Defines dataclasses that represent structured entities such as:
>   - `Tournament`   
  These ensure type safety, readability, and easy downstream usage.

>- **`parsers/`**  
  Each parser targets a specific data domain (e.g., tournaments, matches, odds).  
  They fetch raw HTML/text, extract relevant fields, and convert them into dataclass instances.

>- **`utils/`**  

>- **`main.py`**  
  The orchestrator: combines models, parsers, and utilities to run a complete extraction.

