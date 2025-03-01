from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from threading import Thread
import time
import os
from dotenv import load_dotenv
from models import db, User, EmergencyContact, Medication, VitalSigns, Alert, NotificationLog
from emergency_handler import EmergencyHandler
from medication_reminder import MedicationReminder
from vital_analyzer import VitalSignsAnalyzer
from watch_api import watch_api

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vital_signs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize services
emergency_handler = EmergencyHandler()
medication_reminder = MedicationReminder()

# Register blueprints
app.register_blueprint(watch_api)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    medications = Medication.query.filter_by(user_id=current_user.id).all()
    alerts = Alert.query.filter_by(user_id=current_user.id).order_by(Alert.timestamp.desc()).limit(5).all()
    return render_template('dashboard.html', medications=medications, alerts=alerts)

@app.route('/medications')
@login_required
def medications():
    """Display user's medications"""
    medications = Medication.query.filter_by(user_id=current_user.id).all()
    return render_template('medications.html', medications=medications)

@app.route('/add_medication', methods=['POST'])
@login_required
def add_medication():
    """Add a new medication"""
    try:
        # Parse dates
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date = None
        if request.form.get('end_date'):
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        
        # Create medication
        medication = Medication(
            user_id=current_user.id,
            name=request.form['name'],
            dosage=request.form['dosage'],
            frequency=request.form['frequency'],
            start_date=start_date,
            end_date=end_date,
            instructions=request.form.get('instructions', '')
        )
        
        db.session.add(medication)
        db.session.commit()
        
        flash('Medication added successfully!', 'success')
        return redirect(url_for('medications'))
        
    except Exception as e:
        flash(f'Error adding medication: {str(e)}', 'danger')
        return redirect(url_for('medications'))

@app.route('/medication/<int:id>', methods=['GET'])
@login_required
def get_medication(id):
    """Get medication details for editing"""
    medication = Medication.query.get_or_404(id)
    
    if medication.user_id != current_user.id:
        abort(403)
    
    return jsonify({
        'name': medication.name,
        'dosage': medication.dosage,
        'frequency': medication.frequency,
        'start_date': medication.start_date.strftime('%Y-%m-%d'),
        'end_date': medication.end_date.strftime('%Y-%m-%d') if medication.end_date else '',
        'instructions': medication.instructions
    })

@app.route('/medication/<int:id>/edit', methods=['POST'])
@login_required
def edit_medication(id):
    """Edit an existing medication"""
    medication = Medication.query.get_or_404(id)
    
    if medication.user_id != current_user.id:
        abort(403)
    
    try:
        medication.name = request.form['name']
        medication.dosage = request.form['dosage']
        medication.frequency = request.form['frequency']
        medication.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        if request.form.get('end_date'):
            medication.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
        medication.instructions = request.form.get('instructions', '')
        
        db.session.commit()
        flash('Medication updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating medication: {str(e)}', 'danger')
        app.logger.error(f"Error updating medication: {str(e)}")
    
    return redirect(url_for('medications'))

@app.route('/medication/<int:id>/delete', methods=['POST'])
@login_required
def delete_medication(id):
    """Delete a medication"""
    medication = Medication.query.get_or_404(id)
    if medication.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        db.session.delete(medication)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/contacts')
@login_required
def contacts():
    """Display emergency contacts"""
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    return render_template('contacts.html', contacts=contacts)

@app.route('/add_contact', methods=['POST'])
@login_required
def add_contact():
    """Add a new emergency contact"""
    try:
        contact = EmergencyContact(
            user_id=current_user.id,
            name=request.form['name'],
            phone=request.form['phone'],
            email=request.form['email'],
            relationship=request.form['relationship']
        )
        db.session.add(contact)
        db.session.commit()
        flash('Emergency contact added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding contact: {str(e)}', 'danger')
    
    return redirect(url_for('contacts'))

@app.route('/contact/<int:contact_id>', methods=['GET'])
@login_required
def get_contact(contact_id):
    """Get contact details for editing"""
    contact = EmergencyContact.query.get_or_404(contact_id)
    
    if contact.user_id != current_user.id:
        abort(403)
    
    return jsonify({
        'name': contact.name,
        'phone': contact.phone,
        'email': contact.email,
        'relationship': contact.relationship
    })

@app.route('/contact/<int:contact_id>/edit', methods=['POST'])
@login_required
def edit_contact(contact_id):
    """Edit an existing contact"""
    contact = EmergencyContact.query.get_or_404(contact_id)
    
    if contact.user_id != current_user.id:
        abort(403)
    
    try:
        contact.name = request.form['name']
        contact.phone = request.form['phone']
        contact.email = request.form['email']
        contact.relationship = request.form['relationship']
        
        db.session.commit()
        flash('Emergency contact updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating contact: {str(e)}', 'danger')
    
    return redirect(url_for('contacts'))

