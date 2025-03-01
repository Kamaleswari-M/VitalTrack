from flask import Blueprint, jsonify, request
from database import VitalDatabase
from vital_analyzer import VitalSignsAnalyzer
from vital_manager import VitalManager
import jwt
import datetime

api = Blueprint('api', __name__)
db = VitalDatabase()
analyzer = VitalSignsAnalyzer()
manager = VitalManager()

# Secret key for JWT
SECRET_KEY = "your-secret-key"  # In production, use environment variable

def generate_token(user_id):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def token_required(f):
    """Decorator for JWT token verification"""
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.split()[1]  # Remove 'Bearer' prefix
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    
    return decorated

@api.route('/vitals/current', methods=['GET'])
@token_required
def get_current_vitals():
    """Get current vital signs"""
    vitals = db.get_vital_history(hours=1).iloc[0].to_dict() if not db.get_vital_history(hours=1).empty else {}
    return jsonify(vitals)

@api.route('/vitals/history', methods=['GET'])
@token_required
def get_vitals_history():
    """Get vital signs history"""
    hours = request.args.get('hours', default=24, type=int)
    history = db.get_vital_history(hours=hours).to_dict('records')
    return jsonify(history)

@api.route('/predictions', methods=['GET'])
@token_required
def get_predictions():
    """Get health predictions"""
    days = request.args.get('days', default=7, type=int)
    predictions = db.get_prediction_history(days=days).to_dict('records')
    return jsonify(predictions)

@api.route('/profile', methods=['GET', 'PUT'])
@token_required
def handle_profile():
    """Get or update user profile"""
    if request.method == 'GET':
        profile = db.get_user_profile()
        return jsonify(profile)
    else:
        profile_data = request.json
        db.update_user_profile(profile_data)
        return jsonify({'message': 'Profile updated successfully'})

@api.route('/medications', methods=['GET', 'POST'])
@token_required
def handle_medications():
    """Get or add medication reminders"""
    if request.method == 'GET':
        # Get medication schedule
        return jsonify(manager.medication_schedule)
    else:
        # Add new medication
        data = request.json
        manager.add_medication_reminder(
            name=data['name'],
            time_str=data['time'],
            dosage=data['dosage'],
            description=data.get('description', '')
        )
        return jsonify({'message': 'Medication reminder added successfully'})

@api.route('/sos', methods=['POST'])
@token_required
def trigger_sos():
    """Trigger SOS alert"""
    success = manager.trigger_sos()
    return jsonify({'success': success})

@api.route('/contacts', methods=['GET', 'POST'])
@token_required
def handle_contacts():
    """Get or add emergency contacts"""
    if request.method == 'GET':
        return jsonify(manager.emergency_contacts)
    else:
        data = request.json
        manager.add_emergency_contact(
            name=data['name'],
            phone=data['phone'],
            relationship=data.get('relationship', '')
        )
        return jsonify({'message': 'Emergency contact added successfully'})

# Health insights and recommendations
@api.route('/insights', methods=['GET'])
@token_required
def get_health_insights():
    """Get personalized health insights"""
    vitals_df = db.get_vital_history(hours=24)
    if not vitals_df.empty:
        analysis = analyzer.analyze_vitals(vitals_df)
        return jsonify(analysis)
    return jsonify({'message': 'No recent data available'})
