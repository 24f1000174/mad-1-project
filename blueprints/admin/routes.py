from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import admin_bp
from extensions import db
from database.models import User, Trek, Booking, ActivityLog, Profile
from services.trek_service import TrekService
from services.search_service import SearchService
from utils.decorators import role_required
from utils.helpers import log_activity, create_notification
from utils.constants import (
    ROLE_ADMIN, ROLE_STAFF, ROLE_TREKKER,
    STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED, STATUS_BLACKLISTED,
    ALL_DIFFICULTIES, ALL_TREK_STATUSES
)

# ------------------------------------------------------------------
#  DASHBOARD
# ------------------------------------------------------------------

@admin_bp.route('/dashboard')
@login_required
@role_required(ROLE_ADMIN)
def dashboard():
    """Admin dashboard with aggregate statistics."""
    stats = {
        'total_treks': Trek.query.count(),
        'upcoming_treks': Trek.query.filter_by(status='Upcoming').count(),
        'active_treks': Trek.query.filter_by(status='Started').count(),
        'completed_treks': Trek.query.filter_by(status='Completed').count(),
        'total_users': User.query.filter_by(role=ROLE_TREKKER).count(),
        'total_staff': User.query.filter_by(role=ROLE_STAFF).count(),
        'pending_staff': User.query.filter_by(role=ROLE_STAFF, status=STATUS_PENDING).count(),
        'total_bookings': Booking.query.count(),
        'active_bookings': Booking.query.filter_by(status='Booked').count(),
    }
    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
    recent_logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_bookings=recent_bookings, recent_logs=recent_logs)


# ------------------------------------------------------------------
#  TREK MANAGEMENT
# ------------------------------------------------------------------

@admin_bp.route('/treks')
@login_required
@role_required(ROLE_ADMIN)
def treks():
    """Lists all treks with search and filter support."""
    query = request.args.get('q', '')
    difficulty = request.args.get('difficulty', '')
    status = request.args.get('status', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    trek_list = SearchService.search_treks(
        query=query, difficulty=difficulty, status=status,
        min_price=min_price, max_price=max_price
    )
    approved_staff = User.query.filter_by(role=ROLE_STAFF, status=STATUS_APPROVED).all()
    return render_template('admin/treks.html', treks=trek_list,
                           approved_staff=approved_staff,
                           difficulties=ALL_DIFFICULTIES, statuses=ALL_TREK_STATUSES,
                           filters={'q': query, 'difficulty': difficulty, 'status': status,
                                    'min_price': min_price, 'max_price': max_price})


@admin_bp.route('/treks/create', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN)
def create_trek():
    """Creates a new trek."""
    approved_staff = User.query.filter_by(role=ROLE_STAFF, status=STATUS_APPROVED).all()
    if request.method == 'POST':
        staff_id = request.form.get('staff_id') or None
        if staff_id:
            staff_id = int(staff_id)

        trek, error = TrekService.create_trek(
            title=request.form.get('title'),
            description=request.form.get('description'),
            difficulty=request.form.get('difficulty'),
            start_date=request.form.get('start_date'),
            end_date=request.form.get('end_date'),
            price=request.form.get('price'),
            max_slots=request.form.get('max_slots'),
            staff_id=staff_id
        )
        if error:
            flash(error, 'danger')
        else:
            log_activity(current_user.id, 'Trek Created', f"Created trek: {trek.title}")
            flash(f'Trek "{trek.title}" created successfully!', 'success')
            return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=None,
                           approved_staff=approved_staff, difficulties=ALL_DIFFICULTIES, mode='create')