@app.route('/contact/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    """Delete an emergency contact"""
    contact = EmergencyContact.query.get_or_404(contact_id)
    
    if contact.user_id != current_user.id:
        abort(403)
    
    try:
        db.session.delete(contact)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/api/reports/<timeframe>')
@login_required
def get_report_data(timeframe):
    # Get vital signs data based on timeframe
    if timeframe == 'daily':
        data = VitalSigns.query.filter(
            VitalSigns.user_id == current_user.id,
            VitalSigns.timestamp >= datetime.now().replace(hour=0, minute=0, second=0)
        ).all()
    elif timeframe == 'weekly':
        data = VitalSigns.query.filter(
            VitalSigns.user_id == current_user.id,
            VitalSigns.timestamp >= datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=7)
        ).all()
    else:  # monthly
        data = VitalSigns.query.filter(
            VitalSigns.user_id == current_user.id,
            VitalSigns.timestamp >= datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=30)
        ).all()

    return jsonify({
        'timestamps': [d.timestamp.strftime('%Y-%m-%d %H:%M') for d in data],
        'heart_rate': [d.heart_rate for d in data],
        'spo2': [d.spo2 for d in data],
        'temperature': [d.temperature for d in data],
        'activity': [d.activity_level for d in data],
        'insights': [{
            'date': d.timestamp.strftime('%Y-%m-%d'),
            'avg_heart_rate': d.heart_rate,
            'avg_spo2': d.spo2,
            'avg_temperature': d.temperature,
            'activity_level': d.activity_level,
            'alerts': len(d.alerts) if hasattr(d, 'alerts') else 0
        } for d in data]
    })

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                current_user.profile_pic = filename
                db.session.commit()
                return jsonify({'success': True})
            return jsonify({'success': False, 'message': 'Invalid file type'})
        
        # Handle profile update
        current_user.first_name = request.form.get('first_name', current_user.first_name)
        current_user.last_name = request.form.get('last_name', current_user.last_name)
        current_user.email = request.form.get('email', current_user.email)
        current_user.phone = request.form.get('phone', current_user.phone)
        db.session.commit()
        return jsonify({'success': True})

    stats = {
        'total_alerts': Alert.query.filter_by(user_id=current_user.id).count(),
        'total_medications': Medication.query.filter_by(user_id=current_user.id).count(),
        'total_contacts': EmergencyContact.query.filter_by(user_id=current_user.id).count()
    }
    
    return render_template('profile.html', stats=stats)

@app.route('/update_medical_info', methods=['POST'])
@login_required
def update_medical_info():
    current_user.medical_conditions = request.form.get('medical_conditions', '')
    current_user.allergies = request.form.get('allergies', '')
    current_user.blood_type = request.form.get('blood_type', '')
    db.session.commit()
    return jsonify({'success': True})

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if not current_user.check_password(request.form['current_password']):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    current_user.set_password(request.form['new_password'])
    db.session.commit()
    return jsonify({'success': True})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if passwords match
        if request.form['password'] != request.form['confirm_password']:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        # Check if email already exists
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Check if username already exists
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already taken', 'danger')
            return render_template('register.html')

        # Create new user
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            phone=request.form['phone'],
            medical_conditions=request.form.get('medical_conditions', '')
        )
        user.set_password(request.form['password'])
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/record_vital_signs', methods=['POST'])
@login_required
def record_vital_signs():
    vital_signs = VitalSigns(
        user_id=current_user.id,
        heart_rate=float(request.form['heart_rate']),
        blood_pressure_systolic=float(request.form['blood_pressure_systolic']),
        blood_pressure_diastolic=float(request.form['blood_pressure_diastolic']),
        temperature=float(request.form['temperature']),
        oxygen_saturation=float(request.form['oxygen_saturation'])
    )
    
    db.session.add(vital_signs)
    
    # Analyze the new vital signs
    recent_vitals = VitalSigns.query.filter_by(user_id=current_user.id).order_by(VitalSigns.timestamp.desc()).limit(10).all()
    analysis = vital_analyzer.analyze_vitals_ai(recent_vitals)
    
    # Handle any detected anomalies
    if analysis['anomaly_detected']:
        alert = Alert(
            user_id=current_user.id,
            type='vital_signs',
            message='; '.join(analysis['concerns']),
            vital_sign='multiple',
            value=0.0
        )
        db.session.add(alert)
        
        # Notify emergency contacts if critical
        if any('critical' in concern.lower() for concern in analysis['concerns']):
            emergency_handler.handle_emergency(
                current_user,
                vital_signs,
                "Critical vital signs detected: " + '; '.join(analysis['concerns'])
            )
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Vital signs recorded successfully',
        'analysis': analysis
    })

