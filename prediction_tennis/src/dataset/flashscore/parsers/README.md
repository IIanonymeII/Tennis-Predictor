# Parsers

This directory contains modules responsible for parsing Flashscore data.

## Files

Each parser module is designed as a state machine that reads data segments, interprets them, and converts them into the corresponding data model.

- **tournaments_parser.py**
Parses information related to tournaments. Utilizes data models defined in `models/tournaments.py`.

- **odds_parser.py**  
  Parses betting odds. Utilizes dataclasses defined in `models/odds.py`.