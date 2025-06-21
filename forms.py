from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UploadForm(FlaskForm):
    file = FileField('Excel File', validators=[
        FileRequired(),
        FileAllowed(['xlsx', 'xls'], 'Only Excel files are allowed!')
    ])
    submit = SubmitField('Upload and Process')

class StudentForm(FlaskForm):
    student_name = StringField('Student Name', validators=[DataRequired(), Length(max=100)])
    roll_number = StringField('Roll Number', validators=[DataRequired(), Length(max=50)])
    branch = StringField('Branch', validators=[DataRequired(), Length(max=50)])
    college_name = StringField('College Name', validators=[DataRequired(), Length(max=200)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    internship_name = StringField('Internship Name', validators=[DataRequired(), Length(max=200)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    mentor_name = StringField('Mentor Name', validators=[Length(max=100)])
    internship_location = StringField('Internship Location', validators=[Length(max=200)])
    performance_grade = SelectField('Performance Grade', choices=[
        ('', 'Select Grade'),
        ('A+', 'A+'),
        ('A', 'A'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('C+', 'C+'),
        ('C', 'C')
    ])
    specialization = StringField('Specialization/Project', validators=[Length(max=100)])
    submit = SubmitField('Save Student')
    
    def validate_end_date(self, field):
        if field.data and self.start_date.data:
            if field.data <= self.start_date.data:
                raise ValidationError('End date must be after start date.')

class VerificationForm(FlaskForm):
    certificate_id = StringField('Certificate ID', validators=[DataRequired(), Length(min=5, max=20)])
    submit = SubmitField('Verify Certificate')