@app.route('/trigger_sos', methods=['POST'])
@login_required
def trigger_sos():
    """Trigger SOS alert"""
    user = current_user
    
    # Get latest vital signs if available
    vital_signs = VitalSigns.query.filter_by(user_id=user.id).order_by(VitalSigns.timestamp.desc()).first()
    
    # Get message from request if provided
    message = request.form.get('message', '')
    
    # Handle emergency
    handler = EmergencyHandler()
    success = handler.handle_emergency(user, vital_signs, message)
    
    if success:
        flash('SOS alert triggered successfully! Emergency contacts have been notified.', 'success')
    else:
        flash('Failed to trigger SOS alert. Please add emergency contacts first.', 'danger')
    
    return jsonify({'status': 'success' if success else 'error'})

@app.route('/check_medication_reminders')
@login_required
def check_medication_reminders():
    """Check for due medications and send reminders"""
    user = current_user
    current_time = datetime.now()
    
    # Get all active medications
    medications = Medication.query.filter_by(user_id=user.id, active=True).all()
    
    reminders = []
    for med in medications:
        if med.is_due(current_time):
            reminder_msg = f"Time to take {med.name} - {med.dosage}"
            flash(reminder_msg, 'info')
            reminders.append(reminder_msg)
            
            # Log the reminder
            log = NotificationLog(
                user_id=user.id,
                type='MEDICATION_REMINDER',
                severity='MEDIUM',
                message=reminder_msg,
                channels='APP_NOTIFICATION'
            )
            db.session.add(log)
    
    db.session.commit()
    return jsonify({'reminders': reminders})

@app.route('/predictions')
@login_required
def predictions():
    """Show AI predictions page"""
    # Get latest vital signs
    latest_vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
        .order_by(VitalSigns.timestamp.desc())\
        .first()
    
    if not latest_vitals:
        flash('No vital signs data available. Please add some vital signs first.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Get AI analysis
    analyzer = VitalSignsAnalyzer()
    analysis = analyzer.analyze_vitals(current_user.id, latest_vitals)
    
    return render_template('predictions.html', 
                         latest_vitals=latest_vitals,
                         analysis=analysis)

@app.route('/analyze_health')
@login_required
def analyze_health():
    """Analyze health and return results"""
    latest_vitals = VitalSigns.query.filter_by(user_id=current_user.id)\
        .order_by(VitalSigns.timestamp.desc())\
        .first()
    
    if not latest_vitals:
        return jsonify({'success': False, 'message': 'No vital signs data available'})
    
    analyzer = VitalSignsAnalyzer()
    analysis = analyzer.analyze_vitals(current_user.id, latest_vitals)
    
    # Create alerts for any anomalies or concerns
    if analysis['alerts'] or analysis['anomalies']:
        alert = Alert(
            user_id=current_user.id,
            type='AI_PREDICTION',
            message=f"Health concerns detected: {', '.join(analysis['alerts'] + analysis['anomalies'])}",
            severity='HIGH' if analysis['anomalies'] else 'MEDIUM'
        )
        db.session.add(alert)
        db.session.commit()
    
    return jsonify({'success': True, 'analysis': analysis})

# API Routes
@app.route('/api/sos', methods=['POST'])
@login_required
def trigger_sos_api():
    success = emergency_handler.handle_sos(current_user.id)
    return jsonify({'success': success})

@app.route('/api/vital-signs', methods=['POST'])
@login_required
def record_vital_signs_api():
    data = request.json
    vital_signs = VitalSigns(
        user_id=current_user.id,
        heart_rate=data.get('heart_rate'),
        blood_pressure_systolic=data.get('systolic'),
        blood_pressure_diastolic=data.get('diastolic'),
        temperature=data.get('temperature'),
        oxygen_saturation=data.get('spo2')
    )
    
    db.session.add(vital_signs)
    db.session.commit()
    
    # Analyze vitals and emit updates
    analysis = vital_analyzer.analyze_vitals(vital_signs)
    
    return jsonify({'success': True})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Background task for medication reminders
def check_medication_reminders():
    with app.app_context():
        while True:
            users = User.query.all()
            for user in users:
                medication_reminder.check_medications(user)
            time.sleep(300)  # Check every 5 minutes

# Start background task
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    reminder_thread = Thread(target=check_medication_reminders)
    reminder_thread.daemon = True
    reminder_thread.start()

if __name__ == '__main__':
    try:
        with app.app_context():
            db.create_all()  # Create database tables
        app.run(host='127.0.0.1', port=8080, debug=True)
    except KeyboardInterrupt:
        print("Shutting down gracefully...")
