import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from datetime import datetime, timedelta
from models import VitalSigns, Alert, db

class HealthPredictor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.anomaly_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        self.vital_predictors = {
            'heart_rate': RandomForestRegressor(n_estimators=100, random_state=42),
            'blood_pressure_systolic': RandomForestRegressor(n_estimators=100, random_state=42),
            'blood_pressure_diastolic': RandomForestRegressor(n_estimators=100, random_state=42),
            'temperature': RandomForestRegressor(n_estimators=100, random_state=42),
            'oxygen_saturation': RandomForestRegressor(n_estimators=100, random_state=42)
        }
        
    def prepare_data(self, vital_signs):
        """Prepare vital signs data for analysis"""
        df = pd.DataFrame([{
            'timestamp': vs.timestamp,
            'heart_rate': vs.heart_rate,
            'blood_pressure_systolic': vs.blood_pressure_systolic,
            'blood_pressure_diastolic': vs.blood_pressure_diastolic,
            'temperature': vs.temperature,
            'oxygen_saturation': vs.oxygen_saturation
        } for vs in vital_signs])
        
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        return df
        
    def extract_features(self, df):
        """Extract time-based features from vital signs data"""
        # Calculate rolling statistics
        rolling_mean = df.rolling(window=5).mean()
        rolling_std = df.rolling(window=5).std()
        
        # Calculate rate of change
        rate_of_change = df.diff()
        
        # Combine features
        features = pd.concat([
            df,
            rolling_mean.add_suffix('_mean'),
            rolling_std.add_suffix('_std'),
            rate_of_change.add_suffix('_change')
        ], axis=1)
        
        return features.fillna(method='bfill')
        
    def detect_anomalies(self, user_id, hours=24):
        """Detect anomalies in vital signs"""
        # Get recent vital signs
        since = datetime.utcnow() - timedelta(hours=hours)
        vital_signs = VitalSigns.query.filter(
            VitalSigns.user_id == user_id,
            VitalSigns.timestamp >= since
        ).order_by(VitalSigns.timestamp.asc()).all()
        
        if len(vital_signs) < 10:  # Need minimum data points
            return []
            
        # Prepare data
        df = self.prepare_data(vital_signs)
        features = self.extract_features(df)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Detect anomalies
        anomaly_labels = self.anomaly_detector.fit_predict(scaled_features)
        anomaly_indices = np.where(anomaly_labels == -1)[0]
        
        anomalies = []
        if len(anomaly_indices) > 0:
            for idx in anomaly_indices[-3:]:  # Get last 3 anomalies
                timestamp = df.index[idx]
                values = df.iloc[idx]
                
                # Determine which vital signs are anomalous
                for vital, value in values.items():
                    mean = df[vital].mean()
                    std = df[vital].std()
                    if abs(value - mean) > 2 * std:  # Outside 2 standard deviations
                        anomalies.append({
                            'timestamp': timestamp,
                            'vital_sign': vital,
                            'value': value,
                            'expected_range': f'{mean - std:.1f} - {mean + std:.1f}'
                        })
        
        return anomalies
        
    def predict_trends(self, user_id, hours=24, forecast_hours=4):
        """Predict vital sign trends for the next few hours"""
        # Get recent vital signs
        since = datetime.utcnow() - timedelta(hours=hours)
        vital_signs = VitalSigns.query.filter(
            VitalSigns.user_id == user_id,
            VitalSigns.timestamp >= since
        ).order_by(VitalSigns.timestamp.asc()).all()
        
        if len(vital_signs) < 10:  # Need minimum data points
            return {}
            
        # Prepare data
        df = self.prepare_data(vital_signs)
        features = self.extract_features(df)
        
        predictions = {}
        future_times = pd.date_range(
            start=df.index[-1],
            periods=forecast_hours + 1,
            freq='H'
        )[1:]
        
        # Predict each vital sign
        for vital, model in self.vital_predictors.items():
            # Prepare target variable
            y = df[vital].values
            
            # Use last 'forecast_hours' points as features
            X = features.iloc[-forecast_hours:].values
            
            # Fit model
            model.fit(X, y[-forecast_hours:])
            
            # Predict next points
            future_values = []
            last_features = X[-1:]
            
            for _ in range(forecast_hours):
                pred = model.predict(last_features)[0]
                future_values.append(pred)
                
                # Update features for next prediction
                last_features = np.roll(last_features, -1)
                last_features[0][-1] = pred
            
            predictions[vital] = list(zip(future_times, future_values))
        
        return predictions
        
    def generate_health_insights(self, user_id):
        """Generate health insights based on vital signs analysis"""
        # Detect anomalies
        anomalies = self.detect_anomalies(user_id)
        
        # Predict trends
        predictions = self.predict_trends(user_id)
        
        insights = []
        
        # Analyze anomalies
        if anomalies:
            for anomaly in anomalies:
                insights.append({
                    'type': 'anomaly',
                    'severity': 'warning',
                    'message': f"Unusual {anomaly['vital_sign'].replace('_', ' ')} detected: "
                             f"{anomaly['value']:.1f} (Expected range: {anomaly['expected_range']})",
                    'timestamp': anomaly['timestamp']
                })
        
        # Analyze predictions
        if predictions:
            for vital, pred_values in predictions.items():
                last_value = pred_values[-1][1]
                first_value = pred_values[0][1]
                change = ((last_value - first_value) / first_value) * 100
                
                if abs(change) > 10:  # Significant change
                    direction = 'increase' if change > 0 else 'decrease'
                    insights.append({
                        'type': 'trend',
                        'severity': 'info',
                        'message': f"Predicted {abs(change):.1f}% {direction} in "
                                 f"{vital.replace('_', ' ')} over next {len(pred_values)} hours",
                        'timestamp': datetime.utcnow()
                    })
        
        return insights
        
    def save_insights(self, user_id, insights):
        """Save generated insights as alerts if they are significant"""
        for insight in insights:
            if insight['severity'] in ['warning', 'danger']:
                alert = Alert(
                    user_id=user_id,
                    type=insight['severity'],
                    message=insight['message'],
                    timestamp=insight['timestamp']
                )
                db.session.add(alert)
        
        db.session.commit()
