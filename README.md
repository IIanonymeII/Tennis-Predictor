[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

[![GitHub license](https://img.shields.io/github/license/pretrehr/Sports-betting.svg)](https://github.com/pretrehr/Sports-betting/blob/master/LICENSE)
# Prediction Betting (ATP & WTA)



### Overview
This project focuses on predicting betting outcomes for ATP and WTA tennis matches using historical match data and betting odds. It provides a comprehensive pipeline for data preparation, model development, and evaluation, leveraging modern tools and best practices for robust and maintainable code.

### Key Features  

- **Dependency Management**:  
  Uses **Poetry** to create reproducible environments and handle dependencies effortlessly.  

- **Testing**:  
  - **Static Type Checking**: Ensures type safety with `mypy`.  
  - **Unit Testing**: Validates functionality with `pytest`.  

- **Continuous Integration (CI)**:  
  Automates testing and validation using **GitHub Actions**, maintaining consistent code quality.  

- **Documentation**:  
  Provides clear and concise guidelines for setup, usage, and contribution. 

## requirement
install all requirements
```bash
poetry install 
```

---

### Project Structure
```
├── data        # Data directory for input files 
├── src 
│   ├── dataset # Data collection, cleaning, and feature engineering
│   ├── model   # BaseModel and custom models
│   └── metric  # Metrics for evaluation 
└── tests       # Unit tests for the project
```

## License

This repository is licensed under the terms of the **MIT License**.

SPDX-License-Identifier: MIT

You are free to use, modify, and distribute this project under the terms of the MIT License. If you find this repository useful:
- ⭐ Consider giving it a star!
- 📝 Cite it in your projects or research.

