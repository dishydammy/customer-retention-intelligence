import numpy as np
import pandas as pd
import logging
from utils import get_logger, load_csv

logger = get_logger(__name__, "rfm_analysis.log")

DATA_DIR = 'data/'

def calculate_rfm_metrics(df):
    """Calculate RFM metrics for each customer."""
    df['invoicedate'] = pd.to_datetime(df['invoicedate'])
    snapshot_date = df['invoicedate'].max() + pd.Timedelta(days=1)
    rfm = df.groupby('customerid').agg({'invoicedate': lambda x: (snapshot_date - x.max()).days,
    'invoiceno': 'nunique',
    'totalprice': 'sum'}).reset_index()
    rfm.rename(columns={
    'invoicedate': 'Recency',
    'invoiceno': 'Frequency',
    'totalprice': 'Monetary'}, inplace=True)
    logger.info(f"Snapshot date for recency calculation: {snapshot_date}")
    logger.debug(f"RFM Dataframe shape: {rfm.shape}")
    logger.info("RFM metrics calculated for each customer.")
    return rfm

def apply_log_transformations(rfm):
    """Apply log transformations to RFM metrics to reduce skewness."""
    rfm['R_log'] = np.log1p(rfm['Recency'])
    rfm['F_log'] = np.log1p(rfm['Frequency'])
    rfm['M_log'] = np.log1p(rfm['Monetary'])
    logger.info("Log transformations applied to RFM metrics.")
    return rfm

def calculate_rfm_scores(rfm):
    """Calculate RFM scores for each customer."""
    rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=[5, 4, 3, 2, 1])
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5])
    rfm['M_Score'] = pd.qcut(rfm['Monetary'], q=5, labels=[1, 2, 3, 4, 5])
    rfm['RFM_Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    rfm['RFM_Score'] = rfm['R_Score'].astype(int) + rfm['F_Score'].astype(int) + rfm['M_Score'].astype(int)
    logger.info("RFM scores and segments calculated for each customer.")
    return rfm

def segment_customers(rfm):
    conditions = [
    (rfm['R_Score'] == 5) & (rfm['F_Score'] == 5),        # Champions
    (rfm['R_Score'] <= 2) & (rfm['F_Score'] >= 3),        # At Risk (Must go before Loyal!)
    (rfm['F_Score'] >= 4),                                # Loyal Customers
    (rfm['R_Score'] == 1) & (rfm['F_Score'] == 1),        # Lost
    (rfm['R_Score'] >= 4) & (rfm['F_Score'] <= 2),        # Potential Loyalists
    (rfm['R_Score'] == 3) & (rfm['F_Score'] == 3)         # Needs Attention
]
    choices = [
    'Champions',
    'At Risk',
    'Loyal Customers',
    'Lost',
    'Potential Loyalists',
    'Needs Attention'
]
    rfm['Customer_Segment'] = np.select(conditions, choices, default='Others')
    logger.info("Customers segmented based on RFM scores.")
    return rfm

def run_rfm_pipeline(input_filepath, output_filepath):
    """The main function to run the RFM analysis pipeline."""
    try:
        df = load_csv(input_filepath, logger)
        rfm = calculate_rfm_metrics(df)
        rfm = apply_log_transformations(rfm)
        rfm = calculate_rfm_scores(rfm)
        rfm = segment_customers(rfm)
        rfm.to_csv(output_filepath, index=False)
        logger.info(f"RFM analysis pipeline completed. Output saved to: {output_filepath}")
        logger.info(f"Final RFM Dataframe shape: {rfm.shape}")

    except Exception as e:
        logger.error(f"RFM Pipeline failed due to an error: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    input_filepath = DATA_DIR + 'processed/customer_clean.csv'
    output_filepath = DATA_DIR + 'processed/rfm.csv'
    
    run_rfm_pipeline(input_filepath, output_filepath)
    