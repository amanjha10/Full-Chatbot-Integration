from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import os
import json
import re
import time
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
from setup_rag import RAGSystem
import uuid
from werkzeug.utils import secure_filename

# Import human handoff system
from human_handoff import init_database, db, init_db_manager
from human_handoff.session_manager import session_manager
from human_handoff.agent_routes import agent_bp
from human_handoff.super_admin_routes import super_admin_bp
from human_handoff.socketio_events import init_socketio
from human_handoff.activity_tracker import init_activity_tracker
from human_handoff.models import UserProfile, Student, ChatSession
from human_handoff.daily_scheduler import init_daily_scheduler
from nepali_phone_validator import validate_nepali_phone, format_nepali_phone

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# File upload configuration
UPLOAD_FOLDER = 'user_data/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cache busting - use current timestamp to force browser to reload static files
CACHE_BUSTER = str(int(time.time()))

@app.context_processor
def inject_cache_buster():
    """Inject cache buster into all templates"""
    return {'cache_buster': CACHE_BUSTER}

@app.after_request
def add_cache_control_headers(response):
    """Add cache control headers to prevent caching issues"""
    if request.endpoint == 'static':
        # For static files, use cache busting instead of no-cache
        response.cache_control.max_age = 31536000  # 1 year
        response.cache_control.public = True
    else:
        # For dynamic content, prevent caching
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.after_request
def add_cache_control_headers(response):
    """Add cache control headers to prevent caching issues"""
    if request.endpoint == 'static':
        # For static files, use cache busting instead of no-cache
        response.cache_control.max_age = 31536000  # 1 year
        response.cache_control.public = True
    else:
        # For dynamic content, prevent caching
        response.cache_control.no_cache = True
        response.cache_control.no_store = True
        response.cache_control.must_revalidate = True
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# Configure SQLAlchemy for human handoff system
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///human_handoff.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize human handoff system
init_database(app)
init_db_manager(app)

# Register blueprints
app.register_blueprint(agent_bp)
app.register_blueprint(super_admin_bp)

# Initialize SocketIO for real-time communication
socketio = init_socketio(app)

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
# Create the model
model = genai.GenerativeModel(model_name='gemini-pro')

# Initialize RAG system with proper error handling
def initialize_rag():
    global RAG
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            RAG = RAGSystem()
            # Ensure the documents directory exists
            doc_path = 'data/documents/education_faq.json'
            if not os.path.exists(doc_path):
                print(f"Warning: Document file not found at {doc_path}")
                return False
                
            success = RAG.load_documents(doc_path)
            if success:
                print("RAG system initialized successfully!")
                return True
            else:
                print("RAG system failed to load documents")
                
        except Exception as e:
            print(f"Error initializing RAG system (attempt {retry_count + 1}/{max_retries}): {e}")
            RAG = None
        
        retry_count += 1
        if retry_count < max_retries:
            print(f"Retrying in 5 seconds...")
            import time
            time.sleep(5)
    
    return False

# Initialize RAG on startup (delayed to avoid startup hang)
RAG = None
rag_initialized = False
print("⚠️  RAG initialization delayed to avoid startup hang - will initialize on first use")

# Mock database - In production, use a real database
COUNTRIES = [
    'United States', 'Canada', 'United Kingdom', 'Australia',
    'Germany', 'France', 'Netherlands', 'New Zealand',
    'Singapore', 'Ireland', 'Japan', 'South Korea', 'Other'
]

COURSES_DATABASE = {
    'United States': [
        {
            'name': 'MS Computer Science',
            'university': 'Stanford University',
            'fees': '$52,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s in CS/IT, GRE 320+, TOEFL 100+',
            'intake': 'Fall, Spring',
            'ranking': '#2 Global CS Rankings'
        },
        {
            'name': 'MBA',
            'university': 'Harvard Business School',
            'fees': '$73,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s degree, GMAT 730+, Work experience 3+ years',
            'intake': 'Fall',
            'ranking': '#1 Global MBA Rankings'
        },
        {
            'name': 'MS Data Science',
            'university': 'MIT',
            'fees': '$58,000/year',
            'duration': '1.5 years',
            'eligibility': 'Bachelor\'s in STEM, GRE 315+, Python/R proficiency',
            'intake': 'Fall, Spring',
            'ranking': '#1 Global Engineering Rankings'
        }
    ],
    'Canada': [
        {
            'name': 'MS Engineering',
            'university': 'University of Toronto',
            'fees': 'CAD 47,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s in Engineering, IELTS 7.0+',
            'intake': 'Fall, Winter, Summer',
            'ranking': '#1 in Canada'
        },
        {
            'name': 'MBA',
            'university': 'Rotman School of Management',
            'fees': 'CAD 65,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s degree, GMAT 650+, Work experience 2+ years',
            'intake': 'Fall',
            'ranking': '#1 MBA in Canada'
        },
        {
            'name': 'MS Computer Science',
            'university': 'UBC',
            'fees': 'CAD 42,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s in CS, GRE 310+, IELTS 6.5+',
            'intake': 'Fall, Winter',
            'ranking': '#3 in Canada'
        }
    ],
    'United Kingdom': [
        {
            'name': 'MS Finance',
            'university': 'London School of Economics',
            'fees': '£35,000/year',
            'duration': '1 year',
            'eligibility': 'Bachelor\'s in Finance/Economics, IELTS 7.0+',
            'intake': 'September',
            'ranking': '#2 Global Economics'
        },
        {
            'name': 'MS AI & Machine Learning',
            'university': 'Imperial College London',
            'fees': '£38,000/year',
            'duration': '1 year',
            'eligibility': 'Bachelor\'s in CS/Math, Strong programming skills',
            'intake': 'October',
            'ranking': '#4 Global Engineering'
        },
        {
            'name': 'MBA',
            'university': 'Oxford Said Business School',
            'fees': '£67,000/year',
            'duration': '1 year',
            'eligibility': 'Bachelor\'s degree, GMAT 690+, Work experience 3+ years',
            'intake': 'September',
            'ranking': '#6 Global MBA'
        }
    ],
    'Australia': [
        {
            'name': 'MS Information Technology',
            'university': 'University of Melbourne',
            'fees': 'AUD 44,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s degree, IELTS 6.5+',
            'intake': 'February, July',
            'ranking': '#1 in Australia'
        },
        {
            'name': 'MS Business Analytics',
            'university': 'Australian National University',
            'fees': 'AUD 45,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s in Business/Math, IELTS 6.5+',
            'intake': 'February, July',
            'ranking': '#2 in Australia'
        }
    ],
    'Germany': [
        {
            'name': 'MS Mechanical Engineering',
            'university': 'Technical University of Munich',
            'fees': '€3,000/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s in Engineering, German B2 or IELTS 6.5+',
            'intake': 'Winter, Summer',
            'ranking': '#1 Engineering in Germany'
        },
        {
            'name': 'MS Computer Science',
            'university': 'RWTH Aachen',
            'fees': '€3,500/year',
            'duration': '2 years',
            'eligibility': 'Bachelor\'s in CS, German B2 or IELTS 6.5+',
            'intake': 'Winter, Summer',
            'ranking': '#2 CS in Germany'
        }
    ]
}

STUDY_LEVELS = ['Undergraduate', 'Masters', 'PhD', 'Diploma', 'Certificate']
FIELDS_OF_STUDY = [
    'Computer Science', 'Business Administration', 'Engineering', 
    'Data Science', 'Medicine', 'Law', 'Arts & Humanities', 
    'Social Sciences', 'Natural Sciences', 'Other'
]

CUSTOMER_ADVISORS = [
    {'name': 'Anjali Sharma', 'specialization': 'USA & Canada', 'phone': '+91-9876543210'},
    {'name': 'Rajesh Kumar', 'specialization': 'UK & Europe', 'phone': '+91-9876543211'},
    {'name': 'Priya Patel', 'specialization': 'Australia & New Zealand', 'phone': '+91-9876543212'},
    {'name': 'Amit Singh', 'specialization': 'General Counseling', 'phone': '+91-9876543213'}
]

