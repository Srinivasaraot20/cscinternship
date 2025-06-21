import pandas as pd
import uuid
from datetime import datetime, date
import re
from flask import current_app

def process_excel_file(file_path, session_id):
    """
    Process uploaded Excel file and extract student data
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Expected columns mapping (handle different possible column names)
        column_mapping = {
            'student_name': ['student name', 'student_name', 'name', 'full name'],
            'roll_number': ['roll number', 'roll_number', 'roll no', 'rollno', 'registration number'],
            'branch': ['branch', 'department', 'dept', 'course'],
            'college_name': ['college name', 'college_name', 'college', 'institution'],
            'email': ['email', 'email address', 'mail', 'gmail'],
            'internship_name': ['internship name', 'internship_name', 'internship title', 'program'],
            'start_date': ['start date', 'start_date', 'from date', 'begin date'],
            'end_date': ['end date', 'end_date', 'to date', 'completion date'],
            'mentor_name': ['mentor name', 'mentor_name', 'supervisor', 'guide'],
            'internship_location': ['location', 'internship_location', 'company', 'organization'],
            'performance_grade': ['grade', 'performance_grade', 'score', 'rating'],
            'specialization': ['specialization', 'project', 'area', 'domain']
        }
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Map columns to standard names
        mapped_columns = {}
        for standard_name, possible_names in column_mapping.items():
            for col in df.columns:
                if col in possible_names:
                    mapped_columns[col] = standard_name
                    break
        
        # Rename columns
        df.rename(columns=mapped_columns, inplace=True)
        
        # Validate required columns
        required_columns = ['student_name', 'roll_number', 'branch', 'college_name', 'email', 'internship_name', 'start_date', 'end_date']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Clean and validate data
        students_data = []
        
        for index, row in df.iterrows():
            try:
                # Basic data cleaning
                student_data = {
                    'student_name': clean_text(row['student_name']),
                    'roll_number': clean_text(str(row['roll_number'])),
                    'branch': clean_text(row['branch']),
                    'college_name': clean_text(row['college_name']),
                    'email': validate_email(row['email']),
                    'internship_name': clean_text(row['internship_name']),
                    'start_date': parse_date(row['start_date']),
                    'end_date': parse_date(row['end_date']),
                    'certificate_id': generate_certificate_id(),
                    'issue_date': date.today(),
                    'upload_session_id': session_id,
                    'certificate_status': 'pending'
                }
                
                # Optional fields
                if 'mentor_name' in df.columns and pd.notna(row['mentor_name']):
                    student_data['mentor_name'] = clean_text(row['mentor_name'])
                
                if 'internship_location' in df.columns and pd.notna(row['internship_location']):
                    student_data['internship_location'] = clean_text(row['internship_location'])
                
                if 'performance_grade' in df.columns and pd.notna(row['performance_grade']):
                    student_data['performance_grade'] = clean_text(str(row['performance_grade']))
                
                if 'specialization' in df.columns and pd.notna(row['specialization']):
                    student_data['specialization'] = clean_text(row['specialization'])
                
                # Validate dates
                if student_data['end_date'] <= student_data['start_date']:
                    raise ValueError(f"End date must be after start date for {student_data['student_name']}")
                
                students_data.append(student_data)
                
            except Exception as e:
                current_app.logger.error(f"Error processing row {index + 1}: {str(e)}")
                continue
        
        if not students_data:
            raise ValueError("No valid student records found in the Excel file")
        
        current_app.logger.info(f"Successfully processed {len(students_data)} student records")
        return students_data
        
    except Exception as e:
        current_app.logger.error(f"Error processing Excel file: {str(e)}")
        raise e

def clean_text(text):
    """
    Clean and standardize text data
    """
    if pd.isna(text):
        return ""
    
    # Convert to string and strip whitespace
    text = str(text).strip()
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Title case for names
    if len(text) > 0:
        text = text.title()
    
    return text

def validate_email(email):
    """
    Validate and clean email address
    """
    if pd.isna(email):
        raise ValueError("Email is required")
    
    email = str(email).strip().lower()
    
    # Basic email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValueError(f"Invalid email format: {email}")
    
    return email

def parse_date(date_value):
    """
    Parse various date formats
    """
    if pd.isna(date_value):
        raise ValueError("Date is required")
    
    # If already a date object
    if isinstance(date_value, date):
        return date_value
    
    # If datetime object
    if isinstance(date_value, datetime):
        return date_value.date()
    
    # If string, try to parse
    if isinstance(date_value, str):
        date_value = date_value.strip()
        
        # Common date formats
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_value, date_format).date()
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_value}")
    
    # Try to handle Excel date serial numbers
    try:
        # Excel stores dates as serial numbers
        excel_date = pd.to_datetime(date_value)
        return excel_date.date()
    except:
        raise ValueError(f"Unable to parse date: {date_value}")

def generate_certificate_id():
    """
    Generate unique certificate ID
    """
    # Format: CERT-YYYYMMDD-XXXX (where XXXX is random)
    today = datetime.now()
    date_part = today.strftime('%Y%m%d')
    random_part = str(uuid.uuid4())[:4].upper()
    
    return f"CERT-{date_part}-{random_part}"

def validate_excel_structure(file_path):
    """
    Validate Excel file structure before processing
    """
    try:
        df = pd.read_excel(file_path, nrows=5)  # Read only first 5 rows for validation
        
        # Check if file has data
        if df.empty:
            return False, "Excel file is empty"
        
        # Check minimum required columns
        df.columns = df.columns.str.lower().str.strip()
        
        essential_columns = ['name', 'email', 'date']
        has_essential = any(
            any(essential in col for essential in essential_columns)
            for col in df.columns
        )
        
        if not has_essential:
            return False, "Excel file doesn't contain required columns (name, email, dates)"
        
        return True, "Excel file structure is valid"
        
    except Exception as e:
        return False, f"Error validating Excel file: {str(e)}"

def generate_sample_excel():
    """
    Generate a sample Excel file template
    """
    sample_data = {
        'Student Name': ['John Doe', 'Jane Smith'],
        'Roll Number': ['CS2021001', 'CS2021002'],
        'Branch': ['Computer Science', 'Information Technology'],
        'College Name': ['ABC Engineering College', 'XYZ Institute of Technology'],
        'Email': ['john.doe@email.com', 'jane.smith@email.com'],
        'Internship Name': ['AI Development', 'Web Development'],
        'Start Date': ['2024-01-15', '2024-01-20'],
        'End Date': ['2024-04-15', '2024-04-20'],
        'Mentor Name': ['Dr. Smith', 'Prof. Johnson'],
        'Internship Location': ['Tech Corp', 'Innovation Labs'],
        'Performance Grade': ['A', 'A+'],
        'Specialization': ['Machine Learning', 'Full Stack Development']
    }
    
    df = pd.DataFrame(sample_data)
    return df
