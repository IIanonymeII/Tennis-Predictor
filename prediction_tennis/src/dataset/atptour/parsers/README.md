# Tennis-Predictor – ATP Tour Parsers

This directory contains the **parser modules** responsible for extracting, interpreting, and converting raw Flashscore data into structured data models.  

Each parser is implemented as a **state machine**: it sequentially reads raw segments, interprets them, and maps the information into the corresponding dataclasses defined in the [`models/`](../models) directory.


---

## ⚙️ Files Overview

>- **`data_fetcher.py`**  
    Handles HTTP requests to fetch raw HTML or API responses from atp tour.
>   - Sending requests to relevant endpoints
>   - Handling response validation and error logging
>   - Returning raw content for parsing

>- **`data_parser.py`** 
 Processes the raw data fetched and converts it into structured formats.
 Uses models from `models/players.py`.

---

## 📂 Directory Structure

```shell
parsers/
├── __init__.py
├── README.md
├── data_fetcher.py
└── data_parser.py
```
