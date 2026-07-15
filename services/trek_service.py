from datetime import datetime, date
from extensions import db
from database.models import Trek, User, Booking
from utils.constants import ROLE_STAFF, STATUS_APPROVED
from utils.helpers import log_activity

class TrekService:
    """Service class managing Treks lifecycle and assignments."""

    @staticmethod
    def create_trek(title, description, difficulty, start_date, end_date, price, max_slots, staff_id=None):
        """Creates a new Trek event.
        
        Returns:
            tuple: (Trek, None) if successful, (None, error_string) if failed.
        """
        if not title or not description or not difficulty or not start_date or not end_date or not price or not max_slots:
            return None, "All fields are required."

        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                return None, "Invalid start date format. Use YYYY-MM-DD."
                
        if isinstance(end_date, str):
            try:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                return None, "Invalid end date format. Use YYYY-MM-DD."

        if start_date >= end_date:
            return None, "Start date must be before end date."

        if start_date < date.today():
            return None, "Trek start date cannot be in the past."

        try:
            price = float(price)
            if price <= 0:
                return None, "Price must be greater than zero."
        except ValueError:
            return None, "Price must be a valid number."

        try:
            max_slots = int(max_slots)
            if max_slots <= 0:
                return None, "Maximum slots must be greater than zero."
        except ValueError:
            return None, "Maximum slots must be a valid integer."

        if staff_id:
            staff = User.query.get(staff_id)
            if not staff or staff.role != ROLE_STAFF or staff.status != STATUS_APPROVED:
                return None, "Assigned staff member must be an approved staff user."

        try:
            new_trek = Trek(
                title=title,
                description=description,
                difficulty=difficulty,
                start_date=start_date,
                end_date=end_date,
                price=price,
                max_slots=max_slots,
                available_slots=max_slots, # Initially all slots are available
                staff_id=staff_id if staff_id else None
            )
            db.session.add(new_trek)
            db.session.commit()
            return new_trek, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Database error creating trek: {str(e)}"

    @staticmethod
    def update_trek(trek_id, title, description, difficulty, start_date, end_date, price, max_slots, staff_id=None):
        """Updates trek attributes including capacity updates.
        
        Returns:
            tuple: (Trek, None) if successful, (None, error_string) if failed.
        """
        trek = Trek.query.get(trek_id)
        if not trek:
            return None, "Trek not found."

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date >= end_date:
            return None, "Start date must be before end date."

        try:
            price = float(price)
            if price <= 0:
                return None, "Price must be greater than zero."
        except ValueError:
            return None, "Price must be a valid number."

        try:
            max_slots = int(max_slots)
            if max_slots <= 0:
                return None, "Maximum slots must be greater than zero."
        except ValueError:
            return None, "Maximum slots must be a valid integer."

        booked_slots = trek.max_slots - trek.available_slots
        if max_slots < booked_slots:
            return None, f"Cannot reduce slots below the count of existing bookings ({booked_slots})."

        if staff_id:
            staff = User.query.get(staff_id)
            if not staff or staff.role != ROLE_STAFF or staff.status != STATUS_APPROVED:
                return None, "Assigned staff member must be an approved staff user."

        try:
            trek.title = title
            trek.description = description
            trek.difficulty = difficulty
            trek.start_date = start_date
            trek.end_date = end_date
            trek.price = price
            trek.max_slots = max_slots
            trek.available_slots = max_slots - booked_slots
            trek.staff_id = staff_id if staff_id else None
            
            db.session.commit()
            return trek, None
            
        except Exception as e:
            db.session.rollback()
            return None, f"Database error updating trek: {str(e)}"

    @staticmethod
    def delete_trek(trek_id):
        """Deletes a Trek. Note: this cascade deletes bookings."""
        trek = Trek.query.get(trek_id)
        if not trek:
            return False, "Trek not found."

        try:
            db.session.delete(trek)
            db.session.commit()
            return True, "Trek deleted successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Database error deleting trek: {str(e)}"

    @staticmethod
    def assign_staff(trek_id, staff_id):
        """Assigns an approved staff member to a Trek."""
        trek = Trek.query.get(trek_id)
        if not trek:
            return False, "Trek not found."

        if staff_id:
            staff = User.query.get(staff_id)
            if not staff or staff.role != ROLE_STAFF or staff.status != STATUS_APPROVED:
                return False, "User is not a valid or approved staff member."
            trek.staff_id = staff.id
        else:
            trek.staff_id = None

        try:
            db.session.commit()
            return True, "Staff assigned to trek successfully."
        except Exception as e:
            db.session.rollback()
            return False, f"Database error during staff assignment: {str(e)}"
