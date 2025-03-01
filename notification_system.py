import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from flask_socketio import SocketIO
from datetime import datetime
import json
from models import db, User, NotificationPreference, NotificationLog
import os
from dotenv import load_dotenv

load_dotenv()

class NotificationSystem:
    def __init__(self, socketio):
        self.socketio = socketio
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Twilio configuration
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
        else:
            self.twilio_client = None
    
    def send_email(self, to_email, subject, body):
        """Send email notification"""
        if not self.smtp_username or not self.smtp_password:
            print("Email credentials not configured")
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
                
            return True
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def send_sms(self, to_phone, message):
        """Send SMS notification"""
        if not self.twilio_client:
            print("Twilio not configured")
            return False
            
        try:
            message = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone_number,
                to=to_phone
            )
            return True
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")
            return False
    
    def send_in_app_notification(self, user_id, notification):
        """Send in-app notification via WebSocket"""
        try:
            self.socketio.emit(
                'notification',
                notification,
                room=str(user_id)
            )
            return True
        except Exception as e:
            print(f"Failed to send in-app notification: {str(e)}")
            return False
    
    def format_notification(self, prediction, severity):
        """Format notification message based on prediction type"""
        if prediction['type'] == 'anomaly':
            return {
                'title': 'Abnormal Vital Signs Detected',
                'message': prediction['message'],
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat(),
                'data': prediction
            }
        elif prediction['type'] == 'trend':
            return {
                'title': 'Vital Signs Trend Alert',
                'message': prediction['message'],
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat(),
                'data': prediction
            }
        return None
    
    def notify_emergency_contacts(self, user_id, notification):
        """Notify user's emergency contacts for critical predictions"""
        user = User.query.get(user_id)
        if not user or not user.emergency_contacts:
            return
            
        message = f"""
        URGENT: Health Alert for {user.full_name}
        
        {notification['title']}
        {notification['message']}
        
        Time: {notification['timestamp']}
        
        Please check the Vital Watch dashboard for more details.
        """
        
        for contact in user.emergency_contacts:
            if contact.email:
                self.send_email(
                    contact.email,
                    f"URGENT: Health Alert for {user.full_name}",
                    message
                )
            
            if contact.phone:
                self.send_sms(contact.phone, message)
    
    def handle_prediction(self, user_id, prediction):
        """Handle a new prediction and send appropriate notifications"""
        # Determine severity
        severity = 'info'
        if prediction['type'] == 'anomaly':
            severity = 'warning'
            if 'heart_rate' in prediction['message'] or 'oxygen_saturation' in prediction['message']:
                severity = 'critical'
        elif prediction['type'] == 'trend' and 'decrease' in prediction['message']:
            severity = 'warning'
        
        # Format notification
        notification = self.format_notification(prediction, severity)
        if not notification:
            return
        
        # Get user's notification preferences
        user = User.query.get(user_id)
        if not user:
            return
            
        prefs = NotificationPreference.query.filter_by(user_id=user_id).first()
        if not prefs:
            prefs = NotificationPreference(user_id=user_id)
            db.session.add(prefs)
            db.session.commit()
        
        # Send notifications based on preferences and severity
        notifications_sent = []
        
        # Always send in-app notifications
        if self.send_in_app_notification(user_id, notification):
            notifications_sent.append('in_app')
        
        # For warning and critical severity, send additional notifications
        if severity in ['warning', 'critical']:
            if prefs.email_enabled and user.email:
                if self.send_email(
                    user.email,
                    notification['title'],
                    notification['message']
                ):
                    notifications_sent.append('email')
            
            if prefs.sms_enabled and user.phone:
                if self.send_sms(
                    user.phone,
                    f"{notification['title']}\n{notification['message']}"
                ):
                    notifications_sent.append('sms')
        
        # For critical severity, notify emergency contacts
        if severity == 'critical':
            self.notify_emergency_contacts(user_id, notification)
            notifications_sent.append('emergency_contacts')
        
        # Log the notification
        log = NotificationLog(
            user_id=user_id,
            type=prediction['type'],
            severity=severity,
            message=notification['message'],
            channels=json.dumps(notifications_sent),
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
