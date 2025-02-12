# Models

This directory contains data models used for structuring and managing data parsed from Flashscore, utilizing Python's `dataclasses`.

## Why Dataclasses?
- **Similar to Dictionaries**: Dataclasses are similar to dictionaries, making them highly useful for subsequent data processing steps.
- **DataFrame Compatibility**: The data stored in dataclasses can be easily converted to dictionaries, facilitating seamless integration with Pandas DataFrames for further analysis.

## Files
All models use classes to store data and include a `to_dict()` function to convert the data into dictionary format.
- **tournaments.py**  
    Defines the data structures for tournaments.

- **odds.py**  
    Defines the data structures for betting odds.

## Structure

```shell
utils/
├── __init__.py
├── REAMDE.md
├── tournaments.py
└── odds.py
```