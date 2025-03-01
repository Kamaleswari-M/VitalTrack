import random
import numpy as np
from datetime import datetime

class VitalSignsSimulator:
    def __init__(self):
        # Define normal ranges for vital signs
        self.normal_ranges = {
            'heart_rate': (60, 100),
            'spo2': (95, 100),
            'temperature': (97.0, 99.0),
            'systolic': (90, 120),
            'diastolic': (60, 80)
        }

    def generate_normal_vitals(self):
        """Generate normal vital signs with small random variations"""
        heart_rate = random.uniform(
            self.normal_ranges['heart_rate'][0] + 5,
            self.normal_ranges['heart_rate'][1] - 5
        )
        
        spo2 = random.uniform(
            self.normal_ranges['spo2'][0] + 1,
            self.normal_ranges['spo2'][1]
        )
        
        temperature = random.uniform(
            self.normal_ranges['temperature'][0] + 0.5,
            self.normal_ranges['temperature'][1] - 0.5
        )
        
        systolic = random.uniform(
            self.normal_ranges['systolic'][0] + 5,
            self.normal_ranges['systolic'][1] - 5
        )
        
        diastolic = random.uniform(
            self.normal_ranges['diastolic'][0] + 5,
            self.normal_ranges['diastolic'][1] - 5
        )

        return {
            'timestamp': datetime.now().isoformat(),
            'heart_rate': round(heart_rate, 1),
            'spo2': round(spo2, 1),
            'temperature': round(temperature, 1),
            'blood_pressure': {
                'systolic': round(systolic),
                'diastolic': round(diastolic)
            }
        }

    def generate_abnormal_vitals(self):
        """Generate abnormal vital signs for testing alerts"""
        # Randomly choose which vital sign will be abnormal
        abnormal_type = random.choice(['heart_rate', 'spo2', 'temperature', 'blood_pressure'])
        
        vitals = self.generate_normal_vitals()
        
        if abnormal_type == 'heart_rate':
            # Generate either very high or very low heart rate
            if random.random() < 0.5:
                vitals['heart_rate'] = random.uniform(40, 55)  # Low
            else:
                vitals['heart_rate'] = random.uniform(105, 120)  # High
        
        elif abnormal_type == 'spo2':
            vitals['spo2'] = random.uniform(85, 92)  # Low oxygen
        
        elif abnormal_type == 'temperature':
            if random.random() < 0.5:
                vitals['temperature'] = random.uniform(95, 96.5)  # Low
            else:
                vitals['temperature'] = random.uniform(99.5, 101)  # High
        
        else:  # blood_pressure
            if random.random() < 0.5:
                # High blood pressure
                vitals['blood_pressure']['systolic'] = random.uniform(130, 140)
                vitals['blood_pressure']['diastolic'] = random.uniform(85, 90)
            else:
                # Low blood pressure
                vitals['blood_pressure']['systolic'] = random.uniform(80, 85)
                vitals['blood_pressure']['diastolic'] = random.uniform(50, 55)

        return vitals

# Example usage
if __name__ == "__main__":
    simulator = VitalSignsSimulator()
    
    # Generate normal vital signs
    normal_vitals = simulator.generate_normal_vitals()
    print("\nNormal Vital Signs Sample:")
    print(normal_vitals)
    
    # Generate abnormal vital signs
    abnormal_vitals = simulator.generate_abnormal_vitals()
    print("\nAbnormal Vital Signs Sample:")
    print(abnormal_vitals)
