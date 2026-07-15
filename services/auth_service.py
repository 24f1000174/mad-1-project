from extensions import db
from database.models import User, Profile
from utils.constants import ROLE_STAFF, ROLE_TREKKER, STATUS_APPROVED, STATUS_PENDING, STATUS_BLACKLISTED
from utils.validators import validate_email, validate_password_strength, validate_username
from utils.helpers import log_activity

class AuthService:
    """Service class encapsulating authentication-related business logic."""

    @staticmethod
    def register_user(username, email, password, role, full_name="", phone="", address=""):
        """Registers a new User and corresponding Profile.
        
        Returns:
            tuple: (User, None) if successful, (None, error_string) if failed.
        """
        if not username or not email or not password or not role:
            return None, "All fields are required."
            
        if not validate_username(username):
            return None, "Username must be alphanumeric and between 3 and 20 characters."
            
        if not validate_email(email):
            return None, "Please provide a valid email address."
            
        if not validate_password_strength(password):
            return None, "Password must be at least 6 characters long."
            
        if role not in [ROLE_STAFF, ROLE_TREKKER]:
            return None, "Invalid role choice."

        if User.query.filter_by(username=username).first():
            return None, "Username is already taken."
            
        if User.query.filter_by(email=email).first():
            return None, "Email is already registered."

        status = STATUS_PENDING if role == ROLE_STAFF else STATUS_APPROVED

        try:
            new_user = User(
                username=username,
                email=email,
                role=role,
                status=status
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.flush() # Get new_user.id

            new_profile = Profile(
                user_id=new_user.id,
                full_name=full_name,
                phone=phone,
                address=address
            )
            db.session.add(new_profile)
            db.session.commit()
            
            log_activity(new_user.id, 'User Registration', f"Registered as {role} with status {status}.")
            return new_user, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Database error during registration: {str(e)}"

    @staticmethod
    def authenticate_user(username_or_email, password):
        """Authenticates a user by username or email.
        
        Returns:
            tuple: (User, None) if successful, (None, error_string) if failed.
        """
        if not username_or_email or not password:
            return None, "Username/Email and Password are required."

        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        
        if not user or not user.check_password(password):
            return None, "Invalid username/email or password."

        if user.status == STATUS_BLACKLISTED:
            return None, "Your account has been blacklisted. Access is denied."

        return user, None
