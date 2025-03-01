from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import os
from models import User, ReportSchedule, db
from analytics.report_generator import HealthReport
from notification_system import NotificationSystem

class ReportScheduler:
    def __init__(self, socketio=None):
        self.scheduler = BackgroundScheduler()
        self.notification_system = NotificationSystem(socketio) if socketio else None
        
    def start(self):
        """Start the scheduler"""
        # Schedule daily reports at midnight
        self.scheduler.add_job(
            self.generate_scheduled_reports,
            CronTrigger(hour=0, minute=0),
            id='daily_reports'
        )
        
        # Schedule weekly reports on Monday at midnight
        self.scheduler.add_job(
            self.generate_scheduled_reports,
            CronTrigger(day_of_week='mon', hour=0, minute=0),
            id='weekly_reports'
        )
        
        # Schedule monthly reports on the 1st at midnight
        self.scheduler.add_job(
            self.generate_scheduled_reports,
            CronTrigger(day=1, hour=0, minute=0),
            id='monthly_reports'
        )
        
        self.scheduler.start()
        
    def generate_scheduled_reports(self):
        """Generate reports for all scheduled users"""
    
        current_time = datetime.utcnow()
        
        # Get all active report schedules
        schedules = ReportSchedule.query.filter_by(active=True).all()
        
        for schedule in schedules:
            try:
                # Generate report
                report_generator = HealthReport(schedule.user_id)
                pdf_data = report_generator.generate_pdf_report(
                    days=schedule.report_period
                )
                
                if pdf_data:
                    # Save report
                    filename = f'report_{schedule.user_id}_{current_time.strftime("%Y%m%d")}.pdf'
                    filepath = os.path.join('reports', filename)
                    os.makedirs('reports', exist_ok=True)
                    
                    with open(filepath, 'wb') as f:
                        f.write(pdf_data)
                    
                    # Send notification if notification system is available
                    if self.notification_system:
                        user = User.query.get(schedule.user_id)
                        self.notification_system.send_notification(
                            user_id=schedule.user_id,
                            title='Health Report Generated',
                            message=f'Your {schedule.frequency} health report is ready.',
                            notification_type='report',
                            data={'report_path': filepath}
                        )
                    
            except Exception as e:
                print(f"Error generating report for user {schedule.user_id}: {str(e)}")
                
    def add_schedule(self, user_id, frequency='daily', report_period=30):
        """Add a new report schedule"""
        schedule = ReportSchedule(
            user_id=user_id,
            frequency=frequency,
            report_period=report_period,
            active=True
        )
        db.session.add(schedule)
        db.session.commit()
        
    def update_schedule(self, schedule_id, frequency=None, report_period=None, active=None):
        """Update an existing schedule"""
        schedule = ReportSchedule.query.get(schedule_id)
        if not schedule:
            return False
            
        if frequency:
            schedule.frequency = frequency
        if report_period is not None:
            schedule.report_period = report_period
        if active is not None:
            schedule.active = active
            
        db.session.commit()
        return True
        
    def delete_schedule(self, schedule_id):
        """Delete a schedule"""
        schedule = ReportSchedule.query.get(schedule_id)
        if schedule:
            db.session.delete(schedule)
            db.session.commit()
            return True
        return False
