import re

def validate_registration(data):
    errors = []
    
    # Check required fields
    required_fields = ['username', 'email', 'name', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"{field} is required")
    
    if not errors:
        # Username validation
        if len(data['username']) < 3:
            errors.append("Username must be at least 3 characters long")
            
        # Email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            errors.append("Invalid email format")
            
        # Password validation
        if len(data['password']) < 6:
            errors.append("Password must be at least 6 characters long")
            
    return errors
