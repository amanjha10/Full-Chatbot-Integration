"""
Nepali Phone Number Validation Module
Validates Nepali mobile numbers according to standard formats
"""

import re

def validate_nepali_phone(phone):
    """
    Validate Nepali mobile phone number
    
    Rules:
    - Must be exactly 10 digits long
    - Must start with valid prefixes:
      * NTC: 984, 985, 986, 974, 975, 976
      * Ncell: 980, 981, 982, 970, 971, 972
    - Must only contain digits
    
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
    
    if prefix not in valid_prefixes:
        return {
            'valid': False,
            'message': f'Invalid phone number prefix "{prefix}". Valid prefixes are: {", ".join(sorted(valid_prefixes.keys()))}',
            'provider': None
        }
    
    return {
        'valid': True,
        'message': f'Valid {valid_prefixes[prefix]} number.',
        'provider': valid_prefixes[prefix],
        'formatted_number': clean_phone
    }

def format_nepali_phone(phone):
    """Format a valid Nepali phone number for display"""
    clean_phone = re.sub(r'\D', '', phone)
    if len(clean_phone) == 10:
        return f"{clean_phone[:3]}-{clean_phone[3:6]}-{clean_phone[6:]}"
    return phone

# Test function
if __name__ == '__main__':
    test_numbers = [
        '9801234567',  # Valid Ncell
        '9841234567',  # Valid NTC
        '9621234567',  # Valid Smart Cell
        '9771234567',  # Invalid prefix
        '98012345',    # Too short
        '98012345678', # Too long
        '980-123-4567', # With formatting
        'abc1234567',  # Invalid characters
    ]
    
    print("Testing Nepali Phone Number Validation:")
    print("=" * 50)
    
    for number in test_numbers:
        result = validate_nepali_phone(number)
        status = "✓" if result['valid'] else "✗"
        print(f"{status} {number:12} → {result['message']}")
        if result['valid']:
            print(f"    Provider: {result['provider']}")
            print(f"    Formatted: {format_nepali_phone(number)}")
        print()
