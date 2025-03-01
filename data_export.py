import pandas as pd
from datetime import datetime, timedelta
import json
from io import BytesIO
from models import VitalSigns, Alert, User

class DataExporter:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def get_vital_signs_data(self, days=30):
        """Get vital signs data for the specified period"""
        since = datetime.utcnow() - timedelta(days=days)
        
        vitals = VitalSigns.query.filter(
            VitalSigns.user_id == self.user_id,
            VitalSigns.timestamp >= since
        ).order_by(VitalSigns.timestamp.asc()).all()
        
        data = [{
            'timestamp': v.timestamp,
            'heart_rate': v.heart_rate,
            'blood_pressure_systolic': v.blood_pressure_systolic,
            'blood_pressure_diastolic': v.blood_pressure_diastolic,
            'temperature': v.temperature,
            'oxygen_saturation': v.oxygen_saturation
        } for v in vitals]
        
        return data
        
    def get_alerts_data(self, days=30):
        """Get alerts data for the specified period"""
        since = datetime.utcnow() - timedelta(days=days)
        
        alerts = Alert.query.filter(
            Alert.user_id == self.user_id,
            Alert.timestamp >= since
        ).order_by(Alert.timestamp.desc()).all()
        
        data = [{
            'timestamp': a.timestamp,
            'type': a.type,
            'message': a.message,
            'vital_sign': a.vital_sign,
            'value': a.value,
            'acknowledged': a.acknowledged,
            'acknowledged_at': a.acknowledged_at
        } for a in alerts]
        
        return data
        
    def export_to_csv(self, data_type='vitals', days=30):
        """Export data to CSV format"""
        if data_type == 'vitals':
            data = self.get_vital_signs_data(days)
            filename = f'vital_signs_{datetime.now().strftime("%Y%m%d")}.csv'
        else:
            data = self.get_alerts_data(days)
            filename = f'alerts_{datetime.now().strftime("%Y%m%d")}.csv'
            
        df = pd.DataFrame(data)
        
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return output.getvalue(), filename
        
    def export_to_excel(self, days=30):
        """Export all data to Excel with multiple sheets"""
        vitals_data = self.get_vital_signs_data(days)
        alerts_data = self.get_alerts_data(days)
        
        # Create Excel writer
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Vital Signs sheet
            vitals_df = pd.DataFrame(vitals_data)
            vitals_df.to_excel(writer, sheet_name='Vital Signs', index=False)
            
            # Alerts sheet
            alerts_df = pd.DataFrame(alerts_data)
            alerts_df.to_excel(writer, sheet_name='Alerts', index=False)
            
            # Get workbook and add formats
            workbook = writer.book
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#D9EAD3',
                'border': 1
            })
            
            # Format Vital Signs sheet
            worksheet = writer.sheets['Vital Signs']
            for col_num, value in enumerate(vitals_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
                
            # Format Alerts sheet
            worksheet = writer.sheets['Alerts']
            for col_num, value in enumerate(alerts_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                worksheet.set_column(col_num, col_num, 15)
        
        filename = f'health_data_{datetime.now().strftime("%Y%m%d")}.xlsx'
        return output.getvalue(), filename
        
    def export_to_json(self, days=30):
        """Export all data to JSON format"""
        data = {
            'vital_signs': self.get_vital_signs_data(days),
            'alerts': self.get_alerts_data(days),
            'metadata': {
                'user_id': self.user_id,
                'export_date': datetime.now().isoformat(),
                'period_days': days
            }
        }
        
        output = BytesIO()
        json.dump(data, output, default=str, indent=2)
        output.seek(0)
        
        filename = f'health_data_{datetime.now().strftime("%Y%m%d")}.json'
        return output.getvalue(), filename
