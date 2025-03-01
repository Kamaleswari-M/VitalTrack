import os
from datetime import datetime
from models import Medication, NotificationLog, db
from flask import flash

class MedicationReminder:
    def __init__(self):
        """Initialize medication reminder system"""
        pass
        
    def check_medications(self, user):
        """Check if any medications are due and send reminders"""
        current_time = datetime.now()
        current_date = current_time.date()
        
        # Get medications that are currently active (started and not ended)
        medications = Medication.query.filter(
            Medication.user_id == user.id,
            Medication.start_date <= current_date,
            (Medication.end_date.is_(None) | (Medication.end_date >= current_date))
        ).all()
        
        reminders_sent = []
        for med in medications:
            if self._should_take_medication(med, current_time):
                reminder_msg = f"Time to take {med.name} - {med.dosage}"
                
                # Create notification log
                log = NotificationLog(
                    user_id=user.id,
                    type='MEDICATION_REMINDER',
                    severity='MEDIUM',
                    message=reminder_msg,
                    channels='APP_NOTIFICATION'
                )
                db.session.add(log)
                
                # Add flash message
                flash(reminder_msg, 'info')
                reminders_sent.append(reminder_msg)
        
        if reminders_sent:
            db.session.commit()
            
        return reminders_sent
        
    def _should_take_medication(self, medication, current_time):
        """Determine if medication should be taken based on frequency"""
        # Define medication schedules (hours of the day)
        schedules = {
            'once_daily': [9],  # 9 AM
            'twice_daily': [9, 21],  # 9 AM and 9 PM
            'three_times_daily': [9, 14, 21],  # 9 AM, 2 PM, and 9 PM
            'four_times_daily': [8, 12, 16, 20],  # 8 AM, 12 PM, 4 PM, and 8 PM
            'weekly': [9],  # Once a week at 9 AM
            'monthly': [9]  # Once a month at 9 AM
        }
        
        frequency = medication.frequency.lower().replace(' ', '_')
        if frequency in schedules:
            return current_time.hour in schedules[frequency]
            
        return False
