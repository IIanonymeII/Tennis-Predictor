# Dataset Folder Structure Explanation

This project uses a structured approach to organize the dataset, separating raw and preprocessed data into distinct folders: `dataset/raw/` and `dataset/preprocessed/`. This README explains the rationale behind this choice and provides guidance on how to work with the data in each folder.


## raw Data
Contains the original data files exactly as received from the source. No modifications are made to these files so that you always have a pristine reference for reproducibility and auditing purposes.
- **Location:** `dataset/raw/`



## Preprocessed Data

Houses data that has undergone cleaning, transformation, and feature engineering. These steps prepare the data for direct use in analysis or modeling tasks, saving time on repetitive processing.

- **Location:** `dataset/preprocessed/`

##  Why This Structure?
The choice of using `dataset/raw/` and `dataset/preprocessed/` offers several benefits:

- **Clarity:** Separating raw and preprocessed data makes it clear which version of the data is being used at each stage of the project.

- **Reproducibility:** Keeping the raw data intact allows for easy re-running of preprocessing steps if needed.

- **Efficiency:** Preprocessed data can be directly loaded for analysis or modeling, avoiding redundant computations.

- **Organization:** Aligns with standard data science project structures, making the project easier to navigate for collaborators or future users.

This structure ensures that the dataset is managed in a way that is both intuitive and scalable, supporting the project's goals effectively.