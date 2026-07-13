from flask import render_template, redirect, url_for
from flask_login import current_user
from . import common_bp

@common_bp.route('/')
def index():
    """Landing page — redirects authenticated users to their dashboard."""
    if current_user.is_authenticated:
        from utils.constants import ROLE_ADMIN, ROLE_STAFF
        if current_user.role == ROLE_ADMIN:
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == ROLE_STAFF:
            return redirect(url_for('staff.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    return redirect(url_for('auth.login'))
