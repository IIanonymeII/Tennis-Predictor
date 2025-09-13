
# Tennis-Predictor – Flashscore Models

This directory defines the **data models** used to represent and manage information parsed from Flashscore.  
All models are implemented with Python’s [`dataclasses`](https://docs.python.org/3/library/dataclasses.html), ensuring a clean, lightweight, and extensible way to structure parsed tennis data.

---

## ⚡ Why Dataclasses ?
- **Readable & Structured** → Provide an object-oriented representation of entities (e.g., tournaments, matches, players, odds).  

- **Dictionary-Like** → Can be easily converted into dictionaries via `to_dict()` methods, making them convenient for processing and storage.  

- **Seamless Integration** → Conversion to dictionaries allows smooth loading into **Pandas DataFrames** for analysis and machine learning pipelines.  

- **Extensible** → New fields or models can be added with minimal boilerplate.

---

## ⚙️ Files Overview

>- **`tournaments.py`**  
  Defines data structures for **tournament-level metadata** (name, location, year, surface, etc.).

>- **`matchs.py`**  
  Defines data structures for **matches** within tournaments (round, players, scorelines, results).  

>- **`players.py`**  
  Defines data structures for **players** (name, nationality, ranking, age, etc.).  

>- **`odds.py`**  
  Defines data structures for **betting odds** (bookmaker, pre-match odds, implied probabilities).  

Each file exposes one or more dataclasses with a `to_dict()` method for easy downstream use.

---

## 📂 Directory Structure

```shell
models/
├── __init__.py
├── README.md
├── tournaments.py
├── matchs.py
├── players.py
└── odds.py
```
---
## 💻 Usage Example
### Creating a Player Model

```python 
from dataset.flashscore.models.players import Player

# Create an instance
player = Player(
    id          = "Idgytu"        ,
    name        = "Novak Djokovic",
    nationality = "Serbia"        , 
    link        ="http://url..."  ,    
)

# Convert to dictionary for DataFrame usage
player_dict = player.to_dict()
print(player_dict)
```

### Example Output
```json
 {
    "name": "Novak Djokovic",
    "nationality": "Serbia",
    "ranking": 1,
    "age": 36
}
```
---

## 💡 Notes
* All models follow a consistent interface (`dataclass` + `to_dict()`), ensuring compatibility across sources.

* Keep model definitions minimal and focused on data structure, leaving transformations to parsers or utilities.

* When extending models, maintain dictionary compatibility for smooth DataFrame integration.