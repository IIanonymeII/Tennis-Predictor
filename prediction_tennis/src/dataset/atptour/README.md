# Tennis-Predictor – ATP tour Dataset

This module is dedicated to **extracting and organizing raw tennis data from ATP Tour**.  
It provides a modular parsing pipeline to transform unstructured HTML/text into clean, structured objects (dataclasses) for downstream use in the **Tennis-Predictor** project.

## 📂 Folder Structure

```
atptour/
├── README.md          # This file, explaining the overall project
├── models/            # Data models (dataclasses)
│   ├── README.md      # Explanation of data models and their structure
│   └── players.py
├── parsers/           # Parsers to extract information for each domain
│   ├── README.md      # Details on parsing logic for each data type
│   ├── data_fetcher.py
│   └── data_parser.py
├── utils/             # Shared utility functions
│   ├── README.md      # Description of available utilities
│   ├── config.py  
│   ├── flashscore_utils.py    
│   └── player_utils.py
├── processors/ 
│   ├── README.md
│   ├── player_data_fetcher.py 
│   ├── player_data_processor.py   
│   └── player_data_saver.py
└── main.py            # main script
```

## ⚙️ Files Overview

>- **`models/`**  
  Defines dataclasses that represent structured entities such as:
>   - `Player`, etc.  
  These ensure type safety, readability, and easy downstream usage.

>- **`parsers/`**  
  Each parser targets a specific data domain (e.g., tournaments, matches, odds).  
  They fetch raw HTML/text, extract relevant fields, and convert them into dataclass instances.

>- **`utils/`**  
 Shared helper functions to support parsing and modeling

>- **`processors/`**  
  High-level orchestration layer that ties together **fetching, processing, and saving** of player data

>- **`main.py`**  
  The orchestrator: combines models, parsers, and utilities to run a complete extraction.
---

## 💻 Usage
Run the main parsing pipeline:

```bash
python main.py
```