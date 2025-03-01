from datetime import datetime
from models import db, Alert, EmergencyContact, VitalSigns, NotificationLog
import requests

class EmergencyHandler:
    def __init__(self):
        self.twilio_enabled = False  # Set to True when Twilio is configured
        
    def handle_emergency(self, user, message=None):
        """Handle emergency situation"""
        try:
            # Get user's emergency contacts
            contacts = EmergencyContact.query.filter_by(user_id=user.id).all()
            
            # Get latest vital signs
            vitals = VitalSigns.query.filter_by(user_id=user.id)\
                .order_by(VitalSigns.timestamp.desc())\
                .first()
            
            # Create emergency message
            emergency_msg = self._create_emergency_message(user, vitals, message)
            
            # Create alert
            alert = Alert(
                user_id=user.id,
                type='EMERGENCY',
                message=emergency_msg,
                severity='HIGH'
            )
            db.session.add(alert)
            
            # Send notifications to all emergency contacts
            for contact in contacts:
                self._notify_contact(contact, emergency_msg)
                
                # Log notification
                log = NotificationLog(
                    user_id=user.id,
                    type='EMERGENCY',
                    severity='HIGH',
                    message=f'Emergency alert sent to {contact.name}',
                    channels='sms,email'
                )
                db.session.add(log)
            
            db.session.commit()
            return True, "Emergency contacts have been notified"
            
        except Exception as e:
            db.session.rollback()
            return False, str(e)
    
    def _create_emergency_message(self, user, vitals, custom_msg=None):
        """Create emergency message with vital signs"""
        msg = f"EMERGENCY ALERT for {user.first_name} {user.last_name}\n"
        
        if custom_msg:
            msg += f"Message: {custom_msg}\n"
        
        if vitals:
            msg += "\nVital Signs:\n"
            msg += f"Heart Rate: {vitals.heart_rate} bpm\n"
            msg += f"Blood Pressure: {vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic} mmHg\n"
            msg += f"Temperature: {vitals.temperature}°C\n"
            msg += f"Oxygen Saturation: {vitals.oxygen_saturation}%\n"
        
        msg += f"\nLocation: [Location will be added here]\n"
        msg += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        msg += "\nPlease respond immediately!"
        
        return msg
    
    def _notify_contact(self, contact, message):
        """Send notifications to emergency contact"""
        # Send SMS if Twilio is configured
        if self.twilio_enabled:
            self._send_sms(contact.phone, message)
        
        # For now, we'll just print the message
        print(f"Emergency notification to {contact.name}:")
        print(f"Phone: {contact.phone}")
        print(f"Email: {contact.email}")
        print(f"Message: {message}")
        print("-" * 50)
    
    def _send_sms(self, phone_number, message):
        """Send SMS using Twilio (placeholder for now)"""
        # This will be implemented when Twilio is configured
        pass
