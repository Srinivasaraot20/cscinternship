import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime, date
from flask import current_app

def send_certificate_email(student):
    """
    Send certificate email to student
    """
    try:
        # Email configuration (you should set these in environment variables)
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        email_user = os.getenv('EMAIL_USER', 'srinurao1902@gmail.com')
        email_password = os.getenv('EMAIL_PASSWORD', 'hbpb dopw jlmx twjx')

        # Create message
        msg = MIMEMultipart()
        msg['From'] = email_user
        msg['To'] = student.email
        msg['Subject'] = f"Certificate of Completion - {student.internship_name}"

        # Email body
        body = f"""
Dear {student.student_name},

Congratulations! You have successfully completed the internship program.

Program Details:
- Internship: {student.internship_name}
- Duration: {student.start_date.strftime('%d/%m/%Y')} to {student.end_date.strftime('%d/%m/%Y')}
- Certificate ID: {student.certificate_id}

Please find your certificate attached to this email.

You can also verify your certificate online using the Certificate ID.

Best regards,
Certificate Management Team
        """

        msg.attach(MIMEText(body, 'plain'))

        # Attach certificate if it exists
        if student.certificate_path and os.path.exists(student.certificate_path):
            with open(student.certificate_path, 'rb') as attachment:
                part = MIMEApplication(attachment.read(), _subtype='pdf')
                part.add_header('Content-Disposition', 'attachment', 
                              filename=f'certificate_{student.certificate_id}.pdf')
                msg.attach(part)

        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_password)
        text = msg.as_string()
        server.sendmail(email_user, student.email, text)
        server.quit()

        # Log email success
        from models import EmailLog
        from app import db

        email_log = EmailLog(
            student_id=student.id,
            email_to=student.email,
            subject=msg['Subject'],
            status='sent'
        )
        db.session.add(email_log)
        db.session.commit()

        return True

    except Exception as e:
        current_app.logger.error(f"Error sending email to {student.email}: {str(e)}")

        # Log email failure
        try:
            from models import EmailLog
            from app import db

            email_log = EmailLog(
                student_id=student.id,
                email_to=student.email,
                subject=f"Certificate of Completion - {student.internship_name}",
                status='failed',
                error_message=str(e)
            )
            db.session.add(email_log)
            db.session.commit()
        except:
            pass

        return False

def send_bulk_emails(students, template_type='certificate'):
    """
    Send bulk emails to multiple students
    """
    from app import db

    success_count = 0
    failed_count = 0

    for student in students:
        try:
            if send_certificate_email(student):
                success_count += 1
                student.certificate_status = 'sent'
                student.email_sent_at = datetime.utcnow()
            else:
                failed_count += 1
                student.certificate_status = 'failed'

            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Error in bulk email for student {student.id}: {str(e)}")
            failed_count += 1
            db.session.rollback()

    return success_count, failed_count

def retry_failed_emails():
    """
    Retry sending emails for failed certificates
    """
    from models import Student
    from app import db

    failed_students = Student.query.filter_by(certificate_status='failed').all()

    success_count = 0
    still_failed = 0

    for student in failed_students:
        try:
            if send_certificate_email(student):
                success_count += 1
                student.certificate_status = 'sent'
                student.email_sent_at = datetime.utcnow()
            else:
                still_failed += 1

            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Error retrying email for {student.student_name}: {str(e)}")
            still_failed += 1
            db.session.rollback()

    return success_count, still_failed

def send_all_certificates():
    """
    Generate certificates and send emails for all pending students
    """
    from utils.pdf_generator import generate_certificate
    from utils.qr_generator import generate_qr_code
    from datetime import datetime, date
    from models import SystemStats, Student
    from app import db

    # Get all students who need certificates
    pending_students = Student.query.filter(Student.certificate_path.is_(None)).all()

    success_count = 0
    error_count = 0

    for student in pending_students:
        try:
            # Generate certificate if not exists
            if not student.certificate_path:
                cert_path = generate_certificate(student)
                student.certificate_path = cert_path

                # Generate QR code if not exists
                if not student.qr_code_path:
                    qr_path = generate_qr_code(student.certificate_id)
                    student.qr_code_path = qr_path

            # Send email
            if send_certificate_email(student):
                student.certificate_status = 'sent'
                student.email_sent_at = datetime.utcnow()
                success_count += 1
            else:
                student.certificate_status = 'failed'
                error_count += 1

            db.session.commit()

        except Exception as e:
            current_app.logger.error(f"Error processing student {student.student_name}: {str(e)}")
            student.certificate_status = 'failed'
            error_count += 1
            db.session.rollback()

    # Update daily stats
    today = date.today()
    stats = SystemStats.query.filter_by(date=today).first()
    if not stats:
        stats = SystemStats()
        stats.date = today
        db.session.add(stats)

    stats.certificates_generated = (stats.certificates_generated or 0) + success_count + error_count
    stats.emails_sent = (stats.emails_sent or 0) + success_count
    stats.emails_failed = (stats.emails_failed or 0) + error_count
    db.session.commit()

    return success_count, error_count