# PREPROCESSED


The `preprocessed/` folder contains modular scripts for preparing data before analysis or model training. The pipeline is structured into three key stages: **Cleaning**, **Feature Engineering**, and **Transformations**. Each stage has its own directory and README for documentation.


## Folder Structure


```shell
flashscore/preprocessed/
├── README.md 
├── cleaning/ # Handles data cleaning tasks 
│ ├── README.md  
│ └── ... 
├── feature/ # Scripts for adding new features 
│ ├── README.md
│ └── ... 
├── transformations/ # Data transformations for model readiness 
│ ├── README.md 
│ └── ... 
└── main.py # Main script
```

## Getting Started
To run the application, execute:
```bash
python main.py
```

## Modular Structure

1. **Cleaning (`cleaning/`)**  
   - Handles missing values, duplicates, and inconsistent data.  
   - Standardizes raw data formats.  

2. **Feature Engineering (`feature/`)**  
   - Adds computed columns such as ELO rankings, statistics, and domain-specific metrics.  

3. **Transformations (`transformations/`)**  
   - Applies scaling, normalization, and encoding to prepare data for machine learning models.  

4. **Execution (`main.py`)**  
   - Runs all preprocessing steps in sequence, loading data from `dataset/raw/` and saving outputs to `dataset/preprocessed/`.
