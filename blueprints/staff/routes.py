from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import staff_bp
from extensions import db
from database.models import Trek, Booking, User
from utils.decorators import role_required
from utils.helpers import log_activity, create_notification
from utils.constants import (
    ROLE_STAFF, TREK_UPCOMING, TREK_STARTED, TREK_COMPLETED, TREK_CLOSED
)

# ------------------------------------------------------------------
#  STAFF DASHBOARD
# ------------------------------------------------------------------

@staff_bp.route('/dashboard')
@login_required
@role_required(ROLE_STAFF)
def dashboard():
    """Shows all treks assigned to the currently logged-in staff member."""
    assigned_treks = Trek.query.filter_by(staff_id=current_user.id).order_by(Trek.start_date.asc()).all()
    return render_template('staff/dashboard.html', treks=assigned_treks)


# ------------------------------------------------------------------
#  TREK DETAIL + PARTICIPANTS
# ------------------------------------------------------------------

@staff_bp.route('/treks/<int:trek_id>')
@login_required
@role_required(ROLE_STAFF)
def trek_detail(trek_id):
    """Shows details of an assigned trek including its participant list."""
    trek = Trek.query.get_or_404(trek_id)

    # Staff may only view their own assigned trek
    if trek.staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for('staff.dashboard'))

    # Fetch active bookings (not cancelled) with eager-loaded user data
    participants = (
        Booking.query
        .filter_by(trek_id=trek_id, status='Booked')
        .join(User)
        .all()
    )
    return render_template('staff/trek_detail.html', trek=trek, participants=participants)


# ------------------------------------------------------------------
#  SLOT MANAGEMENT
# ------------------------------------------------------------------

@staff_bp.route('/treks/<int:trek_id>/update-slots', methods=['POST'])
@login_required
@role_required(ROLE_STAFF)
def update_slots(trek_id):
    """Allows staff to manually adjust available slot count for their assigned trek."""
    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for('staff.dashboard'))

    if trek.status in [TREK_COMPLETED, TREK_CLOSED]:
        flash("Cannot update slots for a completed or closed trek.", "warning")
        return redirect(url_for('staff.trek_detail', trek_id=trek_id))

    try:
        new_slots = int(request.form.get('available_slots', 0))
    except ValueError:
        flash("Invalid slot count provided.", "danger")
        return redirect(url_for('staff.trek_detail', trek_id=trek_id))

    # available slots cannot exceed max_slots
    if new_slots < 0 or new_slots > trek.max_slots:
        flash(f"Available slots must be between 0 and {trek.max_slots}.", "warning")
        return redirect(url_for('staff.trek_detail', trek_id=trek_id))

    # available slots cannot be set below the remaining active bookings
    booked_count = Booking.query.filter_by(trek_id=trek_id, status='Booked').count()
    if new_slots + booked_count > trek.max_slots:
        flash(f"Cannot set {new_slots} available slots; {booked_count} slots are already booked.", "warning")
        return redirect(url_for('staff.trek_detail', trek_id=trek_id))

    trek.available_slots = new_slots
    db.session.commit()
    log_activity(current_user.id, 'Slots Updated',
                 f"Staff updated available slots for trek '{trek.title}' to {new_slots}.")
    flash(f"Available slots updated to {new_slots}.", "success")
    return redirect(url_for('staff.trek_detail', trek_id=trek_id))


# ------------------------------------------------------------------
#  TREK STATUS MANAGEMENT
# ------------------------------------------------------------------

@staff_bp.route('/treks/<int:trek_id>/mark-started', methods=['POST'])
@login_required
@role_required(ROLE_STAFF)
def mark_started(trek_id):
    """Staff marks their assigned trek as Started."""
    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for('staff.dashboard'))

    if trek.status != TREK_UPCOMING:
        flash("Only an 'Upcoming' trek can be marked as Started.", "warning")
        return redirect(url_for('staff.trek_detail', trek_id=trek_id))

    trek.status = TREK_STARTED
    db.session.commit()

    # Notify all booked participants
    active_bookings = Booking.query.filter_by(trek_id=trek_id, status='Booked').all()
    for booking in active_bookings:
        create_notification(booking.user_id,
                            f"Your trek '{trek.title}' has started! Have a great adventure.")

    log_activity(current_user.id, 'Trek Started', f"Marked trek '{trek.title}' as Started.")
    flash(f"Trek '{trek.title}' is now marked as Started.", "success")
    return redirect(url_for('staff.trek_detail', trek_id=trek_id))


@staff_bp.route('/treks/<int:trek_id>/mark-completed', methods=['POST'])
@login_required
@role_required(ROLE_STAFF)
def mark_completed(trek_id):
    """Staff marks their assigned trek as Completed."""
    trek = Trek.query.get_or_404(trek_id)

    if trek.staff_id != current_user.id:
        flash("You are not assigned to this trek.", "danger")
        return redirect(url_for('staff.dashboard'))

    if trek.status != TREK_STARTED:
        flash("Only a 'Started' trek can be marked as Completed.", "warning")
        return redirect(url_for('staff.trek_detail', trek_id=trek_id))

    trek.status = TREK_COMPLETED
    db.session.commit()

    # Notify all participants the trek is completed
    active_bookings = Booking.query.filter_by(trek_id=trek_id, status='Booked').all()
    for booking in active_bookings:
        create_notification(booking.user_id,
                            f"Your trek '{trek.title}' has been completed. Hope you enjoyed it!")

    log_activity(current_user.id, 'Trek Completed', f"Marked trek '{trek.title}' as Completed.")
    flash(f"Trek '{trek.title}' is now marked as Completed.", "success")
    return redirect(url_for('staff.trek_detail', trek_id=trek_id))
