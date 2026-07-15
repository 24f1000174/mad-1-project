from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from services.auth_service import AuthService
from utils.constants import ROLE_ADMIN, ROLE_STAFF, ROLE_TREKKER, STATUS_PENDING
from utils.helpers import log_activity

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Authenticates and logs in a user."""
    if current_user.is_authenticated:
        return redirect_role_dashboard(current_user)

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user, error = AuthService.authenticate_user(username_or_email, password)
        if error:
            flash(error, 'danger')
            return render_template('auth/login.html')

        if user.role == ROLE_STAFF and user.status == STATUS_PENDING:
            return redirect(url_for('auth.pending_approval'))

        login_user(user, remember=remember)
        log_activity(user.id, 'User Login', f"Logged in successfully from session.")
        flash(f"Welcome back, {user.username}!", 'success')
        return redirect_role_dashboard(user)

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registers a new User account (Staff or Trekker)."""
    if current_user.is_authenticated:
        return redirect_role_dashboard(current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        full_name = request.form.get('full_name', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')

        user, error = AuthService.register_user(
            username=username,
            email=email,
            password=password,
            role=role,
            full_name=full_name,
            phone=phone,
            address=address
        )

        if error:
            flash(error, 'danger')
            return render_template('auth/register.html')

        if role == ROLE_STAFF:
            flash("Registration successful! Please wait for Admin approval before logging in.", "warning")
            return redirect(url_for('auth.pending_approval'))
        else:
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logs out current user session."""
    user_id = current_user.id
    username = current_user.username
    logout_user()
    log_activity(user_id, 'User Logout', f"Logged out session for user {username}.")
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/pending-approval')
def pending_approval():
    """Informs pending staff users they must wait for admin authorization."""
    return render_template('auth/pending_approval.html')


def redirect_role_dashboard(user):
    """Helper to route user to respective role dashboard."""
    if user.role == ROLE_ADMIN:
        return redirect(url_for('admin.dashboard'))
    elif user.role == ROLE_STAFF:
        return redirect(url_for('staff.dashboard'))
    else:
        return redirect(url_for('user.dashboard'))
