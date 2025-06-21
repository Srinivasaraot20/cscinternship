from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import func

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    college_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    internship_name = db.Column(db.String(200), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    certificate_id = db.Column(db.String(20), unique=True, nullable=False)
    issue_date = db.Column(db.Date, default=datetime.utcnow().date)
    mentor_name = db.Column(db.String(100))
    internship_location = db.Column(db.String(200))
    performance_grade = db.Column(db.String(10))
    specialization = db.Column(db.String(100))
    certificate_status = db.Column(db.String(20), default='pending')  # pending, sent, failed, verified
    email_sent_at = db.Column(db.DateTime)
    verification_count = db.Column(db.Integer, default=0)
    last_verified_at = db.Column(db.DateTime)
    qr_code_path = db.Column(db.String(200))
    certificate_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Batch information
    batch_id = db.Column(db.String(50))
    upload_session_id = db.Column(db.String(50))
    
    def __repr__(self):
        return f'<Student {self.student_name} - {self.certificate_id}>'
    
    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days
    
    @property
    def duration_weeks(self):
        return self.duration_days // 7

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    email_to = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # sent, failed, pending
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    retry_count = db.Column(db.Integer, default=0)
    
    student = db.relationship('Student', backref=db.backref('email_logs', lazy=True))
    
    def __repr__(self):
        return f'<EmailLog {self.email_to} - {self.status}>'

class VerificationLog(db.Model):
    __tablename__ = 'verification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    certificate_id = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    verified_at = db.Column(db.DateTime, default=datetime.utcnow)
    verification_method = db.Column(db.String(20))  # qr_scan, manual_entry
    
    def __repr__(self):
        return f'<VerificationLog {self.certificate_id} - {self.verified_at}>'

class SystemStats(db.Model):
    __tablename__ = 'system_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    certificates_generated = db.Column(db.Integer, default=0)
    emails_sent = db.Column(db.Integer, default=0)
    emails_failed = db.Column(db.Integer, default=0)
    verifications_count = db.Column(db.Integer, default=0)
    storage_used_mb = db.Column(db.Float, default=0.0)
    
    def __repr__(self):
        return f'<SystemStats {self.date}>'
