# Tennis-Predictor – ATP Tour Processors
The **processors** module provides the high-level orchestration logic for handling player-related data.  
It connects the workflow between **fetching**, **processing**, and **saving** raw data into structured outputs.  

---

## ⚙️ Files Overview

>- **`player_data_fetcher.py`**  
  Handles fetching and initial processing of ATP player data:  
>   - Creates link names for **ATP Tour** and **Flashscore**  
>   - Generates player name variants for consistency across sources 

>- **`player_data_processor.py`**  
  Processes player data with a focus on fuzzy matching:  
>   - Processes a single player's record for **name resolution**  
>   - Updates player DataFrames with ATP URLs using **fuzzy matching techniques**  

>- **`player_data_saver.py`**  
  Ensures safe persistence of processed player data:  
>   - Saves comprehensive player data into **CSV files**  
>   - Performs **validation and logging** during the saving process 
## 📂 Directory Structure

```shell
processors/ 
├── README.md
├── player_data_fetcher.py 
├── player_data_processor.py   
└── player_data_saver.py
```