# Tennis-Predictor – Flashscore Parser

This module is dedicated to **extracting and organizing raw tennis data from Flashscore**.  
It provides a modular parsing pipeline to transform unstructured HTML/text into clean, structured objects (dataclasses) for downstream use in the **Tennis-Predictor** project.

---

## 📂 Folder Structure

```
flashscore/
├── README.md          # This file, explaining the overall project
├── models/            # Data models (dataclasses)
│   ├── README.md      # Explanation of data models and their structure
│   ├── tournaments.py
│   ├── matches.py
│   ├── ...
│   └── odds.py
├── parsers/           # Parsers to extract information for each domain
│   ├── README.md      # Details on parsing logic for each data type
│   ├── tournaments_parser.py
│   ├── tournament_dates_parser.py
│   ├── ...
│   └── odds_parser.py
├── utils/             # Shared utility functions
│   ├── README.md      # Description of available utilities
│   ├── flashscore_client.py      
│   └── text_extraction.py
└── main.py            # main script
```
## ⚙️ Files Overview

>- **`models/`**  
  Defines dataclasses that represent structured entities such as:
>   - `Tournament`, `Match`, `Odds`, `Statistics`, etc.  
  These ensure type safety, readability, and easy downstream usage.

>- **`parsers/`**  
  Each parser targets a specific data domain (e.g., tournaments, matches, odds).  
  They fetch raw HTML/text, extract relevant fields, and convert them into dataclass instances.

>- **`utils/`**  
  Shared functions to:
>   - Fetch pages from Flashscore (`flashscore_client.py`)  
>   - Extract patterns with regex and text utilities (`text_extraction.py`)

>- **`main.py`**  
  The orchestrator: combines models, parsers, and utilities to run a complete extraction.

## 💻 Usage
Run the main parsing pipeline:

```bash
python main.py
```

Example: parsing tournaments with the dedicated parser:
```python
from parsers.tournaments_parser import parse_tournaments
from utils.flashscore_client import fetch_page

html = fetch_page("https://www.flashscore.com/tennis/")
tournaments = parse_tournaments(html)

for t in tournaments:
    print(t.name, t.location, t.start_date)
```