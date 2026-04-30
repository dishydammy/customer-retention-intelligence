import pandas as pd
import os
import logging

def get_logger(module_name, log_file="pipeline.log"):
    """
    Creates and returns a centralized logger. 
    By passing __name__ as the module_name, the logs will show exactly which script is running.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file), 
            logging.StreamHandler()                  
        ]
    )
    return logging.getLogger(module_name)

def load_csv(filepath, logger):
    """Safely loads a CSV and logs the shape."""
    if not os.path.exists(filepath):
        logger.error(f"CRITICAL ERROR: File not found at {filepath}")
        raise FileNotFoundError(f"Cannot locate {filepath}")
    
    df = pd.read_csv(filepath)
    logger.info(f"Loaded data from {filepath}. Shape: {df.shape}")
    return df


def assign_intervention(churn_probability, monetary, churn_threshold=0.5, monetary_threshold=300):
    """Maps churn risk and customer value into a retention action segment."""
    high_churn = churn_probability >= churn_threshold
    high_value = monetary >= monetary_threshold

    if high_churn and high_value:
        return "Save"
    if high_churn and not high_value:
        return "Lost Cause"
    if not high_churn and high_value:
        return "Protect"
    return "Maintain"
