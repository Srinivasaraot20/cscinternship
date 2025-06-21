#!/usr/bin/env python3
"""
Create admin user for the certificate management system
"""

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@certificate.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists!")
            print("Username: admin")
            print("Password: admin123")

if __name__ == '__main__':
    create_admin_user()