from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Medication, Alert, VitalSigns
from vital_analyzer import VitalSignsAnalyzer
from emergency_handler import EmergencyHandler

watch_api = Blueprint('watch_api', __name__)

@watch_api.route('/api/watch/medications', methods=['GET'])
@login_required
def get_medications():
    """Get today's medications for the watch"""
    try:
        today = datetime.now().date()
        medications = Medication.query.filter(
            Medication.user_id == current_user.id,
            Medication.start_date <= today,
            (Medication.end_date >= today) | (Medication.end_date.is_(None))
        ).all()
        
        return jsonify({
            'success': True,
            'medications': [{
                'id': med.id,
                'name': med.name,
                'dosage': med.dosage,
                'frequency': med.frequency,
                'instructions': med.instructions
            } for med in medications]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@watch_api.route('/api/watch/vitals', methods=['POST'])
@login_required
def record_vitals():
    """Record vital signs from watch"""
    try:
        data = request.json
        
        vitals = VitalSigns(
            user_id=current_user.id,
            heart_rate=data.get('heart_rate'),
            blood_pressure_systolic=data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
            temperature=data.get('temperature'),
            oxygen_saturation=data.get('oxygen_saturation')
        )
        db.session.add(vitals)
        
        # Analyze vitals for any concerns
        analyzer = VitalSignsAnalyzer()
        analysis = analyzer.analyze_vitals(current_user.id, vitals)
        
        if analysis['alerts'] or analysis['anomalies']:
            alert = Alert(
                user_id=current_user.id,
                type='WATCH_ALERT',
                message=f"Health concerns detected via watch: {', '.join(analysis['alerts'] + analysis['anomalies'])}",
                severity='HIGH' if analysis['anomalies'] else 'MEDIUM'
            )
            db.session.add(alert)
        
        db.session.commit()
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@watch_api.route('/api/watch/sos', methods=['POST'])
@login_required
def trigger_sos():
    """Trigger SOS from watch"""
    try:
        data = request.json
        handler = EmergencyHandler()
        success, message = handler.handle_emergency(
            current_user,
            message=data.get('message', 'Emergency triggered from watch!')
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
