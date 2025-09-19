"""
Authentication routes for student login/signup
Handles user registration, login, logout, and session management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
import traceback
from .models import db, Student

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def validate_email(email):
    """Validate email format"""
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    return len(password) >= 6

def validate_phone(phone):
    """Validate phone number format"""
    if not phone:
        return True  # Phone is optional
    # Basic phone validation - can be enhanced
    pattern = r'^[\+]?[\d\s\-\(\)]{10,}$'
    return re.match(pattern, phone) is not None

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Student signup page"""
    if request.method == 'POST':
        # Check if request is JSON (AJAX) or form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Extract form data
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        errors = {}
        
        if not first_name or len(first_name) < 2:
            errors['first_name'] = 'First name must be at least 2 characters long'
        
        if not last_name or len(last_name) < 2:
            errors['last_name'] = 'Last name must be at least 2 characters long'
        
        if not email:
            errors['email'] = 'Email is required'
        elif not validate_email(email):
            errors['email'] = 'Please enter a valid email address'
        elif Student.query.filter_by(email=email).first():
            errors['email'] = 'Email already registered. Please use a different email or login.'
        
        if phone and not validate_phone(phone):
            errors['phone'] = 'Please enter a valid phone number'
        
        if not password:
            errors['password'] = 'Password is required'
        elif not validate_password(password):
            errors['password'] = 'Password must be at least 6 characters long'
        
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            else:
                for field, message in errors.items():
                    flash(f'{field}: {message}', 'error')
                return render_template('singup_login/singup.html', errors=errors)
        
        try:
            # Create new student
            student = Student(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone if phone else None
            )
            student.set_password(password)
            
            db.session.add(student)
            db.session.commit()
            
            # Log in the user
            login_user(student)
            
            # Store user info in session
            session['student_id'] = student.id
            session['student_name'] = student.get_full_name()
            session['student_email'] = student.email
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Account created successfully!',
                    'redirect_url': url_for('index')
                })
            else:
                flash('Account created successfully! Welcome to EduConsult.', 'success')
                return redirect(url_for('index'))
        
        except Exception as e:
            db.session.rollback()
            error_message = 'An error occurred during registration. Please try again.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_message}), 500
            else:
                flash(error_message, 'error')
                return render_template('singup_login/singup.html')
    
    # GET request - show signup form
    return render_template('singup_login/singup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Student login page"""
    if request.method == 'POST':
        # Check if request is JSON (AJAX) or form data
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        remember_me = data.get('remember_me', False)
        
        # Validation
        errors = {}
        
        if not email:
            errors['email'] = 'Email is required'
        elif not validate_email(email):
            errors['email'] = 'Please enter a valid email address'
        
        if not password:
            errors['password'] = 'Password is required'
        
        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors}), 400
            else:
                for field, message in errors.items():
                    flash(f'{field}: {message}', 'error')
                return render_template('singup_login/singup.html', errors=errors)
        
        # Check credentials
        student = Student.query.filter_by(email=email).first()
        
        if not student or not student.check_password(password):
            error_message = 'Invalid email or password'
            if request.is_json:
                return jsonify({'success': False, 'message': error_message}), 401
            else:
                flash(error_message, 'error')
                return render_template('singup_login/singup.html')
        
        if not student.is_active:
            error_message = 'Your account has been deactivated. Please contact support.'
            if request.is_json:
                return jsonify({'success': False, 'message': error_message}), 401
            else:
                flash(error_message, 'error')
                return render_template('singup_login/singup.html')
        
        try:
            # Update last login
            student.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log in the user
            login_user(student, remember=remember_me)
            
            # Store user info in session
            session['student_id'] = student.id
            session['student_name'] = student.get_full_name()
            session['student_email'] = student.email
            
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'Login successful!',
                    'redirect_url': url_for('index')
                })
            else:
                flash(f'Welcome back, {student.get_full_name()}!', 'success')
                return redirect(url_for('index'))
        
        except Exception as e:
            db.session.rollback()
            # Log the actual exception for debugging
            print(f"LOGIN ERROR: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            error_message = f'An error occurred during login: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': error_message}), 500
            else:
                flash(error_message, 'error')
                return render_template('singup_login/singup.html')
    
    # GET request - show login form
    return render_template('singup_login/singup.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Student logout"""
    student_name = current_user.get_full_name() if current_user.is_authenticated else 'User'
    
    # Clear session data
    session.pop('student_id', None)
    session.pop('student_name', None)
    session.pop('student_email', None)
    session.pop('chat_session_id', None)
    session.pop('requires_human', None)
    session.pop('escalated_at', None)
    
    logout_user()
    flash(f'Goodbye, {student_name}! You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/check-auth')
def check_auth():
    """API endpoint to check authentication status"""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'student': current_user.to_dict()
        })
    else:
        return jsonify({'authenticated': False})

@auth_bp.route('/profile')
@login_required
def profile():
    """Student profile page"""
    return render_template('auth/profile.html', student=current_user)

@auth_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """Update student profile"""
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # Extract form data
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    phone = data.get('phone', '').strip()
    country_of_interest = data.get('country_of_interest', '').strip()
    field_of_study = data.get('field_of_study', '').strip()
    study_level = data.get('study_level', '').strip()
    
    # Validation
    errors = {}
    
    if not first_name or len(first_name) < 2:
        errors['first_name'] = 'First name must be at least 2 characters long'
    
    if not last_name or len(last_name) < 2:
        errors['last_name'] = 'Last name must be at least 2 characters long'
    
    if phone and not validate_phone(phone):
        errors['phone'] = 'Please enter a valid phone number'
    
    if errors:
        if request.is_json:
            return jsonify({'success': False, 'errors': errors}), 400
        else:
            for field, message in errors.items():
                flash(f'{field}: {message}', 'error')
            return redirect(url_for('auth.profile'))
    
    try:
        # Update student profile
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.phone = phone if phone else None
        current_user.country_of_interest = country_of_interest if country_of_interest else None
        current_user.field_of_study = field_of_study if field_of_study else None
        current_user.study_level = study_level if study_level else None
        
        db.session.commit()
        
        # Update session data
        session['student_name'] = current_user.get_full_name()
        
        if request.is_json:
            return jsonify({
                'success': True, 
                'message': 'Profile updated successfully!',
                'student': current_user.to_dict()
            })
        else:
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('auth.profile'))
    
    except Exception as e:
        db.session.rollback()
        error_message = 'An error occurred while updating profile. Please try again.'
        if request.is_json:
            return jsonify({'success': False, 'message': error_message}), 500
        else:
            flash(error_message, 'error')
            return redirect(url_for('auth.profile'))
