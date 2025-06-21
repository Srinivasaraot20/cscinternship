import os
import uuid
from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file, abort, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc
from flask_wtf.csrf import CSRFProtect

def init_routes(app):
    # Import dependencies inside the function to avoid circular imports
    from app import db
    from models import User, Student, EmailLog, VerificationLog, SystemStats
    from forms import LoginForm, UploadForm, StudentForm
    from utils.excel_processor import process_excel_file
    from utils.pdf_generator import generate_certificate
    from utils.email_utils import send_certificate_email
    from utils.qr_generator import generate_qr_code
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('admin.dashboard'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.password_hash and check_password_hash(user.password_hash, form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page or url_for('admin.dashboard'))
            flash('Invalid username or password', 'error')
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('auth.login'))
    
    # Admin routes
    @app.route('/dashboard')
    @login_required
    def dashboard():
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        
        # Get statistics
        total_students = Student.query.count()
        pending_certs = Student.query.filter_by(certificate_status='pending').count()
        sent_certs = Student.query.filter_by(certificate_status='sent').count()
        failed_certs = Student.query.filter_by(certificate_status='failed').count()
        verified_certs = Student.query.filter(Student.verification_count > 0).count()
        
        # Recent activity
        recent_students = Student.query.order_by(desc(Student.created_at)).limit(10).all()
        recent_verifications = VerificationLog.query.order_by(desc(VerificationLog.verified_at)).limit(10).all()
        
        # Chart data for last 7 days
        chart_data = []
        for i in range(7):
            target_date = date.today() - timedelta(days=i)
            daily_stats = SystemStats.query.filter_by(date=target_date).first()
            if daily_stats:
                chart_data.append({
                    'date': target_date.strftime('%Y-%m-%d'),
                    'generated': daily_stats.certificates_generated,
                    'sent': daily_stats.emails_sent,
                    'verified': daily_stats.verifications_count
                })
            else:
                chart_data.append({
                    'date': target_date.strftime('%Y-%m-%d'),
                    'generated': 0,
                    'sent': 0,
                    'verified': 0
                })
        chart_data.reverse()
        
        stats = {
            'total_students': total_students,
            'pending_certs': pending_certs,
            'sent_certs': sent_certs,
            'failed_certs': failed_certs,
            'verified_certs': verified_certs,
            'success_rate': round((sent_certs / total_students * 100) if total_students > 0 else 0, 1)
        }
        
        return render_template('dashboard.html', 
                             stats=stats, 
                             recent_students=recent_students,
                             recent_verifications=recent_verifications,
                             chart_data=chart_data)
    
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        
        form = UploadForm()
        if form.validate_on_submit():
            file = form.file.data
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                
                try:
                    # Process Excel file
                    session_id = str(uuid.uuid4())
                    students_data = process_excel_file(upload_path, session_id)
                    
                    success_count = 0
                    error_count = 0
                    
                    for student_data in students_data:
                        try:
                            # Create student record
                            student = Student(**student_data)
                            db.session.add(student)
                            db.session.commit()
                            
                            # Generate certificate
                            cert_path = generate_certificate(student)
                            student.certificate_path = cert_path
                            
                            # Generate QR code
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
                            app.logger.error(f"Error processing student {student_data.get('student_name', 'Unknown')}: {str(e)}")
                            error_count += 1
                            db.session.rollback()
                    
                    # Update daily stats
                    today = date.today()
                    stats = SystemStats.query.filter_by(date=today).first()
                    if not stats:
                        stats = SystemStats()
                        stats.date = today
                        db.session.add(stats)
                    
                    stats.certificates_generated += success_count + error_count
                    stats.emails_sent += success_count
                    stats.emails_failed += error_count
                    db.session.commit()
                    
                    flash(f'Processing completed. {success_count} certificates sent successfully, {error_count} failed.', 'info')
                    
                except Exception as e:
                    app.logger.error(f"Error processing file: {str(e)}")
                    flash(f'Error processing file: {str(e)}', 'error')
                finally:
                    # Clean up uploaded file
                    if os.path.exists(upload_path):
                        os.remove(upload_path)
                
                return redirect(url_for('admin.dashboard'))
        
        return render_template('upload.html', form=form)
    
    @app.route('/students')
    @login_required
    def students():
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        
        query = Student.query
        
        if search:
            query = query.filter(
                (Student.student_name.contains(search)) |
                (Student.roll_number.contains(search)) |
                (Student.email.contains(search)) |
                (Student.certificate_id.contains(search))
            )
        
        if status:
            query = query.filter_by(certificate_status=status)
        
        students = query.order_by(desc(Student.created_at)).paginate(
            page=page, per_page=20, error_out=False
        )
        
        return render_template('students.html', students=students, search=search, status=status)
    
    @app.route('/resend/<int:student_id>')
    @login_required
    def resend_certificate(student_id):
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        
        student = Student.query.get_or_404(student_id)
        
        try:
            if send_certificate_email(student):
                student.certificate_status = 'sent'
                student.email_sent_at = datetime.utcnow()
                flash(f'Certificate resent successfully to {student.email}', 'success')
            else:
                student.certificate_status = 'failed'
                flash(f'Failed to resend certificate to {student.email}', 'error')
            
            db.session.commit()
            
        except Exception as e:
            app.logger.error(f"Error resending certificate: {str(e)}")
            flash(f'Error resending certificate: {str(e)}', 'error')
        
        return redirect(url_for('admin.students'))
    
    @app.route('/generate_all_certificates')
    @login_required
    def generate_all_certificates():
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        
        try:
            from utils.pdf_generator import generate_certificate
            from utils.qr_generator import generate_qr_code
            from models import Student
            
            # Get all students without generated certificates
            students_without_certs = Student.query.filter(Student.certificate_path.is_(None)).all()
            
            success_count = 0
            error_count = 0
            
            for student in students_without_certs:
                try:
                    # Generate certificate
                    cert_path = generate_certificate(student)
                    student.certificate_path = cert_path
                    
                    # Generate QR code
                    qr_path = generate_qr_code(student.certificate_id)
                    student.qr_code_path = qr_path
                    
                    student.certificate_status = 'generated'
                    db.session.commit()
                    success_count += 1
                    
                except Exception as e:
                    app.logger.error(f"Error generating certificate for {student.student_name}: {str(e)}")
                    error_count += 1
                    db.session.rollback()
            
            if success_count > 0:
                flash(f'Successfully generated {success_count} certificates. {error_count} failed.', 'success')
            else:
                flash(f'No certificates were generated. {error_count} failed.', 'error')
            
        except Exception as e:
            app.logger.error(f"Error in bulk certificate generation: {str(e)}")
            flash(f'Error generating certificates: {str(e)}', 'error')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/generate_and_send_all')
    @login_required
    def generate_and_send_all():
        """Generate certificates for all students and send emails in one action"""
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        
        try:
            from utils.pdf_generator import generate_certificate
            from utils.qr_generator import generate_qr_code
            from utils.email_utils import send_certificate_email
            from models import Student
            
            # Get all students
            all_students = Student.query.all()
            
            generated_count = 0
            sent_count = 0
            error_count = 0
            
            for student in all_students:
                try:
                    # Generate certificate if not exists
                    if not student.certificate_path:
                        cert_path = generate_certificate(student)
                        student.certificate_path = cert_path
                        generated_count += 1
                    
                    # Generate QR code if not exists
                    if not student.qr_code_path:
                        qr_path = generate_qr_code(student.certificate_id)
                        student.qr_code_path = qr_path
                    
                    # Send email if not already sent
                    if student.certificate_status in ['pending', 'generated', 'failed']:
                        if send_certificate_email(student):
                            student.certificate_status = 'sent'
                            student.email_sent_at = datetime.utcnow()
                            sent_count += 1
                        else:
                            student.certificate_status = 'failed'
                            error_count += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    app.logger.error(f"Error processing student {student.student_name}: {str(e)}")
                    error_count += 1
                    db.session.rollback()
            
            flash(f'Process completed! Generated: {generated_count}, Sent: {sent_count}, Errors: {error_count}', 'success')
            
        except Exception as e:
            app.logger.error(f"Error in bulk operation: {str(e)}")
            flash(f'Error in bulk operation: {str(e)}', 'error')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/retry_failed_emails')
    @login_required
    def retry_failed_emails():
        """Retry sending emails for failed certificates"""
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        
        try:
            from utils.email_utils import send_certificate_email
            from models import Student
            
            # Get all students with failed email status
            failed_students = Student.query.filter_by(certificate_status='failed').all()
            
            if not failed_students:
                flash('No failed emails found to retry.', 'info')
                return redirect(url_for('dashboard'))
            
            success_count = 0
            still_failed = 0
            
            for student in failed_students:
                try:
                    if send_certificate_email(student):
                        student.certificate_status = 'sent'
                        student.email_sent_at = datetime.utcnow()
                        success_count += 1
                    else:
                        still_failed += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    app.logger.error(f"Error retrying email for {student.student_name}: {str(e)}")
                    still_failed += 1
                    db.session.rollback()
            
            flash(f'Retry completed! Success: {success_count}, Still failed: {still_failed}', 'success')
            
        except Exception as e:
            app.logger.error(f"Error retrying failed emails: {str(e)}")
            flash(f'Error retrying failed emails: {str(e)}', 'error')
        
        return redirect(url_for('dashboard'))
    
    @app.route('/send_bulk_emails')
    @login_required
    def send_bulk_emails():
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        
        try:
            from models import Student
            
            # Get all students with generated certificates but not sent
            students_to_send = Student.query.filter(
                Student.certificate_path.isnot(None),
                Student.certificate_status.in_(['pending', 'generated', 'failed'])
            ).all()
            
            if not students_to_send:
                flash('No students found with pending certificates to send.', 'info')
                return redirect(url_for('dashboard'))
            
            from utils.email_utils import send_certificate_email
            success_count = 0
            error_count = 0
            
            for student in students_to_send:
                try:
                    if send_certificate_email(student):
                        student.certificate_status = 'sent'
                        student.email_sent_at = datetime.utcnow()
                        success_count += 1
                    else:
                        student.certificate_status = 'failed'
                        error_count += 1
                    
                    db.session.commit()
                    
                except Exception as e:
                    app.logger.error(f"Error sending email to {student.email}: {str(e)}")
                    error_count += 1
                    db.session.rollback()
            
            flash(f'Bulk email completed. {success_count} emails sent successfully, {error_count} failed.', 'info')
            
        except Exception as e:
            app.logger.error(f"Error in bulk email sending: {str(e)}")
            flash(f'Error sending bulk emails: {str(e)}', 'error')
        
        return redirect(url_for('admin.dashboard'))
    
    @app.route('/download/<certificate_id>')
    def download_certificate(certificate_id):
        student = Student.query.filter_by(certificate_id=certificate_id).first_or_404()
        
        if not student.certificate_path or not os.path.exists(student.certificate_path):
            abort(404)
        
        # Use student name in filename
        safe_name = "".join(c for c in student.student_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_name}_{certificate_id}.pdf"
        
        return send_file(student.certificate_path, as_attachment=True, 
                        download_name=filename)
    
    @app.route('/download_bulk', methods=['POST'])
    @login_required
    def download_bulk_certificates():
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        
        try:
            from models import Student
            import zipfile
            import tempfile
            import shutil
            
            # Get selected certificate IDs from form
            certificate_ids = request.form.getlist('certificate_ids[]')
            if not certificate_ids:
                flash('No certificates selected for download.', 'error')
                return redirect(url_for('admin.students'))
            
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'certificates.zip')
            
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for cert_id in certificate_ids:
                    student = Student.query.filter_by(certificate_id=cert_id).first()
                    if student and student.certificate_path and os.path.exists(student.certificate_path):
                        # Create filename with student name
                        safe_name = "".join(c for c in student.student_name if c.isalnum() or c in (' ', '-', '_')).strip()
                        filename = f"{safe_name}_{cert_id}.pdf"
                        # Add file to zip
                        zipf.write(student.certificate_path, filename)
            
            # Send zip file
            response = send_file(
                zip_path,
                mimetype='application/zip',
                as_attachment=True,
                download_name='certificates.zip'
            )
            
            # Clean up temp directory after sending
            @response.call_on_close
            def cleanup():
                shutil.rmtree(temp_dir)
            
            return response
            
        except Exception as e:
            app.logger.error(f"Error in bulk download: {str(e)}")
            flash(f'Error downloading certificates: {str(e)}', 'error')
            return redirect(url_for('admin.students'))
    
    # Public verification routes
    @app.route('/verify', methods=['GET', 'POST'])
    def verify_certificate():
        from forms import VerificationForm
        form = VerificationForm()
        
        if form.validate_on_submit():
            certificate_id = form.certificate_id.data.strip().upper()
            
            student = Student.query.filter_by(certificate_id=certificate_id).first()
            
            if student:
                # Log verification
                verification_log = VerificationLog(
                    certificate_id=certificate_id,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent', ''),
                    verification_method='manual_entry'
                )
                db.session.add(verification_log)
                
                # Update student verification count
                student.verification_count += 1
                student.last_verified_at = datetime.utcnow()
                
                # Update daily stats
                today = date.today()
                stats = SystemStats.query.filter_by(date=today).first()
                if not stats:
                    stats = SystemStats(date=today, verifications_count=1)
                    db.session.add(stats)
                else:
                    stats.verifications_count = (stats.verifications_count or 0) + 1
                
                db.session.commit()
                
                return render_template('verify.html', student=student, verified=True, form=form)
            else:
                flash('Certificate not found. Please check the Certificate ID.', 'error')
        
        return render_template('verify.html', form=form)
    
    @app.route('/qr/<certificate_id>')
    def qr_verify(certificate_id):
        student = Student.query.filter_by(certificate_id=certificate_id).first_or_404()
        
        # Log QR verification
        verification_log = VerificationLog(
            certificate_id=certificate_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            verification_method='qr_scan'
        )
        db.session.add(verification_log)
        
        # Update student verification count
        student.verification_count += 1
        student.last_verified_at = datetime.utcnow()
        
        # Update daily stats
        today = date.today()
        stats = SystemStats.query.filter_by(date=today).first()
        if not stats:
            stats = SystemStats(date=today, verifications_count=1)
            db.session.add(stats)
        else:
            stats.verifications_count = (stats.verifications_count or 0) + 1
        
        db.session.commit()
        
        return render_template('verify.html', student=student, verified=True, qr_scan=True)
    
    @app.route('/student_portal')
    def student_portal():
        return render_template('student_portal.html')
    
    # API routes for AJAX requests
    @app.route('/api/stats')
    @login_required
    def api_stats():
        if not current_user.is_admin:
            abort(403)
        
        # Get real-time statistics
        total_students = Student.query.count()
        pending_certs = Student.query.filter_by(certificate_status='pending').count()
        sent_certs = Student.query.filter_by(certificate_status='sent').count()
        failed_certs = Student.query.filter_by(certificate_status='failed').count()
        
        return jsonify({
            'total_students': total_students,
            'pending_certs': pending_certs,
            'sent_certs': sent_certs,
            'failed_certs': failed_certs,
            'success_rate': round((sent_certs / total_students * 100) if total_students > 0 else 0, 1)
        })
    
    # Register blueprint-like route groups
    app.add_url_rule('/login', 'auth.login', login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'auth.logout', logout)
    app.add_url_rule('/dashboard', 'admin.dashboard', dashboard)
    app.add_url_rule('/upload', 'admin.upload', upload, methods=['GET', 'POST'])
    app.add_url_rule('/students', 'admin.students', students)
    app.add_url_rule('/resend/<int:student_id>', 'admin.resend', resend_certificate)
    app.add_url_rule('/generate_all_certificates', 'generate_all_certificates', generate_all_certificates)
    app.add_url_rule('/send_bulk_emails', 'send_bulk_emails', send_bulk_emails)
    
    @app.route('/test_single_certificate')
    @login_required
    def test_single_certificate():
        """Test generating a single certificate for the first student"""
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('login'))
        
        try:
            from utils.pdf_generator import generate_certificate
            from utils.qr_generator import generate_qr_code
            from models import Student
            
            # Get the first student
            student = Student.query.first()
            
            if not student:
                flash('No students found. Please upload student data first.', 'error')
                return redirect(url_for('dashboard'))
            
            # Generate certificate
            cert_path = generate_certificate(student)
            student.certificate_path = cert_path
            
            # Generate QR code
            qr_path = generate_qr_code(student.certificate_id)
            student.qr_code_path = qr_path
            
            student.certificate_status = 'generated'
            db.session.commit()
            
            flash(f'Test certificate generated successfully for {student.student_name}!', 'success')
            
        except Exception as e:
            app.logger.error(f"Error generating test certificate: {str(e)}")
            flash(f'Error generating test certificate: {str(e)}', 'error')
            db.session.rollback()
        
        return redirect(url_for('dashboard'))
    
    app.add_url_rule('/test_single_certificate', 'test_single_certificate', test_single_certificate)
