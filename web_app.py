from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, make_response
from flask_socketio import SocketIO, emit
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json

from models import db, User, VitalSigns, EmergencyContact, Medication, Alert, NotificationPreference, NotificationLog, ReportSchedule
from vital_simulator import VitalSignsSimulator as VitalSimulator
from vital_analyzer import VitalSignsAnalyzer as VitalAnalyzer
from auth import auth_bp, login_manager
from swagger_ui import swagger_bp
from predictive_analytics import HealthPredictor
from notification_system import NotificationSystem
from api import api_bp
from analytics.report_generator import HealthReport
from scheduler import ReportScheduler
from data_export import DataExporter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vital_signs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
socketio = SocketIO(app)
db.init_app(app)
login_manager.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(swagger_bp)
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/vital-signs/latest')
@login_required
def get_latest_vital_signs():
    vital_signs = VitalSigns.query.filter_by(user_id=current_user.id).order_by(VitalSigns.timestamp.desc()).first()
    if vital_signs:
        return jsonify({
            'heart_rate': vital_signs.heart_rate,
            'blood_pressure': f'{vital_signs.blood_pressure_systolic}/{vital_signs.blood_pressure_diastolic}',
            'temperature': vital_signs.temperature,
            'oxygen_saturation': vital_signs.oxygen_saturation,
            'timestamp': vital_signs.timestamp.isoformat()
        })
    return jsonify({})

@app.route('/api/vital-signs/history')
@login_required
def get_vital_signs_history():
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    vital_signs = VitalSigns.query.filter(
        VitalSigns.user_id == current_user.id,
        VitalSigns.timestamp >= since
    ).order_by(VitalSigns.timestamp.asc()).all()
    
    return jsonify([{
        'heart_rate': vs.heart_rate,
        'blood_pressure_systolic': vs.blood_pressure_systolic,
        'blood_pressure_diastolic': vs.blood_pressure_diastolic,
        'temperature': vs.temperature,
        'oxygen_saturation': vs.oxygen_saturation,
        'timestamp': vs.timestamp.isoformat()
    } for vs in vital_signs])

@app.route('/api/alerts')
@login_required
def get_alerts():
    alerts = Alert.query.filter_by(
        user_id=current_user.id,
        acknowledged=False
    ).order_by(Alert.timestamp.desc()).all()
    
    return jsonify([{
        'id': alert.id,
        'type': alert.type,
        'message': alert.message,
        'vital_sign': alert.vital_sign,
        'value': alert.value,
        'timestamp': alert.timestamp.isoformat()
    } for alert in alerts])

@app.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    if alert.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    alert.acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/emergency-contacts', methods=['GET', 'POST'])
@login_required
def manage_emergency_contacts():
    if request.method == 'POST':
        contact = EmergencyContact(
            user_id=current_user.id,
            name=request.form['name'],
            relationship=request.form['relationship'],
            phone=request.form['phone'],
            email=request.form.get('email')
        )
        db.session.add(contact)
        db.session.commit()
        flash('Emergency contact added successfully!', 'success')
        return redirect(url_for('auth.profile'))
        
    contacts = EmergencyContact.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': contact.id,
        'name': contact.name,
        'relationship': contact.relationship,
        'phone': contact.phone,
        'email': contact.email
    } for contact in contacts])

@app.route('/api/medications', methods=['GET', 'POST'])
@login_required
def manage_medications():
    if request.method == 'POST':
        medication = Medication(
            user_id=current_user.id,
            name=request.form['name'],
            dosage=request.form['dosage'],
            frequency=request.form['frequency'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date() if request.form.get('end_date') else None,
            instructions=request.form.get('instructions')
        )
        db.session.add(medication)
        db.session.commit()
        flash('Medication added successfully!', 'success')
        return redirect(url_for('auth.profile'))
        
    medications = Medication.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': med.id,
        'name': med.name,
        'dosage': med.dosage,
        'frequency': med.frequency,
        'start_date': med.start_date.isoformat(),
        'end_date': med.end_date.isoformat() if med.end_date else None,
        'instructions': med.instructions
    } for med in medications])

@app.route('/reports')
@login_required
def view_reports():
    """View health reports dashboard"""
    return render_template('reports.html')

