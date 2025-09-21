
# Tennis-Predictor – Flashscore Parsers

This directory contains the **parser modules** responsible for extracting, interpreting, and converting raw Flashscore data into structured data models.  

Each parser is implemented as a **state machine**: it sequentially reads raw segments, interprets them, and maps the information into the corresponding dataclasses defined in the [`models/`](../models) directory.

---

## ⚙️ Files Overview

>- **`tournaments_parser.py`**  
  Parses general tournament-level information.  
  Uses models from `models/tournaments.py`.

>- **`tournament_dates_parser.py`**  
  Retrieves and parses archived data related to a **single tournament**, organized by date.  
  Uses models from `models/tournaments.py`.

>- **`matchs_in_tournament_parser.py`**  
  Extracts match-level data within tournaments.  
  Uses dataclasses from `models/matchs.py` and `models/players.py`.

>- **`match_status_parser.py`**  
  Determines and categorizes match status (e.g., *Finished*, *Retired*, *Walkover*).  
  Uses relevant status-related models.

>- **`match_score_parser.py`**  
>  Scrapes and structures **score-related details**, including:  
>   - Set-by-set results  
>   - Tiebreaks  
>   - Match duration  
>   - Additional statistics  

>- **`parser_match_stat.py`**  
>  Parses **in-match statistics**, such as:  
>   - Points won on serve  
>   - Service games won  
>   - Set-by-set performance metrics 
>   - etc.

>- **`odds_parser.py`**  
  Extracts betting odds and probability information.  
  Uses dataclasses from `models/odds.py`.

---

## 📂 Directory Structure

```shell
parsers/
├── __init__.py
├── README.md
├── tournaments_parser.py
├── tournament_dates_parser.py
├── matchs_in_tournament_parser.py
├── match_status_parser.py
├── match_score_parser.py
├── parser_match_stat.py
└── odds_parser.py
```