# Country codes for phone number validation
COUNTRY_CODES = [
    {'code': '+977', 'country': 'Nepal', 'flag': '🇳🇵'},
    {'code': '+91', 'country': 'India', 'flag': '🇮🇳'},
    {'code': '+1', 'country': 'United States/Canada', 'flag': '🇺🇸🇨🇦'},
    {'code': '+44', 'country': 'United Kingdom', 'flag': '🇬🇧'},
    {'code': '+61', 'country': 'Australia', 'flag': '🇦🇺'},
    {'code': '+49', 'country': 'Germany', 'flag': '🇩🇪'},
    {'code': '+33', 'country': 'France', 'flag': '🇫🇷'},
    {'code': '+31', 'country': 'Netherlands', 'flag': '🇳🇱'},
    {'code': '+64', 'country': 'New Zealand', 'flag': '🇳🇿'},
    {'code': '+65', 'country': 'Singapore', 'flag': '🇸🇬'},
    {'code': '+353', 'country': 'Ireland', 'flag': '🇮🇪'},
    {'code': '+81', 'country': 'Japan', 'flag': '🇯🇵'},
    {'code': '+86', 'country': 'China', 'flag': '🇨🇳'},
    {'code': '+977', 'country': 'Nepal', 'flag': '🇳🇵'},
    {'code': '+880', 'country': 'Bangladesh', 'flag': '🇧🇩'},
    {'code': '+94', 'country': 'Sri Lanka', 'flag': '🇱🇰'}
]

# Add a set of greeting/conversational queries
GREETING_KEYWORDS = [
    'hello', 'hi', 'hey', 'how are you', 'good morning', 'good afternoon', 
    'good evening', 'greetings', "what's up", "how's it going", 'namaste'
]

def is_greeting_query(user_message):
    """Check if a message is a greeting, being more precise to avoid false positives"""
    msg = user_message.lower().strip()

    # Check if message exactly matches a greeting
    if msg in GREETING_KEYWORDS:
        return True

    # Check if message starts with a greeting
    for greeting in GREETING_KEYWORDS:
        if msg.startswith(greeting + ' '):
            return True

    return False

def validate_name(name):
    """Validate user name input"""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    if len(name.strip()) > 100:
        return False, "Name must be less than 100 characters"
    if not re.match(r'^[a-zA-Z\s\-\.\']+$', name.strip()):
        return False, "Name can only contain letters, spaces, hyphens, dots, and apostrophes"
    return True, ""

def validate_phone_number(phone, country_code):
    """Validate phone number with country code"""
    if not phone or not phone.strip():
        return False, "Phone number is required"

    # Special handling for Nepal (+977) using dedicated validator
    if country_code == '+977':
        # Remove spaces, dashes, parentheses, and other formatting
        clean_phone = re.sub(r'[^\d+]', '', phone.strip())

        # Remove country code if present
        if clean_phone.startswith('+977'):
            clean_phone = clean_phone[4:]
        elif clean_phone.startswith('977'):
            clean_phone = clean_phone[3:]

        # Use Nepali phone validator
        result = validate_nepali_phone(clean_phone)
        if result['valid']:
            return True, f"✅ {result['message']} (Provider: {result['provider']})"
        else:
            return False, f"❌ {result['message']}"

    # General validation for other countries
    # Remove spaces, dashes, parentheses, and other formatting
    clean_phone = re.sub(r'[^\d+]', '', phone.strip())

    # If phone already includes country code, validate it
    if clean_phone.startswith(country_code):
        number_without_code = clean_phone[len(country_code):]
    elif clean_phone.startswith(country_code.replace('+', '')):
        # Handle case where + is missing
        number_without_code = clean_phone[len(country_code.replace('+', '')):]
    else:
        # Phone number without country code
        number_without_code = clean_phone

    # Remove leading zeros
    number_without_code = number_without_code.lstrip('0')

    # Basic length validation (most phone numbers are 6-15 digits without country code)
    if len(number_without_code) < 6 or len(number_without_code) > 15:
        return False, f"Phone number should be between 6-15 digits (you entered {len(number_without_code)} digits)"

    # Check if it contains only digits
    if not number_without_code.isdigit():
        return False, "Phone number should contain only digits"

    return True, ""

def validate_email(email):
    """Validate email format"""
    if not email or not email.strip():
        return True, ""  # Email is optional

    email = email.strip()
    pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(pattern, email):
        return False, "Please enter a valid email address"

    return True, ""

def get_semantic_response(user_input, context=None):
    """Use Gemini API for semantic understanding"""
    try:
        prompt = f"""
        You are an education consultancy chatbot. Analyze this user input and provide a structured response.
        
        User input: "{user_input}"
        Context: {context or "Initial conversation"}
        
        Available countries: {', '.join(COUNTRIES)}
        Available study levels: {', '.join(STUDY_LEVELS)}
        Available fields: {', '.join(FIELDS_OF_STUDY)}
        
        Based on the user input, determine:
        1. Intent (country_inquiry, course_inquiry, general_info, greeting, other)
        2. Extracted entities (countries, courses, study level mentioned)
        3. Suggested response type (country_suggestions, course_suggestions, specific_info, clarification_needed)
        4. Confidence level (high, medium, low)
        
        Respond in JSON format:
        {{
            "intent": "...",
            "entities": {{
                "countries": [],
                "courses": [],
                "study_level": "",
                "field_of_study": ""
            }},
            "response_type": "...",
            "confidence": "...",
            "suggested_reply": "..."
        }}
        """
        
        response = model.generate_content(prompt)
        
        # Try to parse JSON response
        try:
            result = json.loads(response.text)
            return result
        except:
            # Fallback if JSON parsing fails
            return {
                "intent": "other",
                "entities": {},
                "response_type": "clarification_needed",
                "confidence": "low",
                "suggested_reply": "I'd be happy to help you with your study abroad plans. Could you please tell me which country you're interested in?"
            }
    except Exception as e:
        print(f"Gemini API error: {e}")
        return {
            "intent": "other",
            "entities": {},
            "response_type": "clarification_needed",
            "confidence": "low",
            "suggested_reply": "I'd be happy to help you with your study abroad plans. Could you please tell me which country you're interested in?"
        }

def get_rag_response(user_input):
    """Query RAG system for document-based answers with improved matching"""
    if not RAG or not RAG.is_initialized:
        return None, 0.0
        
    try:
        # Clean up input
        user_input = user_input.strip().lower()
        
        # Get multiple results
        results = RAG.search(user_input, k=3)
        if not results:
            return None, 0.0
            
        # Use both semantic similarity and text matching
        best_result = None
        best_score = 0.0
        
        for res in results:
            # Get base score from RAG
            score = res['score']
            
            # Boost score if question contains exact matches
            query_words = set(user_input.split())
            question_words = set(res['question'].lower().split())
            word_overlap = len(query_words.intersection(question_words))
            
            if word_overlap > 0:
                overlap_bonus = 0.1 * (word_overlap / len(query_words))
                score += overlap_bonus
            
            if score > best_score:
                best_result = res
                best_score = score
                
        print(f"Best RAG match: Score={best_score}, Question={best_result['question'] if best_result else 'None'}")
        return best_result, best_score
        
    except Exception as e:
        print(f"Error in RAG response: {e}")
        return None, 0.0

def get_user_profile_status(session_id):
    """Check if user profile exists for this session"""
    try:
        profile = UserProfile.query.filter_by(session_id=session_id).first()
        return profile
    except Exception as e:
        print(f"Error checking user profile: {e}")
        return None

def get_persistent_user_profile():
    """Get user profile from persistent storage (localStorage key or database)"""
    try:
        # Try to get from request headers (sent by frontend localStorage)
        persistent_user_id = request.headers.get('X-Persistent-User-ID')
        if persistent_user_id:
            # Look for existing profile by persistent ID
            profile = UserProfile.query.filter_by(persistent_user_id=persistent_user_id).first()
            if profile:
                return profile

        # Fallback to session-based lookup for existing profiles
        session_id = session_manager.get_session_id()
        profile = UserProfile.query.filter_by(session_id=session_id).first()

        # If we found a profile by session but it has a persistent_user_id,
        # return it along with the persistent_user_id for frontend to save
        if profile and profile.persistent_user_id:
            return profile

        return profile
    except Exception as e:
        print(f"Error getting persistent user profile: {e}")
        return None

