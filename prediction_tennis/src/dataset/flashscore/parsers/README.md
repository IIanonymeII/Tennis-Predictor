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
└── odds_parser.py
```