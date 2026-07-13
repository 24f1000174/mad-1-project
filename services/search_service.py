from database.models import User, Trek, Booking
from utils.constants import ROLE_STAFF, ROLE_TREKKER, ROLE_ADMIN

class SearchService:
    """Service class providing search and filter operations."""

    @staticmethod
    def search_treks(query=None, difficulty=None, status=None, min_price=None, max_price=None):
        """Searches treks with optional filters."""
        q = Trek.query

        if query:
            q = q.filter(Trek.title.ilike(f'%{query}%'))
        if difficulty:
            q = q.filter(Trek.difficulty == difficulty)
        if status:
            q = q.filter(Trek.status == status)
        if min_price:
            try:
                q = q.filter(Trek.price >= float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                q = q.filter(Trek.price <= float(max_price))
            except ValueError:
                pass

        return q.order_by(Trek.start_date.asc()).all()

    @staticmethod
    def search_users(query=None, status=None):
        """Searches trekker accounts."""
        q = User.query.filter(User.role == ROLE_TREKKER)

        if query:
            q = q.filter(
                (User.username.ilike(f'%{query}%')) |
                (User.email.ilike(f'%{query}%'))
            )
        if status:
            q = q.filter(User.status == status)

        return q.order_by(User.created_at.desc()).all()

    @staticmethod
    def search_staff(query=None, status=None):
        """Searches staff accounts."""
        q = User.query.filter(User.role == ROLE_STAFF)

        if query:
            q = q.filter(
                (User.username.ilike(f'%{query}%')) |
                (User.email.ilike(f'%{query}%'))
            )
        if status:
            q = q.filter(User.status == status)

        return q.order_by(User.created_at.desc()).all()

    @staticmethod
    def search_bookings(query=None, status=None):
        """Searches all bookings with optional username or trek title filter."""
        q = Booking.query.join(User).join(Trek)

        if query:
            q = q.filter(
                (User.username.ilike(f'%{query}%')) |
                (Trek.title.ilike(f'%{query}%'))
            )
        if status:
            q = q.filter(Booking.status == status)

        return q.order_by(Booking.booking_date.desc()).all()
