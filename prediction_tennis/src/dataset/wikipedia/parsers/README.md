# Tennis-Predictor – Wkipedia Parsers

This directory contains the **parser modules** responsible for extracting, interpreting, and converting raw Flashscore data into structured data models.  

Each parser is implemented as a **state machine**: it sequentially reads raw segments, interprets them, and maps the information into the corresponding dataclasses defined in the [`models/`](../models) directory.


---

## ⚙️ Files Overview

>- **`season_links.py`**  
  Provides methods to fetch webpage content, extract season links, and create a mapping of years to their corresponding Wikipedia URLs.  
  **Key functionality:**
>   - Retrieve all ATP season pages for a given range of years.
>   - Validate and normalize URLs before parsing.

>- **`season_tournament.py`**  
  Parses Wikipedia ATP season pages to extract structured tournament information.  
  **Key functionality:**
>   - Interpret color-coded table rows to identify tournament types and results.
>   - Convert raw HTML tables into structured dataclasses for tournaments.  
  **Primary attributes:**
>       - `url` (str): URL of the Wikipedia ATP season page.  
>       - `year` (str): Year of the ATP season being parsed.

---

## 📂 Directory Structure

```shell
parsers/
├── __init__.py
├── README.md
├── season_links.py
└── season_tournament.py
```