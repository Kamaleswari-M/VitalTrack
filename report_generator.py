from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import io
import base64
from fpdf import FPDF
import pandas as pd
import numpy as np
from models import VitalSigns, Alert, Medication

class HealthReport:
    def __init__(self, user):
        self.user = user
        
    def generate_vital_signs_plot(self, days=7):
        """Generate plots for vital signs trends"""
        since = datetime.utcnow() - timedelta(days=days)
        vital_signs = VitalSigns.query.filter(
            VitalSigns.user_id == self.user.id,
            VitalSigns.timestamp >= since
        ).order_by(VitalSigns.timestamp.asc()).all()
        
        if not vital_signs:
            return None
            
        timestamps = [vs.timestamp for vs in vital_signs]
        heart_rates = [vs.heart_rate for vs in vital_signs]
        temperatures = [vs.temperature for vs in vital_signs]
        spo2_levels = [vs.oxygen_saturation for vs in vital_signs]
        systolic = [vs.blood_pressure_systolic for vs in vital_signs]
        diastolic = [vs.blood_pressure_diastolic for vs in vital_signs]
        
        # Create subplots
        fig, axes = plt.subplots(4, 1, figsize=(12, 16))
        fig.suptitle('Vital Signs Trends', fontsize=16)
        
        # Heart Rate
        axes[0].plot(timestamps, heart_rates, 'b-')
        axes[0].set_title('Heart Rate')
        axes[0].set_ylabel('BPM')
        axes[0].grid(True)
        
        # Blood Pressure
        axes[1].plot(timestamps, systolic, 'r-', label='Systolic')
        axes[1].plot(timestamps, diastolic, 'b-', label='Diastolic')
        axes[1].set_title('Blood Pressure')
        axes[1].set_ylabel('mmHg')
        axes[1].legend()
        axes[1].grid(True)
        
        # Temperature
        axes[2].plot(timestamps, temperatures, 'g-')
        axes[2].set_title('Body Temperature')
        axes[2].set_ylabel('°C')
        axes[2].grid(True)
        
        # SpO2
        axes[3].plot(timestamps, spo2_levels, 'm-')
        axes[3].set_title('Oxygen Saturation (SpO2)')
        axes[3].set_ylabel('%')
        axes[3].grid(True)
        
        plt.tight_layout()
        
        # Convert plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode()
        
    def generate_alert_summary(self, days=7):
        """Generate summary of alerts"""
        since = datetime.utcnow() - timedelta(days=days)
        alerts = Alert.query.filter(
            Alert.user_id == self.user.id,
            Alert.timestamp >= since
        ).order_by(Alert.timestamp.desc()).all()
        
        alert_summary = {
            'total': len(alerts),
            'warning': len([a for a in alerts if a.type == 'warning']),
            'danger': len([a for a in alerts if a.type == 'danger']),
            'recent_alerts': alerts[:5]  # Last 5 alerts
        }
        
        return alert_summary
        
    def generate_medication_summary(self):
        """Generate summary of current medications"""
        current_date = datetime.utcnow().date()
        medications = Medication.query.filter(
            Medication.user_id == self.user.id,
            Medication.start_date <= current_date,
            (Medication.end_date.is_(None) | (Medication.end_date >= current_date))
        ).all()
        
        return medications
        
    def generate_pdf_report(self, days=7):
        """Generate a complete PDF health report"""
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Health Report', 0, 1, 'C')
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Generated on: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        pdf.cell(0, 10, f'Patient: {self.user.first_name} {self.user.last_name}', 0, 1, 'C')
        pdf.ln(10)
        
        # Vital Signs Trends
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Vital Signs Trends', 0, 1, 'L')
        vital_signs_plot = self.generate_vital_signs_plot(days)
        if vital_signs_plot:
            pdf.image(io.BytesIO(base64.b64decode(vital_signs_plot)), x=10, w=190)
        
        # Alert Summary
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Alert Summary', 0, 1, 'L')
        alert_summary = self.generate_alert_summary(days)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Total Alerts: {alert_summary["total"]}', 0, 1, 'L')
        pdf.cell(0, 10, f'Warning Alerts: {alert_summary["warning"]}', 0, 1, 'L')
        pdf.cell(0, 10, f'Danger Alerts: {alert_summary["danger"]}', 0, 1, 'L')
        
        if alert_summary['recent_alerts']:
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Recent Alerts:', 0, 1, 'L')
            pdf.set_font('Arial', '', 12)
            for alert in alert_summary['recent_alerts']:
                pdf.multi_cell(0, 10, 
                    f'- {alert.timestamp.strftime("%Y-%m-%d %H:%M")}: {alert.message}')
        
        # Medication Summary
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Current Medications', 0, 1, 'L')
        medications = self.generate_medication_summary()
        
        if medications:
            for med in medications:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, med.name, 0, 1, 'L')
                pdf.set_font('Arial', '', 12)
                pdf.cell(0, 10, f'Dosage: {med.dosage}', 0, 1, 'L')
                pdf.cell(0, 10, f'Frequency: {med.frequency}', 0, 1, 'L')
                if med.instructions:
                    pdf.multi_cell(0, 10, f'Instructions: {med.instructions}')
                pdf.ln(5)
        else:
            pdf.cell(0, 10, 'No current medications', 0, 1, 'L')
        
        # Save PDF to memory
        pdf_output = io.BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        
        return pdf_output.getvalue()
