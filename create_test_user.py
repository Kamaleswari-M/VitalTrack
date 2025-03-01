from web_app import app, db
from models import User, EmergencyContact
from datetime import datetime, date

def create_test_user():
    with app.app_context():
        # Create test user if it doesn't exist
        user = User.query.filter_by(username='test').first()
        if not user:
            user = User(
                username='test',
                email='test@example.com',
                first_name='Test',
                last_name='User',
                date_of_birth=date(1990, 1, 1),
                gender='Other'
            )
            user.set_password('test123')
            db.session.add(user)
            
            # Add emergency contact
            contact = EmergencyContact(
                user=user,
                name='Emergency Contact',
                relationship='Family',
                phone='+0987654321',
                email='emergency@example.com'
            )
            db.session.add(contact)
            
            db.session.commit()
            print("Test user created successfully!")
        else:
            print("Test user already exists!")

if __name__ == '__main__':
    create_test_user()