def save_user_profile(session_id, name, phone, email=None):
    """Save user profile to database with persistent user ID"""
    try:
        # Check for persistent user ID in headers
        persistent_user_id = request.headers.get('X-Persistent-User-ID')

        # Check if profile already exists
        existing_profile = None
        if persistent_user_id:
            existing_profile = UserProfile.query.filter_by(persistent_user_id=persistent_user_id).first()

        if not existing_profile:
            existing_profile = UserProfile.query.filter_by(session_id=session_id).first()

        if existing_profile:
            # Update existing profile
            existing_profile.name = name.strip()
            existing_profile.phone = phone.strip()
            existing_profile.email = email.strip() if email and email.strip() else None
            existing_profile.last_used = datetime.utcnow()
            existing_profile.session_id = session_id  # Update session ID
            db.session.commit()
            return existing_profile

        # Generate persistent user ID if not provided
        if not persistent_user_id:
            import uuid
            persistent_user_id = f"user_{uuid.uuid4().hex[:12]}"

        # Create new profile
        profile = UserProfile(
            session_id=session_id,
            persistent_user_id=persistent_user_id,
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip() if email and email.strip() else None
        )

        db.session.add(profile)
        db.session.commit()
        return profile
    except Exception as e:
        print(f"Error saving user profile: {e}")
        db.session.rollback()
        return None





def save_user_profile(session_id, name, phone, email=None):
    """Save user profile to database"""
    try:
        # Check if profile already exists
        existing_profile = UserProfile.query.filter_by(session_id=session_id).first()
        if existing_profile:
            return existing_profile

        # Create new profile
        profile = UserProfile(
            session_id=session_id,
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip() if email and email.strip() else None
        )

        db.session.add(profile)
        db.session.commit()
        return profile
    except Exception as e:
        print(f"Error saving user profile: {e}")
        db.session.rollback()
        return None

def emit_bot_message_to_agents(session_id, message_content):
    """Emit bot message to agents if session is being handled by human"""
    try:
        if session_manager.is_human_handling_session():
            socketio.emit('new_message', {
                'session_id': session_id,
                'sender_type': 'bot',
                'sender_id': 'system',
                'message_content': message_content,
                'timestamp': datetime.utcnow().isoformat(),
                'sender_name': 'EduConsult Bot'
            }, room=session_id)
            print(f"Emitted bot message to agents in session {session_id}: {message_content[:50]}...")
    except Exception as e:
        print(f"Error emitting bot message: {e}")

# File upload helper functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, session_id, message_context=None):
    """Save uploaded file and return file info"""
    try:
        if not file or not file.filename:
            print(f"DEBUG: No file or filename provided")
            return None

        if not allowed_file(file.filename):
            print(f"DEBUG: File type not allowed: {file.filename}")
            return None

        # Create session-specific directory
        session_dir = os.path.join(UPLOAD_FOLDER, session_id)
        os.makedirs(session_dir, exist_ok=True)
        print(f"DEBUG: Created directory: {session_dir}")

        # Secure filename
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"

        filepath = os.path.join(session_dir, filename)
        file.save(filepath)
        print(f"DEBUG: Saved file: {filepath}")

        file_size = os.path.getsize(filepath)
        file_type = filename.rsplit('.', 1)[1].lower()

        # Save to database
        file_db_id = None
        try:
            from human_handoff.models import UploadedFile, UserProfile

            # Try to get user profile for this session
            user_profile = UserProfile.query.filter_by(session_id=session_id).first()

            uploaded_file = UploadedFile(
                session_id=session_id,
                user_profile_id=user_profile.id if user_profile else None,
                original_name=file.filename,
                filename=filename,
                filepath=filepath,
                file_size=file_size,
                file_type=file_type,
                message_context=message_context
            )

            db.session.add(uploaded_file)
            db.session.commit()
            file_db_id = uploaded_file.id
            print(f"DEBUG: Saved file to database with ID: {file_db_id}")

        except Exception as db_error:
            print(f"WARNING: Failed to save file to database: {db_error}")
            # Continue without database save

        file_info = {
            'id': file_db_id,
            'filename': filename,
            'original_name': file.filename,
            'filepath': filepath,
            'size': file_size,
            'type': file_type
        }
        print(f"DEBUG: File info: {file_info}")
        return file_info

    except Exception as e:
        print(f"ERROR: Failed to save file {file.filename}: {e}")
        return None

def process_uploaded_files(files, session_id, message_context=None):
    """Process multiple uploaded files"""
    processed_files = []

    print(f"DEBUG: process_uploaded_files called with keys: {list(files.keys())}")

    for key, file in files.items():
        print(f"DEBUG: Processing file key: '{key}', filename: '{file.filename if file else 'None'}'")

        # Handle both 'files' (from curl/form) and 'file_' prefixed keys (from frontend)
        if (key == 'files' or key.startswith('file_')) and file and file.filename:
            print(f"DEBUG: Attempting to save file: {file.filename}")
            file_info = save_uploaded_file(file, session_id, message_context)
            if file_info:
                print(f"DEBUG: Successfully saved file: {file_info}")
                processed_files.append(file_info)
            else:
                print(f"DEBUG: Failed to save file: {file.filename}")
        else:
            print(f"DEBUG: Skipping key '{key}' - doesn't match criteria or no filename")

    print(f"DEBUG: Total processed files: {len(processed_files)}")
    return processed_files

