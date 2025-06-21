#!/usr/bin/env python3
"""
Create a sample Excel file with student data for certificate generation
"""

import pandas as pd
from datetime import datetime, date, timedelta
import random

# Sample data for students
students_data = [
    {
        'student name': 'John Smith',
        'roll number': 'CS2021001',
        'branch': 'Computer Science',
        'college name': 'Tech University',
        'email': 'john.smith@techuni.edu',
        'internship name': 'Full Stack Web Development',
        'start date': '2024-06-01',
        'end date': '2024-08-31',
        'mentor name': 'Dr. Sarah Johnson',
        'location': 'San Francisco, CA',
        'grade': 'A+',
        'specialization': 'React.js & Node.js Development'
    },
    {
        'student name': 'Emma Wilson',
        'roll number': 'EC2021002',
        'branch': 'Electronics & Communication',
        'college name': 'Engineering Institute',
        'email': 'emma.wilson@enginst.edu',
        'internship name': 'IoT Systems Development',
        'start date': '2024-06-15',
        'end date': '2024-08-15',
        'mentor name': 'Prof. Michael Chen',
        'location': 'Austin, TX',
        'grade': 'A',
        'specialization': 'Sensor Networks & Embedded Systems'
    },
    {
        'student name': 'David Rodriguez',
        'roll number': 'ME2021003',
        'branch': 'Mechanical Engineering',
        'college name': 'State Technical College',
        'email': 'david.rodriguez@stc.edu',
        'internship name': 'Automotive Design Internship',
        'start date': '2024-05-20',
        'end date': '2024-08-20',
        'mentor name': 'Dr. Lisa Thompson',
        'location': 'Detroit, MI',
        'grade': 'B+',
        'specialization': 'CAD Design & Manufacturing'
    },
    {
        'student name': 'Priya Sharma',
        'roll number': 'IT2021004',
        'branch': 'Information Technology',
        'college name': 'Global Tech University',
        'email': 'priya.sharma@gtu.edu',
        'internship name': 'Data Science & Analytics',
        'start date': '2024-06-10',
        'end date': '2024-09-10',
        'mentor name': 'Dr. Robert Kim',
        'location': 'Seattle, WA',
        'grade': 'A+',
        'specialization': 'Machine Learning & Data Visualization'
    },
    {
        'student name': 'Alex Turner',
        'roll number': 'CS2021005',
        'branch': 'Computer Science',
        'college name': 'Metropolitan University',
        'email': 'alex.turner@metro.edu',
        'internship name': 'Mobile App Development',
        'start date': '2024-07-01',
        'end date': '2024-09-30',
        'mentor name': 'Ms. Jennifer Davis',
        'location': 'New York, NY',
        'grade': 'A',
        'specialization': 'Flutter & iOS Development'
    },
    {
        'student name': 'Maria Gonzalez',
        'roll number': 'EE2021006',
        'branch': 'Electrical Engineering',
        'college name': 'Tech Institute',
        'email': 'maria.gonzalez@techins.edu',
        'internship name': 'Renewable Energy Systems',
        'start date': '2024-06-05',
        'end date': '2024-08-05',
        'mentor name': 'Dr. James Wilson',
        'location': 'Phoenix, AZ',
        'grade': 'B+',
        'specialization': 'Solar Panel Design & Installation'
    },
    {
        'student name': 'Kevin Lee',
        'roll number': 'CS2021007',
        'branch': 'Computer Science',
        'college name': 'Digital University',
        'email': 'kevin.lee@digital.edu',
        'internship name': 'Cybersecurity Research',
        'start date': '2024-05-15',
        'end date': '2024-08-15',
        'mentor name': 'Dr. Amanda Foster',
        'location': 'Washington, DC',
        'grade': 'A+',
        'specialization': 'Network Security & Penetration Testing'
    },
    {
        'student name': 'Sophie Martin',
        'roll number': 'CE2021008',
        'branch': 'Civil Engineering',
        'college name': 'Construction College',
        'email': 'sophie.martin@cc.edu',
        'internship name': 'Smart City Infrastructure',
        'start date': '2024-06-20',
        'end date': '2024-09-20',
        'mentor name': 'Prof. Daniel Brown',
        'location': 'Chicago, IL',
        'grade': 'A',
        'specialization': 'Urban Planning & Smart Systems'
    },
    {
        'student name': 'Ryan Johnson',
        'roll number': 'AI2021009',
        'branch': 'Artificial Intelligence',
        'college name': 'Future Tech Academy',
        'email': 'ryan.johnson@fta.edu',
        'internship name': 'AI & Machine Learning',
        'start date': '2024-07-15',
        'end date': '2024-10-15',
        'mentor name': 'Dr. Emily Chang',
        'location': 'San Jose, CA',
        'grade': 'A+',
        'specialization': 'Deep Learning & Neural Networks'
    },
    {
        'student name': 'Isabella Garcia',
        'roll number': 'BT2021010',
        'branch': 'Biotechnology',
        'college name': 'Life Sciences University',
        'email': 'isabella.garcia@lsu.edu',
        'internship name': 'Biomedical Research',
        'start date': '2024-06-25',
        'end date': '2024-08-25',
        'mentor name': 'Dr. Mark Anderson',
        'location': 'Boston, MA',
        'grade': 'A',
        'specialization': 'Genetic Engineering & Lab Research'
    }
]

# Create DataFrame
df = pd.DataFrame(students_data)

# Save to Excel file
excel_filename = 'sample_students_data.xlsx'
df.to_excel(excel_filename, index=False, engine='openpyxl')

print(f"Sample Excel file '{excel_filename}' created successfully!")
print(f"Number of students: {len(students_data)}")
print("\nColumns in the Excel file:")
for col in df.columns:
    print(f"- {col}")

print(f"\nFile saved as: {excel_filename}")
print("You can now upload this file to the Certificate Management System.")