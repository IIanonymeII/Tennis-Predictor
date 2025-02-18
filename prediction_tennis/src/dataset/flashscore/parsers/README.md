# Parsers

This directory contains modules responsible for parsing Flashscore data.

## Files

Each parser module is designed as a state machine that reads data segments, interprets them, and converts them into the corresponding data model.

- **tournaments_parser.py**
Parses information related to tournaments. Utilizes data models defined in `models/tournaments.py`.

- **tournament_dates_parser.py**
Parses information related to a single tournament and retrieves all relevant archives (organized by date) associated with that tournament. Utilizes data models defined in `models/tournaments.py`.

- **matchs_in_tournament_parser.py**  
  Parses match data within tournaments. Utilizes dataclasses defined in `models/matchs.py` and `models/players.py` to manage match and player information.

- **match_status_parser.py**
  Checks the status of a match, such as "Retired," "Finished," "Walkover," etc. Utilizes relevant data models to classify and interpret match statuses.

- **match_score_parser.py**
  Scrapes the match score to retrieve set results for each player, tiebreak details, match duration, and other related statistics.

- **odds_parser.py**  
  Parses betting odds. Utilizes dataclasses defined in `models/odds.py`.


## Structure

```shell
parsers/
├── __init__.py
├── REAMDE.md
├── tournaments_parser.py
├── tournament_dates_parser.py
├── matchs_in_tournament_parser.py
├── match_status_parser.py
├── match_score_parser.py
└── odds_parser.py
```