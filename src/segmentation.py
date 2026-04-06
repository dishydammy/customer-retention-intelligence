import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib
import os
import logging
from utils import get_logger, load_csv

logger = get_logger(__name__, "segmentation.log")

DATA_DIR = 'data/'
MODEL_DIR = 'models/'

def scale_rfm_features(rfm):
    """Scales the RFM features using StandardScaler."""
    scaler= StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm[['R_log', 'F_log', 'M_log']])
    scaler_path = os.path.join(MODEL_DIR, 'scaler.pkl')
    joblib.dump(scaler, scaler_path)
    logger.info(f"RFM features scaled and scaler saved to: {scaler_path}")
    return rfm_scaled

def train_kmeans_model(rfm_scaled, optimal_k=4):
    """Trains a Kmeans model on the scaled features."""
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    predictions = kmeans.fit_predict(rfm_scaled)
    model_path = os.path.join(MODEL_DIR, 'segmentation_model.pkl')
    joblib.dump(kmeans, model_path)
    logger.info(f"KMeans model trained with {optimal_k} clusters and saved to: {model_path}")
    return predictions

def assign_and_map_clusters(rfm, cluster_predictions):
    """Assigns cluster labels to the RFM dataframe and maps them to segments names"""
    rfm['Cluster'] = cluster_predictions
    segment_mapping = {1: "Champions", 0: "Loyal Base", 2: "Potential Loyals", 3: 'Lost/Inactive'}

    rfm['Cluster_Label'] = rfm['Cluster'].map(segment_mapping)
    logger.info("Cluster labels assigned and mapped to segment names.")
    logger.info(f"Cluster distribution:\n{rfm['Cluster_Label'].value_counts()}")
    return rfm

def run_segmentation_pipeline(input_filepath, output_filepath):
    """The main function for training the segmentation model"""
    try:
        rfm = load_csv(input_filepath, logger)
        rfm_scaled = scale_rfm_features(rfm)
        predictions = train_kmeans_model(rfm_scaled)
        rfm = assign_and_map_clusters(rfm, predictions)
        rfm.reset_index().to_csv(output_filepath, index=False)
        logger.info("Segmentation of customers complete")

    except Exception as e:
        logger.error(f"Segmentation pipeline failed due to an error: {e}", exc_info=True)
        raise e

if __name__ == "__main__":
    input_filepath = DATA_DIR + 'processed/rfm.csv'
    output_filepath = DATA_DIR + 'processed/rfm_segmented.csv'
    
    run_segmentation_pipeline(input_filepath, output_filepath)