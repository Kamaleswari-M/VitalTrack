from datetime import datetime
import sqlite3
import json
import pandas as pd

class VitalDatabase:
    def __init__(self, db_path='vital_signs.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create vital signs table
        c.execute('''
            CREATE TABLE IF NOT EXISTS vital_signs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                heart_rate REAL,
                spo2 REAL,
                temperature REAL,
                activity_level REAL
            )
        ''')
        
        # Create predictions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS health_predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                prediction_type TEXT,
                confidence REAL,
                details TEXT
            )
        ''')
        
        # Create user profiles table
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                age INTEGER,
                gender TEXT,
                medical_conditions TEXT,
                emergency_contacts TEXT
            )
        ''')
        
        # Create medication schedule table
        c.execute('''
            CREATE TABLE IF NOT EXISTS medication_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                time TEXT,
                dosage TEXT,
                description TEXT,
                last_taken DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_vitals(self, vitals):
        """Store vital signs readings"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO vital_signs 
            (timestamp, heart_rate, spo2, temperature, activity_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            vitals['heart_rate'],
            vitals['spo2'],
            vitals['temperature'],
            vitals['activity_level']
        ))
        
        conn.commit()
        conn.close()
    
    def store_prediction(self, prediction):
        """Store health predictions"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO health_predictions 
            (timestamp, prediction_type, confidence, details)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now(),
            prediction['condition'],
            prediction['confidence'],
            prediction['recommendation']
        ))
        
        conn.commit()
        conn.close()
    
    def get_vital_history(self, hours=24):
        """Get vital signs history for the last n hours"""
        conn = sqlite3.connect(self.db_path)
        
        query = f'''
            SELECT * FROM vital_signs 
            WHERE timestamp >= datetime('now', '-{hours} hours')
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def get_prediction_history(self, days=7):
        """Get prediction history for the last n days"""
        conn = sqlite3.connect(self.db_path)
        
        query = f'''
            SELECT * FROM health_predictions 
            WHERE timestamp >= datetime('now', '-{days} days')
            ORDER BY timestamp DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def update_user_profile(self, profile_data):
        """Update user profile"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Convert lists/dicts to JSON strings
        if 'medical_conditions' in profile_data:
            profile_data['medical_conditions'] = json.dumps(profile_data['medical_conditions'])
        if 'emergency_contacts' in profile_data:
            profile_data['emergency_contacts'] = json.dumps(profile_data['emergency_contacts'])
        
        # Check if profile exists
        c.execute('SELECT id FROM user_profiles WHERE id = 1')
        if c.fetchone() is None:
            # Insert new profile
            columns = ', '.join(profile_data.keys())
            placeholders = ', '.join(['?' for _ in profile_data])
            query = f'INSERT INTO user_profiles ({columns}) VALUES ({placeholders})'
        else:
            # Update existing profile
            set_clause = ', '.join([f'{k} = ?' for k in profile_data.keys()])
            query = f'UPDATE user_profiles SET {set_clause} WHERE id = 1'
        
        c.execute(query, list(profile_data.values()))
        conn.commit()
        conn.close()
    
    def get_user_profile(self):
        """Get user profile"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT * FROM user_profiles WHERE id = 1')
        row = c.fetchone()
        
        if row:
            columns = [description[0] for description in c.description]
            profile = dict(zip(columns, row))
            
            # Convert JSON strings back to Python objects
            if profile.get('medical_conditions'):
                profile['medical_conditions'] = json.loads(profile['medical_conditions'])
            if profile.get('emergency_contacts'):
                profile['emergency_contacts'] = json.loads(profile['emergency_contacts'])
        else:
            profile = None
            
        conn.close()
        return profile
