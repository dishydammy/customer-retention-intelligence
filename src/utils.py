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