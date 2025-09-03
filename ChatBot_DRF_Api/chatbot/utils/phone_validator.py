# chatbot/utils/phone_validator.py
"""
Phone number validation utilities
Based on the Flask reference implementation
"""
import re

def validate_nepali_phone(phone):
    """
    Validate Nepali mobile phone number
    
    Returns:
        dict: {
            'valid': bool,
            'message': str,
            'provider': str or None
        }
    """
    if not phone:
        return {
            'valid': False,
            'message': 'Phone number is required.',
            'provider': None
        }
    
    # Remove any spaces, hyphens, or other non-digit characters
    clean_phone = re.sub(r'\D', '', phone)
    
    # Check if exactly 10 digits
    if len(clean_phone) != 10:
        return {
            'valid': False,
            'message': f'Phone number must be exactly 10 digits. You entered {len(clean_phone)} digits.',
            'provider': None
        }
    
    # Check valid prefixes
    valid_prefixes = {
        '984': 'NTC',
        '985': 'NTC',
        '986': 'NTC',
        '974': 'NTC',
        '975': 'NTC',
        '976': 'NTC',
        '980': 'Ncell',
        '981': 'Ncell', 
        '982': 'Ncell',
        '970': 'Ncell',
        '971': 'Ncell',
        '972': 'Ncell'
    }
    
    prefix = clean_phone[:3]
    
    if prefix in valid_prefixes:
        return {
            'valid': True,
            'message': f'Valid Nepali mobile number.',
            'provider': valid_prefixes[prefix]
        }
    else:
        return {
            'valid': False,
            'message': f'Invalid prefix "{prefix}". Valid prefixes are: {", ".join(valid_prefixes.keys())}',
            'provider': None
        }

def validate_phone_number(phone, country_code):
    """Validate phone number with country code"""
    if not phone or not phone.strip():
        return False, "Phone number is required"

    # Special handling for Nepal (+977)
    if country_code == '+977':
        clean_phone = re.sub(r'[^\d+]', '', phone.strip())
        
        # Remove country code if present
        if clean_phone.startswith('+977'):
            clean_phone = clean_phone[4:]
        elif clean_phone.startswith('977'):
            clean_phone = clean_phone[3:]

        result = validate_nepali_phone(clean_phone)
        if result['valid']:
            return True, f"✅ {result['message']} (Provider: {result['provider']})"
        else:
            return False, f"❌ {result['message']}"

    # General validation for other countries
    clean_phone = re.sub(r'[^\d+]', '', phone.strip())

    if clean_phone.startswith(country_code):
        number_without_code = clean_phone[len(country_code):]
    elif clean_phone.startswith(country_code.replace('+', '')):
        number_without_code = clean_phone[len(country_code.replace('+', '')):]
    else:
        number_without_code = clean_phone

    # Remove leading zeros
    number_without_code = number_without_code.lstrip('0')

    # Basic length validation
    if len(number_without_code) < 6 or len(number_without_code) > 15:
        return False, f"Phone number should be between 6-15 digits (you entered {len(number_without_code)} digits)"

    # Check if it contains only digits
    if not number_without_code.isdigit():
        return False, "Phone number should contain only digits"

    return True, ""

def validate_name(name):
    """Validate user name input"""
    if not name or len(name.strip()) < 2:
        return False, "Name must be at least 2 characters long"
    if len(name.strip()) > 100:
        return False, "Name must be less than 100 characters"
    if not re.match(r'^[a-zA-Z\s\-\.\']+$', name.strip()):
        return False, "Name can only contain letters, spaces, hyphens, dots, and apostrophes"
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
