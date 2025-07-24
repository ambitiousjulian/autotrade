import os
import pickle
import logging
import numpy as np
import pandas as pd
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class MLFilter:
    """XGBoost-based edge detection filter"""
    
    def __init__(self):
        self.model_path = os.getenv("MODEL_PATH", "./core/models/model.pkl")
        self.min_edge_probability = float(os.getenv("MIN_EDGE_PROBABILITY", "0.55"))
        self.model = None
        self.features = ["iv_rank", "vix", "spy_rsi", "put_call_ratio", "day_of_week"]
        
        self._load_model()
        
    def _load_model(self):
        """Load pre-trained XGBoost model"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                logger.info(f"ML model loaded from {self.model_path}")
            else:
                logger.warning("No trained model found, using mock predictions")
                self.model = None
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            
    def is_edge_today(self, market_data: Dict) -> bool:
        """Determine if there's a trading edge today"""
        try:
            if self.model is None:
                # Mock prediction when no model available
                return self._mock_prediction(market_data)
                
            # Prepare features
            features_df = self._prepare_features(market_data)
            
            # Get prediction probability
            prob = self.model.predict_proba(features_df)[0][1]
            
            has_edge = prob >= self.min_edge_probability
            logger.info(f"ML Filter: Edge probability = {prob:.3f}, Has edge = {has_edge}")
            
            return has_edge
            
        except Exception as e:
            logger.error(f"ML filter error: {e}")
            return True  # Default to allowing trades on error
            
    def _prepare_features(self, market_data: Dict) -> pd.DataFrame:
        """Convert market data to model features"""
        feature_values = []
        
        for feature in self.features:
            if feature == "day_of_week":
                value = datetime.now().weekday()
            else:
                value = market_data.get(feature, 0)
            feature_values.append(value)
            
        return pd.DataFrame([feature_values], columns=self.features)
        
    def _mock_prediction(self, market_data: Dict) -> bool:
        """Mock edge detection based on simple rules"""
        iv_rank = market_data.get("iv_rank", 50)
        vix = market_data.get("vix", 20)
        
        # Simple rules for demo
        if vix > 30:  # High volatility
            return False
        elif iv_rank > 70:  # High IV rank
            return True
        elif iv_rank < 30:  # Low IV rank
            return False
        else:
            # Random edge for demo
            return np.random.random() > 0.4
            
    def train_model(self, historical_data: pd.DataFrame):
        """Train XGBoost model on historical data (offline process)"""
        # This would be run separately to train the model
        # Not implemented in detail for this skeleton
        pass