from extensions import db
from database.models import Booking, Trek
from utils.constants import BOOKING_ACTIVE, BOOKING_CANCELLED, TREK_UPCOMING, TREK_STARTED, TREK_COMPLETED, TREK_CLOSED
from utils.helpers import log_activity, create_notification

class BookingService:
    """Service class managing all trek booking business logic."""

    @staticmethod
    def book_trek(user_id, trek_id):
        """Books a trek for a user after validating all business rules.
        
        Returns:
            tuple: (Booking, None) on success, (None, error_string) on failure.
        """
        trek = Trek.query.get(trek_id)
        if not trek:
            return None, "Trek not found."

        # Rule: Cannot book a closed trek
        if trek.status == TREK_CLOSED:
            return None, "This trek is closed and no longer accepting bookings."

        # Rule: Cannot book a completed trek
        if trek.status == TREK_COMPLETED:
            return None, "This trek has already been completed."

        # Rule: Cannot book a started trek
        if trek.status == TREK_STARTED:
            return None, "This trek has already started and is no longer accepting bookings."

        # Rule: Prevent overbooking
        if trek.available_slots <= 0:
            return None, "Sorry, this trek is fully booked with no available slots."

        # Rule: Prevent duplicate booking for the same trek
        existing = Booking.query.filter_by(
            user_id=user_id, trek_id=trek_id, status=BOOKING_ACTIVE
        ).first()
        if existing:
            return None, "You have already booked this trek."

        try:
            booking = Booking(
                user_id=user_id,
                trek_id=trek_id,
                status=BOOKING_ACTIVE,
                price_paid=trek.price
            )
            trek.available_slots -= 1  # Decrement available slots atomically
            db.session.add(booking)
            db.session.commit()

            log_activity(user_id, 'Trek Booked', f"Booked trek '{trek.title}' for Rs. {trek.price}")
            create_notification(user_id, f"Your booking for '{trek.title}' is confirmed! Price paid: Rs. {trek.price:.2f}")
            return booking, None

        except Exception as e:
            db.session.rollback()
            return None, f"Database error during booking: {str(e)}"

    @staticmethod
    def cancel_booking(user_id, booking_id):
        """Cancels an active booking if cancellation is permitted.
        
        Cancellation is only allowed while the trek status is 'Upcoming'.
        
        Returns:
            tuple: (True, None) on success, (False, error_string) on failure.
        """
        booking = Booking.query.filter_by(id=booking_id, user_id=user_id).first()
        if not booking:
            return False, "Booking not found or does not belong to you."

        if booking.status == BOOKING_CANCELLED:
            return False, "This booking is already cancelled."

        trek = Trek.query.get(booking.trek_id)
        if not trek:
            return False, "Associated trek not found."

        # Rule: Cannot cancel after the trek has started
        if trek.status in [TREK_STARTED, TREK_COMPLETED]:
            return False, "Cancellation is not allowed once the trek has started or is completed."

        try:
            booking.status = BOOKING_CANCELLED
            trek.available_slots += 1  # Restore the slot
            db.session.commit()

            log_activity(user_id, 'Booking Cancelled', f"Cancelled booking for trek '{trek.title}'.")
            create_notification(user_id, f"Your booking for '{trek.title}' has been cancelled. The slot has been released.")
            return True, None

        except Exception as e:
            db.session.rollback()
            return False, f"Database error during cancellation: {str(e)}"

    @staticmethod
    def get_user_bookings(user_id):
        """Returns all bookings for a user ordered by most recent first."""
        return (
            Booking.query
            .filter_by(user_id=user_id)
            .join(Trek)
            .order_by(Booking.booking_date.desc())
            .all()
        )
