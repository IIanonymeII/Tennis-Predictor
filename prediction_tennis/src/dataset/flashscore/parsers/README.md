# Parsers

This directory contains modules responsible for parsing Flashscore data.

## Files

- **odds_parser.py**  
  Parses betting odds. Utilizes dataclasses defined in `models/odds.py`.

Each parser module is designed as a state machine that reads data segments, interprets them, and converts them into the corresponding data model.