@admin_bp.route('/treks/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_ADMIN)
def edit_trek(trek_id):
    """Edits an existing trek."""
    trek = Trek.query.get_or_404(trek_id)
    approved_staff = User.query.filter_by(role=ROLE_STAFF, status=STATUS_APPROVED).all()

    if request.method == 'POST':
        staff_id = request.form.get('staff_id') or None
        if staff_id:
            staff_id = int(staff_id)

        updated_trek, error = TrekService.update_trek(
            trek_id=trek_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            difficulty=request.form.get('difficulty'),
            start_date=request.form.get('start_date'),
            end_date=request.form.get('end_date'),
            price=request.form.get('price'),
            max_slots=request.form.get('max_slots'),
            staff_id=staff_id
        )
        if error:
            flash(error, 'danger')
        else:
            log_activity(current_user.id, 'Trek Updated', f"Updated trek: {updated_trek.title}")
            flash(f'Trek "{updated_trek.title}" updated successfully!', 'success')
            return redirect(url_for('admin.treks'))

    return render_template('admin/trek_form.html', trek=trek,
                           approved_staff=approved_staff, difficulties=ALL_DIFFICULTIES, mode='edit')


@admin_bp.route('/treks/<int:trek_id>/delete', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN)
def delete_trek(trek_id):
    """Deletes a trek (and its bookings via cascade)."""
    trek = Trek.query.get_or_404(trek_id)
    title = trek.title
    success, message = TrekService.delete_trek(trek_id)
    if success:
        log_activity(current_user.id, 'Trek Deleted', f"Deleted trek: {title}")
        flash(f'Trek "{title}" has been deleted.', 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.treks'))


@admin_bp.route('/treks/<int:trek_id>/assign-staff', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN)
def assign_staff(trek_id):
    """Assigns staff to a trek."""
    staff_id = request.form.get('staff_id') or None
    if staff_id:
        staff_id = int(staff_id)
    success, message = TrekService.assign_staff(trek_id, staff_id)
    if success:
        log_activity(current_user.id, 'Staff Assigned', f"Assigned staff_id={staff_id} to trek_id={trek_id}")
        flash(message, 'success')
    else:
        flash(message, 'danger')
    return redirect(url_for('admin.treks'))


# ------------------------------------------------------------------
#  STAFF MANAGEMENT
# ------------------------------------------------------------------

@admin_bp.route('/staff')
@login_required
@role_required(ROLE_ADMIN)
def staff_list():
    """Lists all staff with search and status filter."""
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    staff_members = SearchService.search_staff(query=query, status=status)
    return render_template('admin/staff_list.html', staff_members=staff_members,
                           filters={'q': query, 'status': status})


@admin_bp.route('/staff/<int:user_id>/approve', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN)
def approve_staff(user_id):
    """Approves a pending staff application."""
    staff = User.query.get_or_404(user_id)
    if staff.role != ROLE_STAFF:
        flash("This user is not a staff member.", 'danger')
        return redirect(url_for('admin.staff_list'))

    staff.status = STATUS_APPROVED
    db.session.commit()
    create_notification(staff.id, "Your staff application has been approved! You can now log in.")
    log_activity(current_user.id, 'Staff Approved', f"Approved staff: {staff.username}")
    flash(f'Staff member "{staff.username}" has been approved.', 'success')
    return redirect(url_for('admin.staff_list'))


@admin_bp.route('/staff/<int:user_id>/reject', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN)
def reject_staff(user_id):
    """Rejects a pending staff application."""
    staff = User.query.get_or_404(user_id)
    if staff.role != ROLE_STAFF:
        flash("This user is not a staff member.", 'danger')
        return redirect(url_for('admin.staff_list'))

    staff.status = STATUS_REJECTED
    db.session.commit()
    create_notification(staff.id, "Your staff application has been rejected by the administrator.")
    log_activity(current_user.id, 'Staff Rejected', f"Rejected staff: {staff.username}")
    flash(f'Staff member "{staff.username}" has been rejected.', 'warning')
    return redirect(url_for('admin.staff_list'))


@admin_bp.route('/staff/<int:user_id>/blacklist', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN)
def blacklist_staff(user_id):
    """Blacklists a staff member."""
    staff = User.query.get_or_404(user_id)
    if staff.role != ROLE_STAFF:
        flash("This user is not a staff member.", 'danger')
        return redirect(url_for('admin.staff_list'))

    staff.status = STATUS_BLACKLISTED
    db.session.commit()
    log_activity(current_user.id, 'Staff Blacklisted', f"Blacklisted staff: {staff.username}")
    flash(f'Staff member "{staff.username}" has been blacklisted.', 'warning')
    return redirect(url_for('admin.staff_list'))


# ------------------------------------------------------------------
#  USER MANAGEMENT
# ------------------------------------------------------------------

@admin_bp.route('/users')
@login_required
@role_required(ROLE_ADMIN)
def users_list():
    """Lists all trekker accounts with search and filter."""
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    users = SearchService.search_users(query=query, status=status)
    return render_template('admin/users_list.html', users=users,
                           filters={'q': query, 'status': status})


@admin_bp.route('/users/<int:user_id>/blacklist', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN)
def blacklist_user(user_id):
    """Blacklists a trekker account."""
    user = User.query.get_or_404(user_id)
    if user.role != ROLE_TREKKER:
        flash("Only trekker accounts can be blacklisted here.", 'danger')
        return redirect(url_for('admin.users_list'))

    user.status = STATUS_BLACKLISTED
    db.session.commit()
    log_activity(current_user.id, 'User Blacklisted', f"Blacklisted user: {user.username}")
    flash(f'User "{user.username}" has been blacklisted.', 'warning')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/unblacklist', methods=['POST'])
@login_required
@role_required(ROLE_ADMIN)
def unblacklist_user(user_id):
    """Removes a trekker from the blacklist."""
    user = User.query.get_or_404(user_id)
    user.status = STATUS_APPROVED
    db.session.commit()
    log_activity(current_user.id, 'User Unblacklisted', f"Restored user: {user.username}")
    flash(f'User "{user.username}" has been restored.', 'success')
    return redirect(url_for('admin.users_list'))


# ------------------------------------------------------------------
#  BOOKINGS OVERVIEW
# ------------------------------------------------------------------

@admin_bp.route('/bookings')
@login_required
@role_required(ROLE_ADMIN)
def all_bookings():
    """Shows all bookings with search and status filter."""
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    bookings = SearchService.search_bookings(query=query, status=status)
    return render_template('admin/bookings.html', bookings=bookings,
                           filters={'q': query, 'status': status})


# ------------------------------------------------------------------
#  ACTIVITY LOGS (Historical Data)
# ------------------------------------------------------------------

@admin_bp.route('/logs')
@login_required
@role_required(ROLE_ADMIN)
def activity_logs():
    """Shows recent activity logs sorted by newest first."""
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
    return render_template('admin/activity_logs.html', logs=logs)
