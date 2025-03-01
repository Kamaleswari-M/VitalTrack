# VitalTrack - Health Monitoring System

VitalTrack is a comprehensive health monitoring system designed for patients recovering from surgery. It provides real-time vital signs monitoring, emergency alerts, medication reminders, and health prediction capabilities.

## Features

- Real-time vital signs monitoring (heart rate, SpO2, temperature)
- Emergency SOS button with instant contact notification
- Medication reminder system
- Health anomaly detection and prediction
- User-friendly dashboard
- Mobile-responsive design

## Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Database**: SQLite
- **Real-time Updates**: Flask-SocketIO
- **Authentication**: Flask-Login
- **Scheduling**: APScheduler
- **SMS Notifications**: Twilio
- **Email Notifications**: SMTP

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Twilio account for SMS notifications
- An email account for sending email notifications

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/vitaltrack.git
   cd vitaltrack
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add your configuration:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=sqlite:///vital_signs.db
   SECRET_KEY=your-secret-key-here
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   TWILIO_PHONE_NUMBER=your-twilio-phone
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-specific-password
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

## Running the Application

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

1. **Registration**: Create an account with your personal information
2. **Add Emergency Contacts**: Add contact details for emergency notifications
3. **Set Up Medications**: Add your medications and reminder schedules
4. **Monitor Vital Signs**: Connect your monitoring device and view real-time updates
5. **Emergency SOS**: Use the SOS button in case of emergencies

## Development

- The application uses Flask's built-in development server
- Debug mode is enabled by default in development
- SQLite database is used for development
- Real-time updates are handled through WebSocket connections

## Production Deployment

For production deployment:

1. Use a production-grade WSGI server (e.g., Gunicorn)
2. Set up a proper database (e.g., PostgreSQL)
3. Configure proper logging
4. Set up SSL/TLS for secure communications
5. Use environment variables for sensitive information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@vitaltrack.com or create an issue in the GitHub repository.