def handle_user_profile_collection(user_message, session_id, context=None):
    """Handle user profile collection flow"""
    # Check for persistent profile first
    persistent_profile = get_persistent_user_profile()

    if persistent_profile:
        # Profile already exists, continue with normal chat
        print(f"DEBUG: Persistent profile exists for {persistent_profile.name}, skipping collection")
        return None

    # Check current session profile status
    profile = get_user_profile_status(session_id)

    # Get or initialize profile collection state from session
    from flask import session as flask_session
    profile_state = flask_session.get('profile_collection_state', 'need_name')

    if profile:
        # Profile already exists, continue with normal chat
        print(f"DEBUG: Session profile exists, skipping collection")
        return None

    # Handle profile collection based on current state
    if profile_state == 'need_name' or profile_state == 'collecting_name':
        # User is sending their name (first message after hardcoded welcome)
        # Validate name
        is_valid, error_msg = validate_name(user_message)
        if not is_valid:
            return {
                'response': f"I'm sorry, but {error_msg}. Please enter your full name:",
                'suggestions': [],
                'type': 'profile_collection',
                'collecting': 'name'
            }

        # Name is valid, store it and ask for country code
        flask_session['user_name'] = user_message.strip()
        flask_session['profile_collection_state'] = 'selecting_country_code'

        country_suggestions = [f"{cc['code']} {cc['flag']} {cc['country']}" for cc in COUNTRY_CODES[:8]]

        return {
            'response': f"Nice to meet you, {user_message.strip()}! 👋<br><br>Now I need your phone number for our records. Please first select your country code:",
            'suggestions': country_suggestions + ['Show more countries'],
            'type': 'profile_collection',
            'collecting': 'country_code'
        }




    elif profile_state == 'selecting_country_code':
        # Handle country code selection
        if user_message.lower() == 'show more countries':
            # Show remaining country codes
            country_suggestions = [f"{cc['code']} {cc['flag']} {cc['country']}" for cc in COUNTRY_CODES[8:]]
            return {
                'response': "Here are more country codes to choose from:",
                'suggestions': country_suggestions + ['Show previous countries'],
                'type': 'profile_collection',
                'collecting': 'country_code'
            }
        elif user_message.lower() == 'show previous countries':
            # Show first set of country codes
            country_suggestions = [f"{cc['code']} {cc['flag']} {cc['country']}" for cc in COUNTRY_CODES[:8]]
            return {
                'response': "Please select your country code:",
                'suggestions': country_suggestions + ['Show more countries'],
                'type': 'profile_collection',
                'collecting': 'country_code'
            }
        else:
            # Extract country code from selection - handle multiple formats
            selected_code = None
            selected_country = None

            # Try different matching patterns
            for cc in COUNTRY_CODES:
                # Pattern 1: "+977 🇳🇵 Nepal"
                if user_message.startswith(cc['code']):
                    selected_code = cc['code']
                    selected_country = cc['country']
                    break
                # Pattern 2: "🇳🇵 Nepal (+977)"
                elif cc['code'] in user_message and cc['country'].lower() in user_message.lower():
                    selected_code = cc['code']
                    selected_country = cc['country']
                    break
                # Pattern 3: Just the country name
                elif cc['country'].lower() in user_message.lower():
                    selected_code = cc['code']
                    selected_country = cc['country']
                    break
                # Pattern 4: Just the code
                elif cc['code'].replace('+', '') in user_message.replace('+', ''):
                    selected_code = cc['code']
                    selected_country = cc['country']
                    break

            if not selected_code:
                return {
                    'response': "Please select a valid country code from the options above:",
                    'suggestions': [f"{cc['code']} {cc['flag']} {cc['country']}" for cc in COUNTRY_CODES[:8]] + ['Show more countries'],
                    'type': 'profile_collection',
                    'collecting': 'country_code'
                }

            # Store selected country code and ask for phone number
            flask_session['selected_country_code'] = selected_code
            flask_session['selected_country_name'] = selected_country
            flask_session['profile_collection_state'] = 'collecting_phone'

            return {
                'response': f"Great! You selected {selected_country} ({selected_code}).<br><br>Now please enter your phone number (without the country code).<br><br>For example, if your number is {selected_code}1234567890, just enter: 1234567890",
                'suggestions': [],
                'type': 'profile_collection',
                'collecting': 'phone'
            }

    elif profile_state == 'collecting_phone':
        # Validate phone number
        country_code = flask_session.get('selected_country_code', '+1')
        user_phone = user_message.strip()

        # Create full phone number
        if user_phone.startswith(country_code):
            full_phone = user_phone
        elif user_phone.startswith(country_code.replace('+', '')):
            full_phone = '+' + user_phone
        else:
            full_phone = country_code + user_phone

        is_valid, error_msg = validate_phone_number(user_phone, country_code)
        if not is_valid:
            return {
                'response': f"I'm sorry, but {error_msg}.<br><br>Please enter your phone number (without the country code {country_code}):<br><br>Example: If your full number is {country_code}1234567890, just enter: 1234567890",
                'suggestions': [],
                'type': 'profile_collection',
                'collecting': 'phone'
            }

        # Phone is valid, store it and ask for email
        flask_session['user_phone'] = full_phone
        flask_session['profile_collection_state'] = 'collecting_email'

        return {
            'response': f"Perfect! Your phone number {full_phone} has been saved. 📱<br><br>Finally, would you like to provide your email address? This is optional and will help us send you important updates about your study abroad journey.",
            'suggestions': ['Skip email', 'I\'ll provide email'],
            'type': 'profile_collection',
            'collecting': 'email'
        }

    elif profile_state == 'collecting_email':
        # Handle email collection
        if user_message.lower() in ['skip email', 'skip', 'no', 'no email', 'i don\'t want to provide email']:
            # Skip email and complete profile
            name = flask_session.get('user_name', '')
            phone = flask_session.get('user_phone', '')

            # Save profile without email
            profile = save_user_profile(session_id, name, phone, None)

            if profile:
                # Clear profile collection state and mark as completed
                flask_session.pop('profile_collection_state', None)
                flask_session.pop('user_name', None)
                flask_session.pop('user_phone', None)
                flask_session.pop('selected_country_code', None)
                flask_session['profile_completed'] = True  # Mark profile as completed

                return {
                    'response': f"Thank you, {name}! Your profile has been saved successfully. 🎉<br><br>Now I'm ready to help you with your study abroad journey. How can I assist you today?",
                    'suggestions': [
                        '🌍 Choose Country',
                        '🎓 Browse Programs',
                        '📚 Requirements',
                        '💰 Scholarships',
                        '🗣️ Talk to Advisor'
                    ],
                    'type': 'main_menu',
                    'persistent_user_id': profile.persistent_user_id  # Send persistent ID to frontend
                }
            else:
                return {
                    'response': "I'm sorry, there was an error saving your profile. Please try again or contact support.",
                    'suggestions': ['Try again', 'Contact support'],
                    'type': 'error'
                }

        elif user_message.lower() in ['i\'ll provide email', 'provide email', 'yes', 'yes email']:
            flask_session['profile_collection_state'] = 'entering_email'
            return {
                'response': "Great! Please enter your email address:",
                'suggestions': ['Skip email'],
                'type': 'profile_collection',
                'collecting': 'email_input'
            }
        else:
            # User might have directly entered email
            is_valid, error_msg = validate_email(user_message)
            if not is_valid and user_message.strip():
                return {
                    'response': f"I'm sorry, but {error_msg}. Please enter a valid email address or skip:",
                    'suggestions': ['Skip email'],
                    'type': 'profile_collection',
                    'collecting': 'email_input'
                }

            # Email is valid or empty, complete profile
            name = flask_session.get('user_name', '')
            phone = flask_session.get('user_phone', '')
            email = user_message.strip() if user_message.strip() else None

            # Save profile with email
            profile = save_user_profile(session_id, name, phone, email)

            if profile:
                # Clear profile collection state and mark as completed
                flask_session.pop('profile_collection_state', None)
                flask_session.pop('user_name', None)
                flask_session.pop('user_phone', None)
                flask_session.pop('selected_country_code', None)
                flask_session['profile_completed'] = True  # Mark profile as completed

                email_msg = f" and email {email}" if email else ""
                return {
                    'response': f"Thank you, {name}! Your profile with phone {phone}{email_msg} has been saved successfully. 🎉<br><br>Now I'm ready to help you with your study abroad journey. How can I assist you today?",
                    'suggestions': [
                        '🌍 Choose Country',
                        '🎓 Browse Programs',
                        '📚 Requirements',
                        '💰 Scholarships',
                        '🗣️ Talk to Advisor'
                    ],
                    'type': 'main_menu'
                }

    elif profile_state == 'entering_email':
        # Handle direct email entry
        if user_message.lower() in ['skip email', 'skip']:
            # Complete profile without email
            name = flask_session.get('user_name', '')
            phone = flask_session.get('user_phone', '')

            profile = save_user_profile(session_id, name, phone, None)

            if profile:
                # Clear profile collection state
                flask_session.pop('profile_collection_state', None)
                flask_session.pop('user_name', None)
                flask_session.pop('user_phone', None)
                flask_session.pop('selected_country_code', None)

                return {
                    'response': f"Thank you, {name}! Your profile has been saved successfully. 🎉<br><br>Now I'm ready to help you with your study abroad journey. How can I assist you today?",
                    'suggestions': [
                        '🌍 Choose Country',
                        '🎓 Browse Programs',
                        '📚 Requirements',
                        '💰 Scholarships',
                        '🗣️ Talk to Advisor'
                    ],
                    'type': 'main_menu'
                }
        else:
            # Validate and save email
            is_valid, error_msg = validate_email(user_message)
            if not is_valid and user_message.strip():
                return {
                    'response': f"I'm sorry, but {error_msg}. Please enter a valid email address or skip:",
                    'suggestions': ['Skip email'],
                    'type': 'profile_collection',
                    'collecting': 'email_input'
                }

            # Complete profile with email
            name = flask_session.get('user_name', '')
            phone = flask_session.get('user_phone', '')
            email = user_message.strip() if user_message.strip() else None

            profile = save_user_profile(session_id, name, phone, email)

            if profile:
                # Clear profile collection state
                flask_session.pop('profile_collection_state', None)
                flask_session.pop('user_name', None)
                flask_session.pop('user_phone', None)
                flask_session.pop('selected_country_code', None)

                email_msg = f" and email {email}" if email else ""
                return {
                    'response': f"Thank you, {name}! Your profile with phone {phone}{email_msg} has been saved successfully. 🎉<br><br>Now I'm ready to help you with your study abroad journey. How can I assist you today?",
                    'suggestions': [
                        '🌍 Choose Country',
                        '🎓 Browse Programs',
                        '📚 Requirements',
                        '💰 Scholarships',
                        '🗣️ Talk to Advisor'
                    ],
                    'type': 'main_menu'
                }

    # Default fallback
    return None

def search_courses(query, country=None):
    """Search courses based on query and country"""
    results = []

    if country and country in COURSES_DATABASE:
        courses = COURSES_DATABASE[country]
    else:
        courses = []
        for country_courses in COURSES_DATABASE.values():
            courses.extend(country_courses)

    # Simple keyword matching - in production, use better search
    query_lower = query.lower()
    for course in courses:
        if (query_lower in course['name'].lower() or
            query_lower in course['university'].lower() or
            any(keyword in course['name'].lower() for keyword in query_lower.split())):
            results.append(course)

    return results[:5]  # Return top 5 matches