@app.route('/reports/generate', methods=['POST'])
@login_required
def generate_report():
    """Generate and download PDF health report"""
    days = request.form.get('days', 30, type=int)
    report_generator = HealthReport(current_user.id)
    pdf_data = report_generator.generate_pdf_report(days)
    
    if not pdf_data:
        flash('No data available to generate report', 'error')
        return redirect(url_for('view_reports'))
    
    response = make_response(pdf_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=health_report_{datetime.now().strftime("%Y%m%d")}.pdf'
    return response

@app.route('/reports/stats')
@login_required
def get_report_stats():
    """Get vital statistics for charts"""
    days = request.args.get('days', 30, type=int)
    report_generator = HealthReport(current_user.id)
    stats, df = report_generator.generate_vital_stats(days)
    
    if not stats:
        return jsonify({'error': 'No data available'}), 404
        
    charts = report_generator.generate_trend_charts(df)
    alert_summary = report_generator.generate_alert_summary(days)
    
    return jsonify({
        'stats': stats,
        'charts': charts,
        'alert_summary': alert_summary
    })

@app.route('/insights')
@login_required
def get_health_insights():
    """Get predictive health insights for the current user"""
    insights = health_predictor.generate_health_insights(current_user.id)
    
    # Send notifications for each insight
    for insight in insights:
        notification_system.handle_prediction(current_user.id, insight)
    
    return jsonify(insights)

@app.route('/predictions')
@login_required
def get_predictions():
    """Get vital signs predictions for the next few hours"""
    hours = request.args.get('hours', 24, type=int)
    forecast_hours = request.args.get('forecast', 4, type=int)
    predictions = health_predictor.predict_trends(
        current_user.id,
        hours=hours,
        forecast_hours=forecast_hours
    )
    return jsonify(predictions)

@app.route('/anomalies')
@login_required
def get_anomalies():
    """Get detected anomalies in vital signs"""
    hours = request.args.get('hours', 24, type=int)
    anomalies = health_predictor.detect_anomalies(
        current_user.id,
        hours=hours
    )
    return jsonify(anomalies)

@app.route('/notifications/preferences', methods=['GET'])
@login_required
def notification_preferences():
    """View notification preferences"""
    preferences = NotificationPreference.query.filter_by(user_id=current_user.id).first()
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.session.add(preferences)
        db.session.commit()
    
    # Get recent notification logs
    logs = NotificationLog.query.filter_by(user_id=current_user.id)\
        .order_by(NotificationLog.timestamp.desc())\
        .limit(50)\
        .all()
    
    return render_template(
        'notification_preferences.html',
        preferences=preferences,
        notification_logs=logs
    )

@app.route('/notifications/preferences', methods=['POST'])
@login_required
def update_notification_preferences():
    """Update notification preferences"""
    preferences = NotificationPreference.query.filter_by(user_id=current_user.id).first()
    if not preferences:
        preferences = NotificationPreference(user_id=current_user.id)
        db.session.add(preferences)
    
    # Update preferences
    preferences.email_enabled = request.form.get('email_enabled') == 'on'
    preferences.sms_enabled = request.form.get('sms_enabled') == 'on'
    
    quiet_start = request.form.get('quiet_hours_start')
    quiet_end = request.form.get('quiet_hours_end')
    
    if quiet_start:
        preferences.quiet_hours_start = datetime.strptime(quiet_start, '%H:%M').time()
    if quiet_end:
        preferences.quiet_hours_end = datetime.strptime(quiet_end, '%H:%M').time()
    
    db.session.commit()
    flash('Notification preferences updated successfully', 'success')
    return redirect(url_for('notification_preferences'))

@app.route('/notifications/test', methods=['POST'])
@login_required
def test_notifications():
    """Send test notifications"""
    notification_type = request.form.get('type', 'info')
    
    test_prediction = {
        'type': 'test',
        'message': 'This is a test notification.',
        'timestamp': datetime.utcnow()
    }
    
    notification_system.handle_prediction(current_user.id, test_prediction)
    flash('Test notification sent successfully', 'success')
    return redirect(url_for('notification_preferences'))

@app.route('/reports/schedule', methods=['POST'])
@login_required
def schedule_report():
    """Schedule automated report generation"""
    frequency = request.form.get('frequency', 'daily')
    report_period = request.form.get('report_period', 30, type=int)
    
    if frequency not in ['daily', 'weekly', 'monthly']:
        flash('Invalid frequency selected', 'error')
        return redirect(url_for('view_reports'))
        
    report_scheduler.add_schedule(
        user_id=current_user.id,
        frequency=frequency,
        report_period=report_period
    )
    
    flash('Report schedule created successfully', 'success')
    return redirect(url_for('view_reports'))

@app.route('/reports/schedule/<int:schedule_id>', methods=['PUT'])
@login_required
def update_report_schedule(schedule_id):
    """Update report schedule"""
    schedule = ReportSchedule.query.get_or_404(schedule_id)
    
    if schedule.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    data = request.get_json()
    frequency = data.get('frequency')
    report_period = data.get('report_period')
    active = data.get('active')
    
    success = report_scheduler.update_schedule(
        schedule_id=schedule_id,
        frequency=frequency,
        report_period=report_period,
        active=active
    )
    
    if success:
        return jsonify({'message': 'Schedule updated successfully'})
    return jsonify({'error': 'Failed to update schedule'}), 400

@app.route('/reports/schedule/<int:schedule_id>', methods=['DELETE'])
@login_required
def delete_report_schedule(schedule_id):
    """Delete report schedule"""
    schedule = ReportSchedule.query.get_or_404(schedule_id)
    
    if schedule.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    success = report_scheduler.delete_schedule(schedule_id)
    
    if success:
        return jsonify({'message': 'Schedule deleted successfully'})
    return jsonify({'error': 'Failed to delete schedule'}), 400

@app.route('/reports/schedules', methods=['GET'])
@login_required
def get_report_schedules():
    """Get user's report schedules"""
    schedules = ReportSchedule.query.filter_by(user_id=current_user.id).all()
    
    return jsonify({
        'schedules': [{
            'id': s.id,
            'frequency': s.frequency,
            'report_period': s.report_period,
            'active': s.active,
            'created_at': s.created_at.isoformat(),
            'updated_at': s.updated_at.isoformat()
        } for s in schedules]
    })

@app.route('/export/<format>')
@login_required
def export_data(format):
    """Export health data in various formats"""
    days = request.args.get('days', 30, type=int)
    data_type = request.args.get('type', 'all')  # all, vitals, alerts
    
    exporter = DataExporter(current_user.id)
    
    try:
        if format == 'csv':
            if data_type == 'all':
                return jsonify({'error': 'CSV export requires specifying data type (vitals or alerts)'}), 400
            data, filename = exporter.export_to_csv(data_type, days)
            mimetype = 'text/csv'
        elif format == 'excel':
            data, filename = exporter.export_to_excel(days)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif format == 'json':
            data, filename = exporter.export_to_json(days)
            mimetype = 'application/json'
        else:
            return jsonify({'error': 'Unsupported export format'}), 400
            
        response = make_response(data)
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def simulate_and_analyze():
    """Simulate vital signs and analyze them for the current user"""
    vitals = simulator.generate_vital_signs()
    
    # Save to database
    vital_signs = VitalSigns(
        user_id=current_user.id,
        heart_rate=vitals['heart_rate'],
        blood_pressure_systolic=vitals['blood_pressure']['systolic'],
        blood_pressure_diastolic=vitals['blood_pressure']['diastolic'],
        temperature=vitals['temperature'],
        oxygen_saturation=vitals['oxygen_saturation']
    )
    db.session.add(vital_signs)
    
    # Analyze vitals
    analysis = analyzer.analyze_vital_signs(vitals)
    if analysis['alerts']:
        for alert_data in analysis['alerts']:
            alert = Alert(
                user_id=current_user.id,
                type=alert_data['type'],
                message=alert_data['message'],
                vital_sign=alert_data['vital_sign'],
                value=alert_data['value']
            )
            db.session.add(alert)
    
    db.session.commit()
    
    # Emit to WebSocket
    socketio.emit('vital_signs_update', {
        'vital_signs': vitals,
        'alerts': analysis['alerts']
    })

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        simulate_and_analyze()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
