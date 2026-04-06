import pandas as pd
import datetime as dt
import logging
from utils import get_logger, load_csv

logger = get_logger(__name__, "preprocessing.log")

DATA_DIR = 'data/'

def remove_duplicates(df):
    """Remove duplicate rows from the dataframe."""""
    subset_cols = ['invoiceno', 'stockcode', 'quantity', 'customerid']
    duplicate = df.duplicated(subset=subset_cols).sum()
    df.drop_duplicates(subset=subset_cols, inplace=True)
    logger.info("Duplicate rows removed.")
    logger.debug(f"Shape of Dataframe after removing duplicates: {df.shape}")
    logger.info(f"Total duplicate rows removed: {duplicate:,}")
    return df

def handle_missing_customers(df):
    """Remove rows with missing customer IDs."""
    missing_customers = df['customerid'].isnull().sum()
    df.dropna(subset=['customerid'], inplace=True)
    logger.info("Rows with missing customer IDs removed.")
    logger.debug(f"Shape of Dataframe after handling missing customer IDs: {df.shape}")
    logger.info(f"Total rows with missing customer IDs: {missing_customers:,}")
    return df

def remove_cancelled_orders(df):
    """Remove rows with canceled orders (invoices starting with 'C')"""
    cancelled_orders = df['invoiceno'].str.startswith('C', na=False).sum()
    df = df[df['invoiceno'].astype(str).str.startswith('C', na=False) == False]
    logger.info('Cancelled orders removed.')
    logger.info(f"Total cancelled orders removed: {cancelled_orders:,}")
    logger.debug(f"Shape of Dataframe after removing cancelled orders: {df.shape}")
    return df

def remove_anomalies(df):
    """Remove rows with negative or zero quantity or/and unit price"""
    df_clean = df[(df['quantity']>0) & (df['unitprice']>0)]
    rows_removed = len(df) - len(df_clean)
    logger.info(f"Total anomalous rows removed: {rows_removed:,}")
    logger.debug(f"New shape of Dataframe after anomalies removed: {df_clean.shape}")
    logger.info("Anomalies removed")
    return df_clean

def standardize_text_columns(df):
    """Clean up string columns for grouping"""
    df['description'] = df['description'].astype(str).str.upper().str.strip()
    df['stockcode'] = df['stockcode'].astype(str).str.upper().str.strip()
    logger.info("Text columns standardized.")
    return df

def remove_administrative_codes(df):
    """Remove administrative columns from stockcode columns"""
    admin_codes = ['AMAZONFEE', 'B', 'POST', 'DOT', 'M', 'BANK CHARGES', 'CRUK', 'PADS']
    admin_rows = df['stockcode'].isin(admin_codes).sum()
    df_clean = df[df['stockcode'].isin(admin_codes)==False]
    logger.info('Rows with administrative codes removed')
    logger.info(f"Total rows removed: {admin_rows:,}")
    logger.debug(f"Shape of Dataframe after removing administrative codes: {df_clean.shape}")
    return df_clean

def engineer_transaction_features(df):
    """New features for transaction and date created"""
    df['totalprice'] = df['quantity'] * df['unitprice']
    df['invoicedate'] = pd.to_datetime(df['invoicedate'])
    df['year_month'] = df['invoicedate'].dt.to_period('M')
    df['day_of_week'] = df['invoicedate'].dt.day_name()
    df['hour'] = df['invoicedate'].dt.hour
    logger.info("New features engineered: totalprice, year_month, day_of_week, hour and invoicedate.")
    return df

def filter_by_country(df, target_country='United Kingdom'):
    """Filter dataset for rows that only include the United Kingdom"""
    df_filtered = df[df['country'] == target_country]
    logger.info(f"Dataset filtered for country: {target_country}")
    logger.debug(f"Shape of Dataframe after filtering by country: {df_filtered.shape}")
    return df_filtered

def preprocess_pipeline(input_filepath, output_filepath):
    """The main function to run the data prreprocessng piepeline"""
    logger.info("Starting data preprocessing pipeline.")
    logger.info(f"Loading data from file: {input_filepath}")
    try:
        df = load_csv(input_filepath, logger)
        df.columns = df.columns.str.lower()
        logger.info("Dataframe columns converted to lowercase.")

        # 2. Cleaning & Filtering
        df = remove_duplicates(df)
        df = handle_missing_customers(df)
        df = remove_cancelled_orders(df)
        df = remove_anomalies(df)
        
        # 3. Product Catalog Processing
        df = standardize_text_columns(df)
        df = remove_administrative_codes(df)
        
        # 4. Feature Engineering & Market Segmentation
        df = engineer_transaction_features(df)
        df = filter_by_country(df, target_country='United Kingdom')
        
        # 5. Save and Finish
        logger.info(f"Pipeline complete. Final dataset shape: {df.shape}")
        df.to_csv(output_filepath, index=False)
        logger.info(f"Successfully saved clean dataset to: {output_filepath}")
        logger.info("--- PIPELINE COMPLETED SUCCESSFULLY ---")
        
        return df

    except Exception as e:
        logger.error(f"Pipeline failed due to an error: {e}", exc_info=True)
        raise e
    
if __name__ == "__main__":
    input_filepath = DATA_DIR + 'raw/OnlineRetail.csv'
    output_filepath = DATA_DIR + 'processed/customer_clean.csv'

    clean_df = preprocess_pipeline(input_filepath, output_filepath)

    

