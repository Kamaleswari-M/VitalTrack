from datetime import datetime, timedelta
import random
from web_app import app, db
from models import User, VitalSigns, EmergencyContact, Medication, Alert

def create_test_data():
    with app.app_context():
        # Check if test user exists
        test_user = User.query.filter_by(email='test@example.com').first()
        
        if not test_user:
            # Create test user
            test_user = User(
                username='test_user',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                date_of_birth=datetime(1990, 1, 1),
                gender='other'
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
        
        # Clear existing data for this user
        EmergencyContact.query.filter_by(user_id=test_user.id).delete()
        Medication.query.filter_by(user_id=test_user.id).delete()
        VitalSigns.query.filter_by(user_id=test_user.id).delete()
        Alert.query.filter_by(user_id=test_user.id).delete()
        db.session.commit()

        # Create emergency contacts
        contacts = [
            EmergencyContact(
                user_id=test_user.id,
                name='Emergency Contact 1',
                relationship='Family',
                phone='+1234567890',
                email='emergency1@example.com'
            ),
            EmergencyContact(
                user_id=test_user.id,
                name='Emergency Contact 2',
                relationship='Doctor',
                phone='+0987654321',
                email='emergency2@example.com'
            )
        ]
        db.session.bulk_save_objects(contacts)

        # Create medications
        medications = [
            Medication(
                user_id=test_user.id,
                name='Medication A',
                dosage='10mg',
                frequency='daily',
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=30)).date(),
                instructions='Take with food'
            ),
            Medication(
                user_id=test_user.id,
                name='Medication B',
                dosage='5mg',
                frequency='twice_daily',
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=15)).date(),
                instructions='Take before bed'
            )
        ]
        db.session.bulk_save_objects(medications)

        # Create vital signs data (last 24 hours)
        vital_signs = []
        for i in range(24):
            time = datetime.now() - timedelta(hours=i)
            vital_signs.append(
                VitalSigns(
                    user_id=test_user.id,
                    timestamp=time,
                    heart_rate=random.uniform(60, 100),
                    blood_pressure_systolic=random.uniform(90, 120),
                    blood_pressure_diastolic=random.uniform(60, 80),
                    temperature=random.uniform(97.0, 99.0),
                    oxygen_saturation=random.uniform(95, 100)
                )
            )
        db.session.bulk_save_objects(vital_signs)

        # Create some sample alerts
        alerts = [
            Alert(
                user_id=test_user.id,
                timestamp=datetime.now() - timedelta(hours=2),
                type='VITAL_SIGNS',
                message='Heart rate elevated',
                vital_sign='heart_rate',
                value=105.0,
                acknowledged=True
            ),
            Alert(
                user_id=test_user.id,
                timestamp=datetime.now() - timedelta(minutes=30),
                type='MEDICATION',
                message='Time to take Medication A',
                acknowledged=False
            )
        ]
        db.session.bulk_save_objects(alerts)

        db.session.commit()

        print("Test data created successfully!")
        print("Test User Credentials:")
        print("Email: test@example.com")
        print("Password: password123")

if __name__ == '__main__':
    create_test_data()
