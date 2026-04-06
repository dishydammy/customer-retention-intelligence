import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
import joblib
import os
import logging
from utils import get_logger, load_csv

logger = get_logger(__name__, "churn_script.log")

DATA_DIR = 'data/'
MODEL_DIR = 'models/'

def define_churn_windows(df, churn_days=90):
    """Split the dataset into an 'Observation Window' (past behavior) and a 'Performance Window'"""
    df['invoicedate'] = pd.to_datetime(df['invoicedate'])
    max_date = df['invoicedate'].max()
    cutoff   = max_date - pd.Timedelta(days=churn_days)

    df_pre  = df[df['invoicedate'] < cutoff].copy()
    df_post = df[df['invoicedate'] >= cutoff].copy()

    logger.info(f"Churn windows defined with cutoff date: {cutoff}")
    logger.debug(f"Observation Window shape: {df_pre.shape}, Performance Window shape: {df_post.shape}")
    return df_pre, df_post, cutoff

def engineer_observation_features(df_pre, snapshot_date):
    """Calculate RFM metrics only using data from before the cutoff date."""
    rfm = df_pre.groupby('customerid').agg(
        recency   = ('invoicedate', lambda x: (snapshot_date - x.max()).days),
        frequency = ('invoiceno', 'nunique'),
        monetary  = ('totalprice', 'sum') # Make sure this matches your cleaned column name!
    ).reset_index()
    
    logger.info("Observation features (RFM) generated successfully.")
    logger.debug(f"Shape of RFM features: {rfm.shape}")
    return rfm

def engineer_target_labels(df_pre, df_post):
    """Define who churned (1) and who stayed (0) using vectorized logic."""
    pre_cutoff_ids = df_pre['customerid'].unique()
    post_cutoff_ids = df_post['customerid'].unique()

    churn_df = pd.DataFrame({'customerid': pre_cutoff_ids})
    
    churn_df['churned'] = np.where(churn_df['customerid'].isin(post_cutoff_ids), 0, 1)
    
    churn_rate = churn_df['churned'].mean() * 100
    logger.info(f"Target labels engineered. Overall churn rate: {churn_rate:.1f}%")
    return churn_df
    
def build_model_features(rfm_df, churn_df):
    """Merge features and labels, apply log transformations, and calculate binned scores."""
    model_df = rfm_df.merge(churn_df, on='customerid', how='inner')

    model_df['recency_log']   = np.log1p(model_df['recency'])
    model_df['frequency_log'] = np.log1p(model_df['frequency'])
    model_df['monetary_log']  = np.log1p(model_df['monetary'])

    model_df['r_score'] = pd.qcut(model_df['recency'], q=5, labels=[5,4,3,2,1])
    model_df['f_score'] = pd.qcut(model_df['frequency'].rank(method='first'), q=5, labels=[1,2,3,4,5])
    model_df['m_score'] = pd.qcut(model_df['monetary'].rank(method='first'), q=5, labels=[1,2,3,4,5])

    model_df['rfm_score'] = (model_df['r_score'].astype(int) + model_df['f_score'].astype(int) + model_df['m_score'].astype(int))

    features = [
        'recency_log', 'frequency_log', 'monetary_log', 
        'r_score', 'f_score', 'm_score', 'rfm_score'
    ]
    
    logger.info("Final model features built successfully.")
    logger.info(f"Features used for modeling: {features}")
    return model_df, features

def train_and_save_model(model_df, features, model_dir=MODEL_DIR):
    """Train the Random Forest classifier and save the artifact."""
    X = model_df[features].astype(float)
    y = model_df['churned']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    logger.info(f"Data split complete. Training size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")

    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)

    y_proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_proba)
    logger.info(f"Random Forest model trained. ROC-AUC Score: {auc:.4f}")

    model_path = os.path.join(MODEL_DIR, 'churn_model.pkl')
    joblib.dump(model, model_path)
    logger.info(f"Model saved successfully to {model_path}")

    return model, X

def apply_business_logic(model_df, trained_model, X):
    """Score the customer base and assign actionable marketing interventions."""
    model_df['churn_probability'] = trained_model.predict_proba(X)[:, 1]

    monetary_threshold = model_df['monetary'].median()
    churn_threshold    = 0.5

    def assign_intervention(row):
        high_churn = row['churn_probability'] >= churn_threshold
        high_value = row['monetary'] >= monetary_threshold

        if high_churn and high_value:
            return 'Save'
        elif high_churn and not high_value:
            return 'Lost Cause'
        elif not high_churn and high_value:
            return 'Protect'
        else:
            return 'Maintain'

    model_df['intervention'] = model_df.apply(assign_intervention, axis=1)
    
    logger.info("Business logic and interventions applied.")
    logger.info(f"Intervention counts:\n{model_df['intervention'].value_counts().to_string()}")
    
    return model_df

def run_churn_pipeline(input_filepath, output_filepath):
    """The main orchestrator for the Churn Prediction ML Pipeline."""
    logger.info("--- STARTING CHURN PREDICTION PIPELINE ---")
    logger.info(f"Loading data from: {input_filepath}")
    
    try:
        # 1. Load Data
        df = load_csv(input_filepath, logger)
        
        # 2. Split Windows (Note: unpacking all three variables now)
        df_pre, df_post, cutoff_date = define_churn_windows(df)
        
        # 3. Engineer Features and Targets
        rfm_df = engineer_observation_features(df_pre, cutoff_date)
        churn_df = engineer_target_labels(df_pre, df_post)
        
        # 4. Final Dataset Prep
        model_df, features = build_model_features(rfm_df, churn_df)
        
        # 5. Train & Export Model
        trained_model, X = train_and_save_model(model_df, features)
        
        # 6. Apply Business Logic
        final_scored_df = apply_business_logic(model_df, trained_model, X)
        
        # 7. Save Final Results
        final_scored_df.to_csv(output_filepath, index=False)
        logger.info(f"Successfully saved scored customer dataset to: {output_filepath}")
        logger.info("--- PIPELINE COMPLETED SUCCESSFULLY ---")
        
        return final_scored_df

    except Exception as e:
        logger.error(f"Pipeline failed due to an error: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    INPUT_FILE = DATA_DIR + 'processed/customer_clean.csv'
    OUTPUT_FILE = DATA_DIR + 'processed/customers_scored_churn.csv'
    
    run_churn_pipeline(INPUT_FILE, OUTPUT_FILE)