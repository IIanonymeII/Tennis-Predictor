# Tennis-Predictor – Utils

This folder contains **utility functions** that are shared across multiple modules of the Tennis-Predictor project.  

These utilities are designed to **reduce code duplication**, simplify common tasks, and improve overall project maintainability.

---

## ⚙️ Files Overview

>- **`log_setup.py`**  
  Implements a **rotating logging system** to efficiently manage log storage:  
>   - Creates log files  
>   - Rotates and removes old logs automatically  
>   - Ensures long-running processes do not consume excessive disk space

>- **`file_utils.py`**  
  Provides **file and DataFrame utility functions** to simplify common I/O tasks:  
>   - `ensure_output_directory_exists` → Safely creates output directories if missing  
>   - `save_dataframe_to_csv` → Saves DataFrames to CSV with error handling  
>   - `get_file_size_mb` → Retrieves file size in megabytes  
>   - `log_dataframe_information` → Logs DataFrame shape and memory usage  

---

## 📂 Directory Structure

```shell
utils/
├── __init__.py
├── README.md
├── file_utils.py
└── log_setup.py
```