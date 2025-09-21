# Tennis-Predictor – Wikipedia Models

This directory defines the **data models** used to represent and manage information parsed from Wikipedia.  
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
  Defines data structures for **tournament-level metadata** (name, location, year, money, etc.).

Each file exposes one or more dataclasses with a `to_dict()` method for easy downstream use.

---

## 📂 Directory Structure

```shell
models/
├── __init__.py
├── README.md
└── tournaments.py
```
---