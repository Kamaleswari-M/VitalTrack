import datetime
from dataclasses import dataclass
from typing import List, Dict
import json
import time
from threading import Thread
import numpy as np

@dataclass
class MedicationReminder:
    name: str
    time: datetime.time
    dosage: str
    description: str

@dataclass
class EmergencyContact:
    name: str
    phone: str
    relationship: str

class VitalManager:
    def __init__(self):
        self.emergency_contacts: List[EmergencyContact] = []
        self.medication_schedule: List[MedicationReminder] = []
        self.alert_history: List[Dict] = []
        self.is_monitoring = False
        
    def add_emergency_contact(self, name: str, phone: str, relationship: str):
        """Add an emergency contact"""
        contact = EmergencyContact(name=name, phone=phone, relationship=relationship)
        self.emergency_contacts.append(contact)
        
    def add_medication_reminder(self, name: str, time_str: str, dosage: str, description: str):
        """Add a medication reminder"""
        time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()
        reminder = MedicationReminder(
            name=name,
            time=time_obj,
            dosage=dosage,
            description=description
        )
        self.medication_schedule.append(reminder)
        
    def trigger_sos(self) -> bool:
        """
        Simulate sending SOS messages to emergency contacts
        In real hardware, this would connect to GSM module
        """
        if not self.emergency_contacts:
            return False
            
        message = "EMERGENCY ALERT: Your contact needs immediate assistance!"
        
        # In real implementation, this would use a GSM module to send SMS
        for contact in self.emergency_contacts:
            print(f"Sending SOS to {contact.name} at {contact.phone}: {message}")
            
        self.alert_history.append({
            'type': 'SOS',
            'timestamp': datetime.datetime.now(),
            'status': 'sent'
        })
        return True
        
    def check_medication_reminders(self) -> List[MedicationReminder]:
        """Check for due medication reminders"""
        current_time = datetime.datetime.now().time()
        due_reminders = []
        
        for reminder in self.medication_schedule:
            time_diff = datetime.datetime.combine(datetime.date.today(), current_time) - \
                       datetime.datetime.combine(datetime.date.today(), reminder.time)
            
            # If within 5 minutes of scheduled time
            if abs(time_diff.total_seconds()) <= 300:  # 5 minutes
                due_reminders.append(reminder)
                
        return due_reminders
        
    def start_monitoring(self):
        """Start the monitoring thread"""
        self.is_monitoring = True
        self.monitor_thread = Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.is_monitoring = False
        
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            # Check medication reminders
            due_reminders = self.check_medication_reminders()
            for reminder in due_reminders:
                print(f"MEDICATION REMINDER: Time to take {reminder.name} - {reminder.dosage}")
                # In real hardware, this would trigger a buzzer/alarm
                
            time.sleep(60)  # Check every minute

# Example usage
if __name__ == "__main__":
    manager = VitalManager()
    
    # Add emergency contacts
    manager.add_emergency_contact("John Doe", "+1234567890", "Family")
    manager.add_emergency_contact("Jane Smith", "+0987654321", "Doctor")
    
    # Add medication reminders
    manager.add_medication_reminder(
        name="Blood Pressure Medicine",
        time_str="09:00",
        dosage="1 tablet",
        description="Take with water after breakfast"
    )
    
    # Test SOS
    print("\nTesting SOS Feature:")
    manager.trigger_sos()
    
    # Start monitoring
    print("\nStarting Medication Monitoring:")
    manager.start_monitoring()
    
    # Let it run for a few seconds
    time.sleep(5)
    manager.stop_monitoring()
