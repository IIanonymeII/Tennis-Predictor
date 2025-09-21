# Tennis-Predictor – Flashscore Utils

This folder contains **utility functions** that are shared across multiple modules of the Tennis-Predictor project.  

These utilities are designed to **reduce code duplication**, simplify common tasks, and improve overall project maintainability.

---

## ⚙️ Files Overview

>- **`text_extraction.py`**  
  Provides functions to **extract specific patterns from text**, such as:  
>   - Odds  
>   - Years  
>   - Player names or other sequences 

>- **`flashscore_client.py`**  
  Handles **communication with Flashscore**, facilitating:  
>   - HTTP requests  
>   - Data retrieval  
>   - Preliminary data formatting before parsing  

---

## 📂 Directory Structure

```shell
utils/
├── __init__.py
├── README.md
├── text_extraction.py
└── flashscore_client.py
```