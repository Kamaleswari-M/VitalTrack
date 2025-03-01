from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    medical_conditions = db.Column(db.Text)
    profile_pic = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vital_signs = db.relationship('VitalSigns', backref='user', lazy=True)
    emergency_contacts = db.relationship('EmergencyContact', backref='user', lazy=True)
    medications = db.relationship('Medication', backref='user', lazy=True)
    alerts = db.relationship('Alert', backref='user', lazy=True)
    notification_preferences = db.relationship('NotificationPreference', backref='user', lazy=True)
    notification_logs = db.relationship('NotificationLog', backref='user', lazy=True)
    report_schedules = db.relationship('ReportSchedule', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

class VitalSigns(db.Model):
    __tablename__ = 'vital_signs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    heart_rate = db.Column(db.Float)
    blood_pressure_systolic = db.Column(db.Float)
    blood_pressure_diastolic = db.Column(db.Float)
    temperature = db.Column(db.Float)
    oxygen_saturation = db.Column(db.Float)
    
    def __repr__(self):
        return f'<VitalSigns {self.timestamp}>'

class EmergencyContact(db.Model):
    __tablename__ = 'emergency_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50))
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    
    def __repr__(self):
        return f'<EmergencyContact {self.name}>'

class Medication(db.Model):
    __tablename__ = 'medications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    instructions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Medication {self.name}>'

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(20), nullable=False)  # 'warning' or 'danger'
    message = db.Column(db.Text, nullable=False)
    vital_sign = db.Column(db.String(50))  # Which vital sign triggered the alert
    value = db.Column(db.Float)  # The value that triggered the alert
    acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Alert {self.timestamp} - {self.type}>'

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email_enabled = db.Column(db.Boolean, default=True)
    sms_enabled = db.Column(db.Boolean, default=True)
    quiet_hours_start = db.Column(db.Time)
    quiet_hours_end = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=False)
    channels = db.Column(db.String(200))  # JSON list of notification channels used
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ReportSchedule(db.Model):
    """Model for scheduled report generation"""
    __tablename__ = 'report_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly
    report_period = db.Column(db.Integer, nullable=False, default=30)  # days
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ReportSchedule {self.id} for User {self.user_id}>'
