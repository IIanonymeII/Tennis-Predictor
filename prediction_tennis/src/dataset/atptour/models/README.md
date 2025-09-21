# Tennis-Predictor – ATP Tour Models

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


>- **`players.py`**  
Defines data structures for **players** (name, birthday, height, turn_pro, hand, etc.).  

Each file exposes one or more dataclasses with a `to_dict()` method for easy downstream use.

---


## 📂 Directory Structure

```shell
models/
├── __init__.py
├── README.md
└── players.py
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
    birthday    = "02/10/2025"        , 
    height      = 180  ,    
    ...
)

# Convert to dictionary for DataFrame usage
player_dict = player.to_dict()
print(player_dict)
```

### Example Output
```json
 {
    "id"      : "Idgytu",
    "name"    : "Novak Djokovic",
    "birthday": "02/10/2025",
    "height"  : 180,
    ...
}
```
---
## 💡 Notes
* All models follow a consistent interface (`dataclass` + `to_dict()`), ensuring compatibility across sources.

* Keep model definitions minimal and focused on data structure, leaving transformations to parsers or utilities.

* When extending models, maintain dictionary compatibility for smooth DataFrame integration.