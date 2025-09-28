[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![GitHub license](https://img.shields.io/github/license/pretrehr/Sports-betting.svg)](https://github.com/pretrehr/Sports-betting/blob/master/LICENSE)
# Prediction Betting (ATP & WTA)

This project focuses on predicting betting outcomes for ATP and WTA tennis matches using historical match data and betting odds. It provides a comprehensive pipeline for data preparation, model development, and evaluation, leveraging modern tools and best practices for robust and maintainable code.

## ✨ Key Features  

### 📦 Dependency Management
- Managed with **[Poetry](https://python-poetry.org/)** → reproducible environments & easy dependency handling.  

---

### ✅ Testing & Quality Assurance
- **Security** → [`bandit`](https://bandit.readthedocs.io)  
- **Code Quality** → [`ruff`](https://docs.astral.sh/ruff/) (lint & format)  
- **Documentation Coverage** → [`interrogate`](https://interrogate.readthedocs.io) (NumPy-style docstrings)  
- **Type Safety** → [`mypy`](https://mypy-lang.org/)  
- **Unit Tests** → [`pytest`](https://docs.pytest.org)  
- **Documentation Build** → [`Sphinx`](https://www.sphinx-doc.org/)  

---

### 🔄 Continuous Integration
- Automated pipelines with **GitHub Actions** → runs tests, linters, and checks on every push or pull request.  

---

### 📝 Documentation
- Clear, concise guidelines for **setup, usage, and contributions**.  
- Full documentation generated with **Sphinx** (`docs/` folder). 
## 📂 Project Structure
```
├── data                # Data directory for input files 
│   ├── 01_raw/
│   ├── 02_processed/
│   └── 03_final/
├── docs/               # Documentation sources (Sphinx)
├── src 
│   ├── dataset/        # Data collection, cleaning, and feature engineering
│   ├── preprocessing/  # Data preprocessing and feature generation
│   ├── model/          # BaseModel and custom models
│   ├── metric/         # Metrics for evaluation 
│   └── utils/          # Helper functions
└── tests               # Unit tests for the project
```

---

## ⚙️ Data Structure

> * `data/01_raw/`  
  Unmodified raw data collected directly from external sources (web scraping, APIs, downloads, etc.). These files remain untouched to preserve traceability.
>
>  - `atptour/`    → ATP Tour player data (bio, stats)  
>  - `flashscore/` → Matches, odds, rankings  
>  - `wikipedia/`  → Tournament info  

> * `data/02_processed/`  
  Cleaned and pre-processed datasets derived from `01_raw/`.  

> * `data/03_final/`  
  Ready-to-use datasets for modeling and analysis.  
These files are optimized for training ML models and evaluation.

---

## 📦 Requirement
install all requirements
```bash
poetry install 
```

---

## ✅ Testing  
This project integrates robust tools to ensure **security, code quality, documentation coverage, and correctness**.  

- **Security** – [bandit](https://bandit.readthedocs.io): scan for vulnerabilities  
- **Quality** – [ruff](https://docs.astral.sh/ruff/) (lint & format), [interrogate](https://interrogate.readthedocs.io) (docstrings, NumPy style, 80% min)  
- **Unit Tests** – [pytest](https://docs.pytest.org): validate models, features, and evaluation logic  
- **Documentation** – [sphinx](https://www.sphinx-doc.org/): auto-generate browsable docs  

### Run locally (via Poetry)  
```bash
poetry run bandit -r ./prediction_tennis/ --exclude '*/test_*.py' -ll
poetry run ruff check ./prediction_tennis/
poetry run ruff format --check ./prediction_tennis/
poetry run interrogate ./prediction_tennis/
poetry run pytest --disable-warnings -v
poetry run sphinx-build -b html docs/ build/
```


## 🔄 Continuous Integration (GitHub Actions)
This project uses GitHub Actions to automatically run tests on each push or pull request.
The workflow configuration lives in: 
```bash
.github/workflows/tests.yml
```

---

## ⭐ License

This repository is licensed under the terms of the **MIT License**.

SPDX-License-Identifier: MIT

You are free to use, modify, and distribute this project under the terms of the MIT License. If you find this repository useful:
- ⭐ Consider giving it a star!
- 📝 Cite it in your projects or research.