@app.route('/')
def index():
    """Render the front page with chatbot popup"""
    return render_template('front_page/index1.html')

@app.route('/chatbot')
def chatbot():
    """Render the main chatbot page"""
    return render_template('index.html')

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear session for testing purposes"""
    from flask import session as flask_session
    flask_session.clear()
    return jsonify({'status': 'Session cleared'})

@app.route('/reset-session', methods=['POST'])
def reset_session():
    """Reset the current session - create new session ID"""
    new_session_id = session_manager.reset_session()
    return jsonify({
        'status': 'Session reset',
        'new_session_id': new_session_id
    })

@app.route('/api/session-status', methods=['GET'])
def api_session_status():
    """Get current session status"""
    try:
        session_id = session_manager.get_session_id()
        is_escalated = session_manager.is_human_handling_session()

        # Get session details from database
        from human_handoff.models import ChatSession, UserProfile
        chat_session = ChatSession.query.filter_by(session_id=session_id).first()

        # Check if there's an active session with a profile for this user
        active_session_with_profile = None
        try:
            # Look for active sessions with profiles, prioritizing assigned sessions
            # Custom ordering: assigned (with agent) > escalated > active
            active_sessions = ChatSession.query.filter(
                ChatSession.status.in_(['assigned', 'escalated', 'active'])
            ).order_by(
                # Prioritize assigned sessions with agents
                ChatSession.assigned_agent_id.isnot(None).desc(),
                ChatSession.status == 'assigned',
                ChatSession.created_at.desc()
            ).all()

            for session in active_sessions:
                profile = UserProfile.query.filter_by(session_id=session.session_id).first()
                if profile:
                    active_session_with_profile = session
                    print(f"Found active session with profile: {session.session_id} (status: {session.status})")
                    break
        except Exception as e:
            print(f"Error checking for active sessions with profiles: {e}")

        return jsonify({
            'session_id': session_id,
            'is_escalated': is_escalated,
            'status': chat_session.status if chat_session else 'new',
            'requires_human': chat_session.requires_human if chat_session else False,
            'assigned_agent_id': chat_session.assigned_agent_id if chat_session else None,
            'active_session_with_profile': active_session_with_profile.session_id if active_session_with_profile else None
        })
    except Exception as e:
        print(f"Error getting session status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch-session', methods=['POST'])
def api_switch_session():
    """Switch to a different session"""
    try:
        data = request.get_json()
        target_session_id = data.get('target_session_id')

        if not target_session_id:
            return jsonify({'error': 'target_session_id is required'}), 400

        # Verify the target session exists
        from human_handoff.models import ChatSession
        target_session = ChatSession.query.filter_by(session_id=target_session_id).first()
        if not target_session:
            return jsonify({'error': 'Target session not found'}), 404

        # Switch the session
        session['chat_session_id'] = target_session_id
        print(f"Switched to session: {target_session_id}")

        return jsonify({
            'success': True,
            'new_session_id': target_session_id,
            'message': 'Session switched successfully'
        })
    except Exception as e:
        print(f"Error switching session: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    if not request.json or 'message' not in request.json:
        return jsonify({'error': 'Invalid request'}), 400

    user_message = request.json['message'].strip()
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    context = request.json.get('context', 'Initial conversation')

    # Initialize session and log user message
    session_manager.start_session()
    session_manager.log_user_message(user_message, metadata={'context': context})

    # Get session ID first
    session_id = session_manager.get_session_id()

    # Check if we need to collect user profile first (BEFORE human handling check)
    # This ensures profile collection works even if session is marked as escalated

    # Check if profile collection is needed
    profile_state = session.get('profile_collection_state')
    profile_completed = session.get('profile_completed', False)

    print(f"DEBUG: Profile collection check - State: {profile_state}, Completed: {profile_completed}")
    print(f"DEBUG: User message: '{user_message}'")
    print(f"DEBUG: Session keys: {list(session.keys())}")

    # Force profile collection if not completed
    if not profile_completed or profile_state in ['need_name', 'selecting_country_code', 'collecting_phone', 'collecting_email']:
        # Initialize profile collection state if not set
        if 'profile_collection_state' not in session:
            session['profile_collection_state'] = 'need_name'
            print(f"DEBUG: Initialized profile collection state to 'need_name' for session {session_id}")

        print(f"DEBUG: Calling profile collection for message: '{user_message}'")
        profile_response = handle_user_profile_collection(user_message, session_id, context)
        if profile_response:
            print(f"DEBUG: Profile collection returned response: {profile_response.get('type', 'unknown')}")
            # Log profile collection response
            session_manager.log_bot_message(profile_response['response'], metadata={'source': 'profile_collection'})
            return jsonify(profile_response)
        else:
            print(f"DEBUG: Profile collection returned None, continuing to main chat")

    # Check if session is being handled by a human agent (AFTER profile collection)
    if session_manager.is_human_handling_session():
        # Emit user message to agents in real-time
        try:
            socketio.emit('new_message', {
                'session_id': session_id,
                'sender_type': 'user',
                'sender_id': None,
                'message_content': user_message,
                'timestamp': datetime.utcnow().isoformat(),
                'context': context
            }, room=session_id)
            print(f"Emitted user message to agents in session {session_id}: {user_message[:50]}...")
        except Exception as e:
            print(f"Error emitting user message: {e}")

        # Session is being handled by human - don't let bot respond
        return jsonify({
            'response': '',  # No bot response
            'suggestions': [],
            'type': 'human_handling',
            'escalated': True,
            'session_info': session_manager.get_session_info()
        })

    # Handle menu navigation buttons BEFORE RAG system
    if user_message.lower() in ['explore countries', 'browse countries', 'choose country', '🌍 choose country']:
        return jsonify({
            'response': "Here are the top study destinations. Which country interests you?",
            'suggestions': [
                '🇺🇸 United States',
                '🇨🇦 Canada',
                '🇬🇧 United Kingdom',
                '🇦🇺 Australia',
                '🇩🇪 Germany',
                'More countries',
                '🎓 Browse by Field'
            ],
            'type': 'country_selection'
        })
    elif user_message.lower() == 'more countries':
        return jsonify({
            'response': "Here are more study destinations to explore:",
            'suggestions': [
                '🇫🇷 France',
                '🇳🇱 Netherlands',
                '🇳🇿 New Zealand',
                '🇸🇬 Singapore',
                '🇮🇪 Ireland',
                '🇯🇵 Japan',
                'Back to main countries',
                '🎓 Browse by Field'
            ],
            'type': 'country_selection'
        })
    elif user_message.lower() in ['browse programs', '🎓 browse programs']:
        return jsonify({
            'response': "What type of program are you interested in?",
            'suggestions': [
                '🎓 Undergraduate Programs',
                '🎓 Graduate Programs',
                '🎓 PhD Programs',
                '💼 MBA Programs',
                '🔬 Research Programs',
                '📚 Language Courses',
                '💻 Online Programs',
                'Back to main menu'
            ],
            'type': 'program_selection'
        })
    elif user_message.lower() in ['scholarships', '💰 scholarships']:
        return jsonify({
            'response': "Great! Here are scholarship opportunities for international students:",
            'suggestions': [
                '🏆 Merit-based Scholarships',
                '💰 Need-based Scholarships',
                '🌍 Country-specific Scholarships',
                '🎓 University Scholarships',
                '🔬 Research Scholarships',
                '👩‍🎓 Women in STEM Scholarships',
                'Back to main menu'
            ],
            'type': 'scholarship_selection'
        })
    elif user_message.lower() in ['requirements', '📚 requirements']:
        return jsonify({
            'response': "What type of requirements would you like to know about?",
            'suggestions': [
                'Visa Requirements',
                'Language Requirements',
                'Academic Requirements',
                'Financial Requirements',
                'Back to main menu'
            ],
            'type': 'requirements_selection'
        })
    elif user_message.lower() in ['talk to advisor', '🗣️ talk to advisor', 'human agent', 'speak to counselor']:
        # Direct escalation to human handoff system
        escalation_message = "I'll connect you with our expert counselor right away!"

        # Log the escalation request
        session_manager.log_bot_message(escalation_message, is_fallback=False)
        escalation_success = session_manager.handle_fallback(
            escalation_message,
            reason="User requested to talk to advisor"
        )

        if escalation_success:
            response = f"""{escalation_message}

