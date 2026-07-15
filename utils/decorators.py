from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user
from utils.constants import ROLE_STAFF, STATUS_APPROVED, STATUS_PENDING

def role_required(roles):
    """Decorator to restrict view access to specific user roles.
    
    Args:
        roles (str or list): Role string or list of permitted roles (e.g. 'admin', ['admin', 'staff']).
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                abort(403)

            if current_user.role == ROLE_STAFF:
                if current_user.status == STATUS_PENDING:
                    return redirect(url_for('auth.pending_approval'))
                elif current_user.status != STATUS_APPROVED:
                    flash("Your staff account is not approved or is blacklisted.", "danger")
                    return redirect(url_for('auth.login'))

            if current_user.is_blacklisted:
                flash("Your account has been blacklisted. Access denied.", "danger")
                return redirect(url_for('auth.login'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
