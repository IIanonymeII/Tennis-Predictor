# Flashscore Parser

This project aims to extract and organize data from Flashscore (tournaments, matches, statistics, odds, etc.) using a modular architecture based on dataclasses.

## Structure du Projet

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

## Getting Started
To run the application, execute:
```bash
python main.py
```

## Modular Structure
* `models/` : Contains all dataclasses modeling the extracted data (tournaments, matches, statistics, odds, etc.).

* `parsers/` : Includes modules responsible for parsing specific data types. Each parser extracts data from the source and converts it into the defined models.

* `utils/`  : Houses shared utility functions used across the project.

* `main.py` : he entry point that orchestrates data extraction and overall processing.