🔄 **You're now in the queue for human assistance.**

A human agent will join this conversation shortly to help you with your query. Please wait a moment while we connect you.

In the meantime, you can:
- Continue asking questions (they'll be saved for the agent)
- Or wait for the agent to respond"""

            # Emit escalation message to agents
            emit_bot_message_to_agents(session_id, response)

            return jsonify({
                'response': response,
                'suggestions': ['Wait for agent', 'Ask another question', 'Start over'],
                'type': 'human_handoff_initiated',
                'escalated': True,
                'session_info': session_manager.get_session_info()
            })
        else:
            # Fallback to traditional advisor contact if escalation fails
            advisor = CUSTOMER_ADVISORS[0]  # Default advisor
            response = f"""I apologize, but our human agents are currently unavailable. Here's our expert counselor's contact information:

<strong>Assigned Advisor:</strong> {advisor['name']}<br>
<strong>Phone:</strong> {advisor['phone']}<br>
<strong>Specialization:</strong> {advisor['specialization']}<br>
<br>
Our advisor will contact you shortly, or you can call directly.<br><br>
<em>Is there anything else I can help you with?</em>"""

            return jsonify({
                'response': response.strip(),
                'suggestions': ['Continue with bot', 'Schedule callback', 'Back to main menu'],
                'type': 'advisor_contact'
            })
    elif user_message.lower() == 'back to main menu':
        return jsonify({
            'response': "What would you like to know about studying abroad?",
            'suggestions': [
                '🌍 Choose Country',
                '🎓 Browse Programs',
                '📚 Requirements',
                '💰 Scholarships',
                '🗣️ Talk to Advisor'
            ],
            'type': 'main_menu'
        })

    # Handle country and course selections BEFORE RAG system
    # Clean country name from emoji if present
    clean_message = re.sub(r'[^\w\s]', '', user_message).strip()

    if clean_message in COUNTRIES:
        # Country selected
        country = clean_message
        country_courses = COURSES_DATABASE.get(country, [])
        course_names = [course['name'] for course in country_courses]

        # Get country emoji
        country_emojis = {
            'United States': '🇺🇸',
            'Canada': '🇨🇦',
            'United Kingdom': '🇬🇧',
            'Australia': '🇦🇺',
            'Germany': '🇩🇪',
            'France': '🇫🇷',
            'Netherlands': '🇳🇱',
            'New Zealand': '🇳🇿',
            'Singapore': '🇸🇬',
            'Ireland': '🇮🇪',
            'Japan': '🇯🇵'
        }
        emoji = country_emojis.get(country, '🌍')

        response = f"{emoji} Great choice! Here are popular courses in {country}:"
        return jsonify({
            'response': response,
            'suggestions': course_names + ['Show all courses', 'Different country'],
            'type': 'course_selection',
            'data': {'selected_country': user_message}
        })
    elif user_message in [course['name'] for courses in COURSES_DATABASE.values() for course in courses]:
        # Course selected - find the course details
        for country, courses in COURSES_DATABASE.items():
            for course in courses:
                if course['name'] == user_message:
                    response = f"""
                    **{course['name']}** at **{course['university']}**

                    💰 **Fees:** {course['fees']}
                    ⏱️ **Duration:** {course['duration']}
                    📋 **Eligibility:** {course['eligibility']}
                    📅 **Intake:** {course['intake']}
                    🏆 **Ranking:** {course['ranking']}

                    Would you like more information about this course?
                    """
                    return jsonify({
                        'response': response.strip(),
                        'suggestions': ['Apply now', 'Similar courses', 'Different country', 'Talk to advisor'],
                        'type': 'course_details',
                        'data': {'selected_course': course, 'country': country}
                    })

    try:
        # Initialize RAG system on first use if not already initialized
        global RAG, rag_initialized
        if not rag_initialized:
            print("🔄 Initializing RAG system on first use...")
            rag_initialized = initialize_rag()
            if rag_initialized:
                print("✅ RAG system initialized successfully!")
            else:
                print("❌ RAG system failed to initialize")

        # Try RAG system (if initialized)
        if RAG and RAG.is_initialized:
            print(f"\nProcessing message with RAG: '{user_message}'")
            try:
                # Get RAG results
                rag_results = RAG.search(user_message, k=3)
                if rag_results and len(rag_results) > 0:
                    # Debug output
                    print("\nRAG Results:")
                    for idx, res in enumerate(rag_results):
                        print(f"Match {idx + 1}:")
                        print(f"  Question: {res['question']}")
                        print(f"  Score: {res['score']}")
                        print(f"  Category: {res.get('category', 'N/A')}")
                    
                    # Use top result if we got any matches
                    # (scoring threshold is already applied in RAG.search())
                    if rag_results:
                        top_result = rag_results[0]
                        print(f"Using RAG response with score: {top_result['score']}")
                        
                        # Prepare suggestions based on category
                        suggestions = get_suggestions_for_category(top_result.get('category', 'general'))

                        # Log successful bot response
                        session_manager.log_bot_message(
                            top_result['answer'],
                            metadata={
                                'source': 'RAG',
                                'score': top_result['score'],
                                'category': top_result.get('category', 'general')
                            }
                        )

                        # Emit bot response to agents if session is being handled by human
                        emit_bot_message_to_agents(session_id, top_result['answer'])

                        return jsonify({
                            'response': top_result['answer'],
                            'suggestions': suggestions,
                            'type': 'faq_response'
                        })
            except Exception as e:
                print(f"Error getting RAG response: {e}")

        # Check for greetings if no good RAG match was found
        if is_greeting_query(user_message):
            # Get appropriate time-based greeting
            current_time = datetime.now().hour
            if current_time < 12:
                greeting = "Good morning!"
            elif current_time < 17:
                greeting = "Good afternoon!"
            else:
                greeting = "Good evening!"
            response = f"{greeting} I'm EduConsult, your study abroad assistant. How can I help you today?"

            # Log greeting response
            session_manager.log_bot_message(response, metadata={'source': 'greeting'})

            # Emit greeting response to agents if session is being handled by human
            emit_bot_message_to_agents(session_id, response)

            return jsonify({
                'response': response,
                'suggestions': ['Choose country', 'Popular courses', 'Talk to advisor'],
                'type': 'initial_options'
            })

        # Handle special actions first
        if user_message.lower() == 'start over':
            return jsonify({
                'response': "Let's start fresh! How can I help you with your study abroad plans?",
                'suggestions': [
                    '🌍 Choose Country',
                    '🎓 Browse Programs',
                    '📚 Requirements',
                    '💰 Scholarships',
                    '🗣️ Talk to Advisor'
                ],
                'type': 'main_menu',
                'clear_chat': True  # Frontend will clear chat history
            })
        
        if user_message.lower() == 'no, continue with bot':
            return jsonify({
                'response': "I'm here to help! What would you like to know about studying abroad?",
                'suggestions': [
                    '🌍 Choose Country',
                    '🎓 Browse Programs',
                    '📚 Requirements',
                    '💰 Scholarships',
                    '🗣️ Talk to Advisor'
                ],
                'type': 'main_menu'
            })

        # 2. Use semantic understanding for free text (Gemini)
        semantic_result = get_semantic_response(user_message, context)
        if semantic_result['confidence'] == 'high' or semantic_result['intent'] in ['greeting', 'general_info']:
            # Log semantic response
            session_manager.log_bot_message(
                semantic_result['suggested_reply'],
                metadata={
                    'source': 'semantic',
                    'confidence': semantic_result['confidence'],
                    'intent': semantic_result['intent']
                }
            )

            return jsonify({
                'response': semantic_result['suggested_reply'],
                'suggestions': ['Choose country'] + COUNTRIES[:5] + ['Explore by field'],
                'type': 'general'
            })
        # 3. Escalate to human agent if neither RAG nor LLM is confident
        fallback_response = "I apologize, but I'm not sure about that specific query. Let me connect you with one of our human experts who can provide you with personalized assistance."

        # Log the fallback response and trigger human handoff
        session_manager.log_bot_message(fallback_response, is_fallback=True)
        escalation_success = session_manager.handle_fallback(
            fallback_response,
            reason="Bot unable to provide adequate response - low confidence"
        )

        if escalation_success:
            response = f"""{fallback_response}

🔄 **You're now in the queue for human assistance.**

A human agent will join this conversation shortly to help you with your query. Please wait a moment while we connect you.

In the meantime, you can:
- Continue asking questions (they'll be saved for the agent)
- Or wait for the agent to respond"""

            # Emit escalation message to agents
            emit_bot_message_to_agents(session_id, response)

            return jsonify({
                'response': response,
                'suggestions': ['Wait for agent', 'Ask another question', 'Start over'],
                'type': 'human_handoff_initiated',
                'escalated': True,
                'session_info': session_manager.get_session_info()
            })
        else:
            # Fallback to traditional advisor contact if escalation fails
            advisor = CUSTOMER_ADVISORS[3]  # General counselor
            response = f"""I apologize, but I'm not sure about that specific query. Would you like to speak with {advisor['name']}, our {advisor['specialization']} expert?

Contact details:
📞 Phone: {advisor['phone']}
🔧 Expertise: {advisor['specialization']}

They can provide you with personalized assistance and detailed information."""

            return jsonify({
                'response': response,
                'suggestions': ['Yes, connect me', 'No, continue with bot', 'Start over'],
                'type': 'escalation_offer',
                'advisor': advisor
            })
    except Exception as e:
        return jsonify({
            'response': f"Sorry, I encountered an error while processing your request: {e}",
            'suggestions': [],
            'type': 'text'
        })

@app.route('/chat-with-files', methods=['POST'])
def chat_with_files():
    """Handle chat messages with file uploads"""
    try:
        print(f"DEBUG: File upload request received")

        # Get session ID
        session_id = session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            print(f"DEBUG: Created new session ID: {session_id}")

        # Get message and context
        user_message = request.form.get('message', '').strip()
        context_str = request.form.get('context', '{}')
        print(f"DEBUG: User message: '{user_message}'")

        try:
            context = json.loads(context_str)
        except Exception as e:
            print(f"DEBUG: Failed to parse context: {e}")
            context = {}

        # Process uploaded files
        print(f"DEBUG: Processing files for session {session_id}")
        print(f"DEBUG: Request files: {list(request.files.keys())}")
        uploaded_files = process_uploaded_files(request.files, session_id, user_message)
        print(f"DEBUG: Processed {len(uploaded_files)} files successfully")

        # Create file summary for the message
        file_summary = ""
        if uploaded_files:
            file_names = [f['original_name'] for f in uploaded_files]
            file_summary = f"\n\n📎 Files uploaded: {', '.join(file_names)}"

        # Combine message with file info
        full_message = user_message + file_summary if user_message else f"📎 Files uploaded: {', '.join([f['original_name'] for f in uploaded_files])}"

        # Emit user message to agents (including file info)
        try:
            if socketio:
                message_data = {
                    'session_id': session_id,
                    'sender_type': 'user',
                    'sender_id': None,
                    'message_content': full_message,
                    'timestamp': datetime.utcnow().isoformat(),
                    'context': context,
                    'files': uploaded_files
                }

                print(f"DEBUG: Emitting message with {len(uploaded_files)} files to agents")
                print(f"DEBUG: Files data: {uploaded_files}")

                socketio.emit('new_message', message_data, room=session_id)
                print(f"✅ Emitted user message with {len(uploaded_files)} files to agents in session {session_id}")
        except Exception as e:
            print(f"❌ Error emitting user message with files: {e}")

        # Handle profile collection if needed
        profile_completed = session.get('profile_completed', False)
        profile_state = session.get('profile_collection_state')

        print(f"DEBUG: File upload - Profile completed: {profile_completed}, State: {profile_state}")

        # Only handle profile collection if not completed
        if not profile_completed and profile_state in ['need_name', 'selecting_country_code', 'collecting_phone', 'collecting_email']:
            print(f"DEBUG: File upload requires profile collection")
            response = handle_user_profile_collection(full_message, session_id, context)
            if response:
                return jsonify(response)
        else:
            print(f"DEBUG: File upload - Profile already completed or not needed, proceeding with file processing")

        # Process with RAG system
        try:
            # Initialize RAG system on first use if not already initialized
            global RAG, rag_initialized
            if not rag_initialized:
                print("🔄 Initializing RAG system on first use...")
                rag_initialized = initialize_rag()
                if rag_initialized:
                    print("✅ RAG system initialized successfully!")
                else:
                    print("❌ RAG system failed to initialize")

            if RAG and RAG.is_initialized:
                # Include file information in the query
                rag_query = full_message
                if uploaded_files:
                    file_info = "\n".join([f"- {f['original_name']} ({f['type'].upper()}, {f['size']} bytes)" for f in uploaded_files])
                    rag_query += f"\n\nUploaded files:\n{file_info}"

                # Get RAG results
                rag_results = RAG.search(rag_query, k=3)
                if rag_results and len(rag_results) > 0:
                    top_result = rag_results[0]
                    rag_response = top_result['answer']

                if rag_response and rag_response.strip():
                    # ✅ Only show file acknowledgment, not the RAG response content
                    if uploaded_files:
                        rag_response = f"✅ I've received your {len(uploaded_files)} file(s): {', '.join([f['original_name'] for f in uploaded_files])}."

                    # Emit bot response to agents
                    emit_bot_message_to_agents(session_id, rag_response)

                    return jsonify({
                        'response': rag_response,
                        'context': context,
                        'files_processed': len(uploaded_files),
                        'uploaded_files': uploaded_files
                    })
        except Exception as e:
            print(f"RAG system error: {e}")

        # Fallback response
        if uploaded_files:
            fallback_response = f"✅ Thank you for uploading {len(uploaded_files)} file(s): {', '.join([f['original_name'] for f in uploaded_files])}. I've received them and will review the content to better assist you."
        else:
            fallback_response = "I understand you wanted to share files with me. Please try uploading them again, and I'll be happy to help you with any questions about the content."

        if user_message:
            fallback_response += f"\n\nRegarding your message: \"{user_message}\" - I'm here to help with your study abroad questions. Could you please provide more details about what you'd like to know?"

        # Emit fallback response to agents
        emit_bot_message_to_agents(session_id, fallback_response)

        return jsonify({
            'response': fallback_response,
            'context': context,
            'files_processed': len(uploaded_files),
            'uploaded_files': uploaded_files
        })

    except Exception as e:
        print(f"Error in chat_with_files: {e}")
        return jsonify({
            'response': 'Sorry, there was an error processing your files. Please try again.',
            'error': str(e)
        }), 500

@app.route('/api/clear-session-state', methods=['POST'])
def clear_session_state():
    """Clear session state to force fresh profile collection"""
    try:
        # Clear profile collection state
        session.pop('profile_collection_state', None)
        session.pop('user_profile', None)
        session.pop('profile_completed', None)

        # Clear any other session data that might interfere
        keys_to_clear = [
            'collected_name', 'collected_phone', 'collected_email',
            'country_code', 'phone_number', 'email_address'
        ]

        for key in keys_to_clear:
            session.pop(key, None)

        print(f"DEBUG: Cleared session state for session {session.get('session_id', 'unknown')}")

        return jsonify({
            'success': True,
            'message': 'Session state cleared'
        })

    except Exception as e:
        print(f"ERROR: Failed to clear session state: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/messages/<session_id>')
def get_session_messages(session_id):
    """Get messages for a specific session"""
    try:
        # ✅ Handle null/invalid session IDs
        if not session_id or session_id in ['null', 'undefined', 'None']:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID',
                'messages': []
            }), 400

        # This endpoint is called by frontend but we're using localStorage now
        # Return empty array since we use localStorage for persistence
        return jsonify({
            'success': True,
            'messages': [],
            'note': 'Using localStorage for message persistence'
        })
    except Exception as e:
        print(f"ERROR: Failed to get messages for session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'messages': []
        }), 500

@app.route('/api/queue-status/<session_id>')
def get_queue_status(session_id):
    """Get queue status for a specific session"""
    try:
        # ✅ Handle null/invalid session IDs
        if not session_id or session_id in ['null', 'undefined', 'None']:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID',
                'in_queue': False,
                'position': None
            }), 400

        # Check if session is in queue (with error handling)
        try:
            queue_position = session_manager.get_queue_position(session_id)
            is_in_queue = queue_position is not None
        except Exception as queue_error:
            print(f"WARNING: Error checking queue position for {session_id}: {queue_error}")
            # Default to not in queue if there's an error
            queue_position = None
            is_in_queue = False

        return jsonify({
            'success': True,
            'in_queue': is_in_queue,
            'position': queue_position,
            'session_id': session_id
        })
    except Exception as e:
        print(f"ERROR: Failed to get queue status for session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'in_queue': False,
            'position': None
        }), 500

@app.route('/api/clear-profile/<session_id>', methods=['POST'])
def clear_profile_data(session_id):
    """Clear profile data for a specific session (nuclear option)"""
    try:
        if not session_id or session_id in ['null', 'undefined', 'None']:
            return jsonify({
                'success': False,
                'error': 'Invalid session ID'
            }), 400

        # Clear profile from database
        profiles_deleted = 0

        # Find and delete profiles associated with this session
        profiles = UserProfile.query.filter_by(session_id=session_id).all()
        for profile in profiles:
            db.session.delete(profile)
            profiles_deleted += 1

        # Also find profiles by persistent_user_id pattern
        persistent_user_id = f"user_{session_id[:15]}"  # Match the pattern used in create_profile
        persistent_profiles = UserProfile.query.filter_by(persistent_user_id=persistent_user_id).all()
        for profile in persistent_profiles:
            if profile not in profiles:  # Avoid double deletion
                db.session.delete(profile)
                profiles_deleted += 1

        db.session.commit()

        print(f"CLEARED: Deleted {profiles_deleted} profiles for session {session_id}")

        return jsonify({
            'success': True,
            'message': f'Cleared {profiles_deleted} profiles',
            'session_id': session_id
        })

    except Exception as e:
        print(f"ERROR: Failed to clear profile for session {session_id}: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear-all-profiles', methods=['POST'])
def clear_all_profiles():
    """Clear ALL profile data from database (nuclear option)"""
    try:
        # Delete all profiles from database
        profiles_deleted = UserProfile.query.count()
        UserProfile.query.delete()
        db.session.commit()

        print(f"NUCLEAR CLEAR: Deleted ALL {profiles_deleted} profiles from database")

        return jsonify({
            'success': True,
            'message': f'Cleared ALL {profiles_deleted} profiles from database',
            'nuclear': True
        })

    except Exception as e:
        print(f"ERROR: Failed to clear all profiles: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download-file/<int:file_id>')
def download_file(file_id):
    """Download uploaded file by ID"""
    try:
        from human_handoff.models import UploadedFile

        # Get file from database
        uploaded_file = UploadedFile.query.get_or_404(file_id)

        # Check if file exists on disk
        if not os.path.exists(uploaded_file.filepath):
            return jsonify({
                'success': False,
                'error': 'File not found on disk'
            }), 404

        # Send file for download
        return send_file(
            uploaded_file.filepath,
            as_attachment=True,
            download_name=uploaded_file.original_name,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        print(f"ERROR: Failed to download file {file_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/add-faq', methods=['GET', 'POST'])
def add_faq():
    global RAG
    success = None
    error = None
    
    if request.method == 'POST':
        try:
            # Get form data
            question = request.form.get('question')
            answer = request.form.get('answer')
            section = request.form.get('section', 'Custom FAQ')
            
            # Load existing FAQs
            with open('data/documents/education_faq.json', 'r') as f:
                data = json.load(f)
            
            # Create new FAQ entry
            new_faq = {
                'question': question,
                'answer': answer,
                'section': section,
                'page': 0,
                'document': 'Admin Added FAQ',
                'chunk_id': str(uuid.uuid4())
            }
            
            # Add to general_queries.custom_entries list
            if 'general_queries' not in data:
                data['general_queries'] = {}
            if 'custom_entries' not in data['general_queries']:
                data['general_queries']['custom_entries'] = []
            
            data['general_queries']['custom_entries'].append(new_faq)
            
            # Save updated JSON
            with open('data/documents/education_faq.json', 'w') as f:
                json.dump(data, f, indent=4)
            
            # Update embeddings
            if RAG is None:
                RAG = RAGSystem()
            
            if RAG.update_documents('data/documents/education_faq.json'):
                success = "FAQ added and embeddings updated successfully!"
            else:
                error = "Failed to update embeddings for the new FAQ"
                
        except Exception as e:
            error = f"Error saving FAQ: {e}"
            
    return render_template('add_faq.html', success=success, error=error)

@app.route('/api/user-profile', methods=['GET'])
def api_get_user_profile():
    """Get persistent user profile"""
    try:
        # Check for persistent user ID in headers
        persistent_user_id = request.headers.get('X-Persistent-User-ID')

        if persistent_user_id:
            profile = UserProfile.query.filter_by(persistent_user_id=persistent_user_id).first()
            if profile:
                # Update last used timestamp
                profile.last_used = datetime.utcnow()
                db.session.commit()

                return jsonify({
                    'exists': True,
                    'profile': {
                        'name': profile.name,
                        'phone': profile.phone,
                        'email': profile.email,
                        'persistent_user_id': profile.persistent_user_id
                    }
                })

        # Fallback: Check for existing profile by session ID
        session_id = session_manager.get_session_id()
        profile = UserProfile.query.filter_by(session_id=session_id).first()

        if profile and profile.persistent_user_id:
            # Found existing profile with persistent ID - tell frontend to save it
            return jsonify({
                'exists': True,
                'profile': {
                    'name': profile.name,
                    'phone': profile.phone,
                    'email': profile.email,
                    'persistent_user_id': profile.persistent_user_id
                },
                'should_save_persistent_id': True
            })

        return jsonify({'exists': False})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queue-status', methods=['GET'])
def api_queue_status():
    """Get current queue position and estimated wait time"""
    try:
        session_id = session_manager.get_session_id()

        # Get current session
        chat_session = ChatSession.query.filter_by(session_id=session_id).first()

        if not chat_session or not chat_session.requires_human:
            return jsonify({'in_queue': False})

        if chat_session.assigned_agent_id:
            return jsonify({
                'in_queue': False,
                'assigned_to_agent': True,
                'status': 'assigned'
            })

        # Calculate queue position
        queue_position = calculate_queue_position(session_id)
        estimated_wait_time = queue_position * 60  # 60 seconds per position

        # Update session with queue info
        chat_session.queue_position = queue_position
        chat_session.estimated_wait_time = estimated_wait_time
        db.session.commit()

        return jsonify({
            'in_queue': True,
            'queue_position': queue_position,
            'estimated_wait_time': estimated_wait_time,
            'estimated_wait_minutes': round(estimated_wait_time / 60, 1),
            'status': 'waiting'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_queue_position(session_id):
    """Calculate the position of a session in the queue"""
    try:
        # Get all pending sessions ordered by escalation time (FIFO)
        pending_sessions = ChatSession.query.filter_by(
            requires_human=True,
            status='escalated',
            assigned_agent_id=None
        ).order_by(ChatSession.escalated_at.asc()).all()

        # Find position of current session
        for i, session in enumerate(pending_sessions):
            if session.session_id == session_id:
                return i + 1  # Position is 1-based

        return 0  # Not found in queue
    except Exception as e:
        print(f"Error calculating queue position: {e}")
        return 0

# Category-specific suggestion buttons
CATEGORY_SUGGESTIONS = {
    'scholarships': ['Browse scholarships', 'Eligibility check', 'Apply now', 'Talk to advisor'],
    'admissions': ['Requirements', 'Application process', 'Document checklist', 'Talk to advisor'],
    'courses': ['Popular courses', 'Course details', 'Compare courses', 'Talk to advisor'],
    'general': ['Choose country', 'Popular courses', 'Talk to advisor']
}

def get_suggestions_for_category(category):
    """Get relevant suggestion buttons based on response category"""
    return CATEGORY_SUGGESTIONS.get(category.lower(), CATEGORY_SUGGESTIONS['general'])

if __name__ == '__main__':
    # Initialize activity tracker
    init_activity_tracker(app)

    # Initialize daily scheduler for automatic reset at 12 AM Nepal time
    init_daily_scheduler(app)

    # Use SocketIO run instead of app.run for real-time features
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)