# Utils

This folder contains utility functions that are shared across different modules of the project.

## Files

These utilities help reduce code duplication and improve overall project maintainability. 
 
- **text_extraction.py**  
  Extracts patterns from text, such as odds, years or specific sequences.

- **flashscore_client.py**
  Handles communication with Flashscore, facilitating data retrieval and processing.

- **log_setup.py**
  Implements a rotated logging system to manage storage efficiently. This module creates log files and automatically removes old log files to prevent excessive storage use.

## Structure

```shell
utils/
├── __init__.py
├── REAMDE.md
├── text_extraction.py
├── flashscore_client.py
└── log_setup.py
```
