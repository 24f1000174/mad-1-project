import re

def validate_email(email):
    """Simple regex email validator."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def validate_password_strength(password):
    """Enforces basic strength constraints (min 6 characters)."""
    return len(password) >= 6

def validate_username(username):
    """Enforces alphanumeric usernames between 3 and 20 characters."""
    return len(username) >= 3 and len(username) <= 20 and username.isalnum()
