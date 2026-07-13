from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import user_bp
from extensions import db
from database.models import Trek, Booking, Profile, Notification
from services.booking_service import BookingService
from services.search_service import SearchService
from utils.decorators import role_required
from utils.helpers import log_activity
from utils.constants import ROLE_TREKKER, ALL_DIFFICULTIES, TREK_UPCOMING

# ------------------------------------------------------------------
#  TREKKER DASHBOARD
# ------------------------------------------------------------------

@user_bp.route('/dashboard')
@login_required
@role_required(ROLE_TREKKER)
def dashboard():
    """User dashboard showing upcoming booked treks and unread notifications."""
    bookings = BookingService.get_user_bookings(current_user.id)

    # Unread notifications
    unread_notifications = (
        Notification.query
        .filter_by(user_id=current_user.id, read_status=False)
        .order_by(Notification.created_at.desc())
        .all()
    )
    # Mark notifications as read once the dashboard is viewed
    for notif in unread_notifications:
        notif.read_status = True
    db.session.commit()

    # Only Upcoming/Started booked treks for the "active trips" card
    active_bookings = [b for b in bookings if b.status == 'Booked' and b.trek.status in ['Upcoming', 'Started']]

    return render_template('user/dashboard.html',
                           bookings=bookings,
                           active_bookings=active_bookings,
                           notifications=unread_notifications)


# ------------------------------------------------------------------
#  TREK CATALOGUE + SEARCH
# ------------------------------------------------------------------

@user_bp.route('/treks')
@login_required
@role_required(ROLE_TREKKER)
def browse_treks():
    """Public trek catalogue with search and filter support."""
    query = request.args.get('q', '')
    difficulty = request.args.get('difficulty', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    # Only show Upcoming treks to trekkers (not closed/completed/started)
    treks = SearchService.search_treks(
        query=query, difficulty=difficulty, status=TREK_UPCOMING,
        min_price=min_price, max_price=max_price
    )

    # Get IDs of treks already booked by this user (active bookings only)
    my_booking_trek_ids = set(
        b.trek_id for b in Booking.query
        .filter_by(user_id=current_user.id, status='Booked')
        .all()
    )

    return render_template('user/browse_treks.html',
                           treks=treks,
                           my_booking_trek_ids=my_booking_trek_ids,
                           difficulties=ALL_DIFFICULTIES,
                           filters={'q': query, 'difficulty': difficulty,
                                    'min_price': min_price, 'max_price': max_price})


@user_bp.route('/treks/<int:trek_id>')
@login_required
@role_required(ROLE_TREKKER)
def trek_detail(trek_id):
    """Shows full details of a specific trek."""
    trek = Trek.query.get_or_404(trek_id)

    # Check if user has already booked this trek
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek_id, status='Booked'
    ).first()

    return render_template('user/trek_detail.html', trek=trek,
                           existing_booking=existing_booking)


# ------------------------------------------------------------------
#  BOOKING
# ------------------------------------------------------------------

@user_bp.route('/treks/<int:trek_id>/book', methods=['POST'])
@login_required
@role_required(ROLE_TREKKER)
def book_trek(trek_id):
    """Books a trek for the currently logged-in trekker."""
    booking, error = BookingService.book_trek(current_user.id, trek_id)
    if error:
        flash(error, 'danger')
    else:
        flash(f"Trek booked successfully! Your booking ID is #{booking.id}.", 'success')
    return redirect(url_for('user.trek_detail', trek_id=trek_id))


@user_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@login_required
@role_required(ROLE_TREKKER)
def cancel_booking(booking_id):
    """Cancels an active booking if permitted."""
    success, error = BookingService.cancel_booking(current_user.id, booking_id)
    if success:
        flash("Your booking has been cancelled and the slot has been released.", 'success')
    else:
        flash(error, 'danger')
    return redirect(url_for('user.booking_history'))


# ------------------------------------------------------------------
#  BOOKING HISTORY
# ------------------------------------------------------------------

@user_bp.route('/bookings')
@login_required
@role_required(ROLE_TREKKER)
def booking_history():
    """Displays the full booking history for the current user."""
    bookings = BookingService.get_user_bookings(current_user.id)
    return render_template('user/booking_history.html', bookings=bookings)


# ------------------------------------------------------------------
#  PROFILE MANAGEMENT
# ------------------------------------------------------------------

@user_bp.route('/profile')
@login_required
@role_required(ROLE_TREKKER)
def profile():
    """Shows the user's profile page."""
    return render_template('user/profile.html', user=current_user)


@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@role_required(ROLE_TREKKER)
def edit_profile():
    """Allows the user to update profile details."""
    user_profile = current_user.profile

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        address = request.form.get('address', '').strip()
        emergency_contact = request.form.get('emergency_contact', '').strip()
        medical_conditions = request.form.get('medical_conditions', '').strip()

        if not full_name:
            flash("Full name cannot be empty.", "danger")
            return render_template('user/edit_profile.html', user=current_user)

        # Create profile if it doesn't exist (safety guard)
        if not user_profile:
            from database.models import Profile as ProfileModel
            user_profile = ProfileModel(user_id=current_user.id)
            db.session.add(user_profile)

        user_profile.full_name = full_name
        user_profile.phone = phone
        user_profile.address = address
        user_profile.emergency_contact = emergency_contact
        user_profile.medical_conditions = medical_conditions

        db.session.commit()
        log_activity(current_user.id, 'Profile Updated', "User updated their profile information.")
        flash("Your profile has been updated successfully.", 'success')
        return redirect(url_for('user.profile'))

    return render_template('user/edit_profile.html', user=current_user)
