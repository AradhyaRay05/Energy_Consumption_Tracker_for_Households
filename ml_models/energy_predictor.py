"""
Energy Consumption Prediction Model
Uses machine learning to predict future energy consumption
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class EnergyPredictor:
    """Energy consumption prediction model"""
    
    def __init__(self, model_path='models'):
        """
        Initialize the predictor
        
        Args:
            model_path: Directory to save/load models
        """
        self.model_path = model_path
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.is_trained = False
        
        # Create model directory if it doesn't exist
        os.makedirs(model_path, exist_ok=True)
    
    def create_features(self, df):
        """
        Create features from raw energy data
        
        Args:
            df: DataFrame with columns: timestamp, appliance_name, power_usage_kwh, cost
        
        Returns:
            DataFrame with engineered features
        """
        df = df.copy()
        
        # Convert timestamp to datetime if not already
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['day_of_month'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        df['is_peak_hour'] = ((df['hour'] >= 17) & (df['hour'] <= 21)).astype(int)
        
        # Encode appliance names
        if 'appliance_name' in df.columns:
            if 'appliance_name' not in self.label_encoders:
                self.label_encoders['appliance_name'] = LabelEncoder()
                df['appliance_encoded'] = self.label_encoders['appliance_name'].fit_transform(df['appliance_name'])
            else:
                # Handle unseen appliances
                known_appliances = self.label_encoders['appliance_name'].classes_
                df['appliance_encoded'] = df['appliance_name'].apply(
                    lambda x: self.label_encoders['appliance_name'].transform([x])[0] 
                    if x in known_appliances else -1
                )
        
        return df
    
    def aggregate_daily(self, df):
        """
        Aggregate data to daily consumption
        
        Args:
            df: DataFrame with energy records
        
        Returns:
            DataFrame aggregated by date
        """
        df = df.copy()
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        
        # Aggregate by date
        daily_df = df.groupby('date').agg({
            'power_usage_kwh': 'sum',
            'cost': 'sum',
            'appliance_name': 'count'  # Number of appliance uses per day
        }).reset_index()
        
        daily_df.columns = ['date', 'total_kwh', 'total_cost', 'num_uses']
        
        # Convert date back to datetime
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        
        # Add temporal features
        daily_df['day_of_week'] = daily_df['date'].dt.dayofweek
        daily_df['day_of_month'] = daily_df['date'].dt.day
        daily_df['month'] = daily_df['date'].dt.month
        daily_df['is_weekend'] = (daily_df['day_of_week'] >= 5).astype(int)
        
        # Add lag features (previous days' consumption)
        daily_df['prev_day_kwh'] = daily_df['total_kwh'].shift(1)
        daily_df['prev_week_kwh'] = daily_df['total_kwh'].shift(7)
        daily_df['avg_last_7days'] = daily_df['total_kwh'].rolling(window=7, min_periods=1).mean()
        daily_df['avg_last_30days'] = daily_df['total_kwh'].rolling(window=30, min_periods=1).mean()
        
        # Fill NaN values
        daily_df = daily_df.fillna(method='bfill').fillna(0)
        
        return daily_df
    
    def train(self, df, target_col='total_kwh', test_size=0.2):
        """
        Train the prediction model
        
        Args:
            df: Training data DataFrame
            target_col: Name of the target column
            test_size: Proportion of data for testing
        
        Returns:
            Dictionary with training metrics
        """
        # Aggregate to daily data
        daily_data = self.aggregate_daily(df)
        
        # Define features
        feature_cols = [
            'day_of_week', 'day_of_month', 'month', 'is_weekend',
            'num_uses', 'prev_day_kwh', 'prev_week_kwh',
            'avg_last_7days', 'avg_last_30days'
        ]
        
        self.feature_names = feature_cols
        
        # Prepare data
        X = daily_data[feature_cols]
        y = daily_data[target_col]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model (using Random Forest)
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        train_pred = self.model.predict(X_train_scaled)
        test_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            'train_rmse': np.sqrt(mean_squared_error(y_train, train_pred)),
            'test_rmse': np.sqrt(mean_squared_error(y_test, test_pred)),
            'train_mae': mean_absolute_error(y_train, train_pred),
            'test_mae': mean_absolute_error(y_test, test_pred),
            'train_r2': r2_score(y_train, train_pred),
            'test_r2': r2_score(y_test, test_pred),
            'feature_importance': dict(zip(feature_cols, self.model.feature_importances_))
        }
        
        print(f"Training completed!")
        print(f"Train RMSE: {metrics['train_rmse']:.4f}, Test RMSE: {metrics['test_rmse']:.4f}")
        print(f"Train R²: {metrics['train_r2']:.4f}, Test R²: {metrics['test_r2']:.4f}")
        
        return metrics
    
    def predict_next_days(self, historical_df, days=7, tariff_rate=0.12):
        """
        Predict energy consumption for the next N days
        
        Args:
            historical_df: Historical energy data
            days: Number of days to predict
            tariff_rate: Cost per kWh
        
        Returns:
            DataFrame with predictions
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Aggregate historical data
        daily_data = self.aggregate_daily(historical_df)
        
        predictions = []
        last_date = daily_data['date'].max()
        
        # Get recent statistics
        recent_data = daily_data.tail(30)
        avg_last_7 = recent_data['total_kwh'].tail(7).mean()
        avg_last_30 = recent_data['total_kwh'].mean()
        
        for day in range(1, days + 1):
            pred_date = last_date + timedelta(days=day)
            
            # Create features for prediction
            features = {
                'day_of_week': pred_date.dayofweek,
                'day_of_month': pred_date.day,
                'month': pred_date.month,
                'is_weekend': int(pred_date.dayofweek >= 5),
                'num_uses': recent_data['num_uses'].mean(),
                'prev_day_kwh': daily_data['total_kwh'].iloc[-1] if day == 1 else predictions[-1]['predicted_kwh'],
                'prev_week_kwh': daily_data['total_kwh'].iloc[-7] if len(daily_data) >= 7 else daily_data['total_kwh'].mean(),
                'avg_last_7days': avg_last_7,
                'avg_last_30days': avg_last_30
            }
            
            # Predict
            X_pred = pd.DataFrame([features])[self.feature_names]
            X_pred_scaled = self.scaler.transform(X_pred)
            predicted_kwh = self.model.predict(X_pred_scaled)[0]
            
            # Calculate cost
            predicted_cost = predicted_kwh * tariff_rate
            
            predictions.append({
                'date': pred_date,
                'predicted_kwh': round(predicted_kwh, 4),
                'predicted_cost': round(predicted_cost, 2),
                'confidence_score': 0.85  # Can be calculated from model uncertainty
            })
        
        return pd.DataFrame(predictions)
    
    def predict_monthly(self, historical_df, tariff_rate=0.12):
        """
        Predict monthly energy consumption
        
        Args:
            historical_df: Historical energy data
            tariff_rate: Cost per kWh
        
        Returns:
            Dictionary with monthly prediction
        """
        daily_predictions = self.predict_next_days(historical_df, days=30, tariff_rate=tariff_rate)
        
        monthly_kwh = daily_predictions['predicted_kwh'].sum()
        monthly_cost = daily_predictions['predicted_cost'].sum()
        
        return {
            'predicted_monthly_kwh': round(monthly_kwh, 2),
            'predicted_monthly_cost': round(monthly_cost, 2),
            'daily_predictions': daily_predictions.to_dict('records')
        }
    
    def save_model(self, filename='energy_model.pkl'):
        """Save trained model to disk"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'trained_at': datetime.now()
        }
        
        filepath = os.path.join(self.model_path, filename)
        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filename='energy_model.pkl'):
        """Load trained model from disk"""
        filepath = os.path.join(self.model_path, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_names = model_data['feature_names']
        self.is_trained = True
        
        print(f"Model loaded from {filepath}")
        print(f"Model trained at: {model_data['trained_at']}")


# Example usage
if __name__ == "__main__":
    # Create sample data for testing
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', end='2024-10-10', freq='H')
    
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'appliance_name': np.random.choice(['AC', 'Refrigerator', 'TV', 'Washing Machine'], len(dates)),
        'power_usage_kwh': np.random.uniform(0.1, 5.0, len(dates)),
        'cost': np.random.uniform(0.01, 0.6, len(dates)),
        'user_id': 1
    })
    
    # Initialize and train model
    predictor = EnergyPredictor(model_path='../ml_models/models')
    metrics = predictor.train(sample_data)
    
    # Make predictions
    predictions = predictor.predict_next_days(sample_data, days=30)
    print("\nNext 30 days predictions:")
    print(predictions)
    
    # Save model
    predictor.save_model()
