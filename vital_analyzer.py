from datetime import datetime, timedelta
import numpy as np
from sklearn.ensemble import IsolationForest
from models import VitalSigns, Alert, db

class VitalSignsAnalyzer:
    def __init__(self):
        # Normal ranges for vital signs
        self.ranges = {
            'heart_rate': {'min': 60, 'max': 100},
            'blood_pressure_systolic': {'min': 90, 'max': 140},
            'blood_pressure_diastolic': {'min': 60, 'max': 90},
            'temperature': {'min': 36.1, 'max': 37.2},
            'oxygen_saturation': {'min': 95, 'max': 100}
        }
        
    def analyze_vitals(self, user_id, current_vitals=None):
        """Analyze vital signs and predict potential health issues"""
        # Get historical data
        history = VitalSigns.query.filter_by(user_id=user_id)\
            .order_by(VitalSigns.timestamp.desc())\
            .limit(100).all()
            
        if not history:
            return {'status': 'normal', 'alerts': [], 'predictions': []}
            
        # Prepare data for analysis
        data = self._prepare_data(history)
        
        # Check for immediate concerns
        alerts = self._check_vital_ranges(current_vitals) if current_vitals else []
        
        # Detect anomalies
        anomalies = self._detect_anomalies(data)
        
        # Analyze trends
        trends = self._analyze_trends(data)
        
        # Make predictions
        predictions = self._make_predictions(data, trends)
        
        return {
            'status': 'alert' if alerts or anomalies else 'normal',
            'alerts': alerts,
            'anomalies': anomalies,
            'trends': trends,
            'predictions': predictions
        }
        
    def _prepare_data(self, history):
        """Prepare vital signs data for analysis"""
        data = {
            'heart_rate': [],
            'blood_pressure_systolic': [],
            'blood_pressure_diastolic': [],
            'temperature': [],
            'oxygen_saturation': [],
            'timestamps': []
        }
        
        for record in history:
            for key in data.keys():
                if key != 'timestamps':
                    data[key].append(getattr(record, key))
            data['timestamps'].append(record.timestamp)
            
        return data
        
    def _check_vital_ranges(self, vitals):
        """Check if current vital signs are within normal ranges"""
        alerts = []
        
        for vital, value in vars(vitals).items():
            if vital in self.ranges and isinstance(value, (int, float)):
                range_data = self.ranges[vital]
                if value < range_data['min']:
                    alerts.append(f"Low {vital.replace('_', ' ')}: {value}")
                elif value > range_data['max']:
                    alerts.append(f"High {vital.replace('_', ' ')}: {value}")
                    
        return alerts
        
    def _detect_anomalies(self, data):
        """Detect anomalies using Isolation Forest"""
        anomalies = []
        
        # Prepare feature matrix
        X = np.column_stack([
            data['heart_rate'],
            data['blood_pressure_systolic'],
            data['blood_pressure_diastolic'],
            data['temperature'],
            data['oxygen_saturation']
        ])
        
        # Train isolation forest
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        yhat = iso_forest.fit_predict(X)
        
        # Check last reading for anomaly
        if yhat[-1] == -1:  # Anomaly detected
            anomalies.append("Unusual vital signs pattern detected")
            
        return anomalies
        
    def _analyze_trends(self, data):
        """Analyze trends in vital signs"""
        trends = []
        
        for vital in ['heart_rate', 'blood_pressure_systolic', 'blood_pressure_diastolic', 
                     'temperature', 'oxygen_saturation']:
            values = data[vital]
            if len(values) > 10:
                # Calculate trend using simple linear regression
                x = np.arange(len(values))
                z = np.polyfit(x, values, 1)
                slope = z[0]
                
                if abs(slope) > 0.1:  # Significant trend
                    direction = "increasing" if slope > 0 else "decreasing"
                    trends.append(f"{vital.replace('_', ' ')} is {direction}")
                    
        return trends
        
    def _make_predictions(self, data, trends):
        """Make health predictions based on vital signs patterns"""
        predictions = []
        
        # Example prediction rules (these should be refined based on medical expertise)
        
        # Check for potential hypertension
        if (np.mean(data['blood_pressure_systolic']) > 130 or 
            np.mean(data['blood_pressure_diastolic']) > 80):
            predictions.append("Potential hypertension detected")
            
        # Check for fever pattern
        if np.mean(data['temperature'][-5:]) > 37.2:
            predictions.append("Elevated temperature pattern detected")
            
        # Check for low oxygen trend
        if np.mean(data['oxygen_saturation'][-5:]) < 95:
            predictions.append("Declining oxygen saturation trend")
            
        # Check for irregular heart rate
        hr_std = np.std(data['heart_rate'][-10:])
        if hr_std > 15:
            predictions.append("Irregular heart rate pattern detected")
            
        return predictions

# Example usage
if __name__ == "__main__":
    from vital_simulator import VitalSignsSimulator
    
    # Create simulator and analyzer
    simulator = VitalSignsSimulator()
    analyzer = VitalSignsAnalyzer()
    
    # Generate training data (normal vitals)
    normal_data = simulator.generate_time_series(duration_minutes=60)
    
    # Train the analyzer
    analyzer.train_anomaly_detector(normal_data)
    
    # Generate test data with some abnormal vitals
    test_data = simulator.generate_time_series(
        duration_minutes=10,
        condition='post_surgery_stress'
    )
    
    # Analyze the test data
    analysis = analyzer.analyze_vitals(test_data)
    print("\nVital Signs Analysis:")
    print(f"Anomaly Percentage: {analysis['anomaly_percentage']:.2f}%")
    print(f"Average Heart Rate: {analysis['avg_heart_rate']:.2f} bpm")
    print(f"Average SpO2: {analysis['avg_spo2']:.2f}%")
    print(f"Average Temperature: {analysis['avg_temperature']:.2f}°C")
    print("\nAlerts:")
    for alert in analysis['alerts']:
        print(f"- {alert}")
    print("\nPredictions:")
    for prediction in analysis['predictions']:
        print(f"- Condition: {prediction['condition']}")
        print(f"  Confidence: {prediction['confidence']:.2f}")
        print(f"  Recommendation: {prediction['recommendation']}")

    # Analyze vitals for alerts
    vitals = {
        'heart_rate': 110,
        'spo2': 92,
        'temperature': 38.5,
        'blood_pressure': {
            'systolic': 140,
            'diastolic': 90
        }
    }
    alerts = analyzer.analyze_vitals_alerts(vitals)
    print("\nVital Signs Alerts:")
    print(f"Timestamp: {alerts['timestamp']}")
    print(f"Status: {alerts['status']}")
    for alert in alerts['alerts']:
        print(f"- Level: {alert['level']}")
        print(f"  Message: {alert['message']}")

    # Analyze vitals using AI
    vital_signs_history = simulator.generate_time_series(duration_minutes=60)
    ai_analysis = analyzer.analyze_vitals_ai(vital_signs_history)
    print("\nVital Signs AI Analysis:")
    print(f"Concerns: {ai_analysis['concerns']}")
    print(f"Trends: {ai_analysis['trends']}")
    print(f"Predictions: {ai_analysis['predictions']}")
    print(f"Anomaly Detected: {ai_analysis['anomaly_detected']}")
