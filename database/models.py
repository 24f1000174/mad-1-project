from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager

class User(db.Model, UserMixin):
    """User model representing authentication accounts for Admin, Staff, and Trekkers."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='trekker')  # 'admin', 'staff', 'trekker'
    status = db.Column(db.String(20), nullable=False, default='approved')  # 'pending', 'approved', 'rejected', 'blacklisted'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade="all, delete-orphan")
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True, foreign_keys='Trek.staff_id')
    notifications = db.relationship('Notification', backref='recipient', lazy=True, cascade="all, delete-orphan")
    activity_logs = db.relationship('ActivityLog', backref='actor', lazy=True)

    def set_password(self, password):
        """Hashes password and stores password_hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifies clear text password against stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_blacklisted(self):
        return self.status == 'blacklisted'

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_staff(self):
        return self.role == 'staff'

    @property
    def is_trekker(self):
        return self.role == 'trekker'

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Profile(db.Model):
    """Profile model containing personal details for users."""
    __tablename__ = 'profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(100), nullable=True)
    medical_conditions = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Profile user_id={self.user_id} full_name={self.full_name}>"


class Trek(db.Model):
    """Trek model representing single trekking events."""
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # 'Easy', 'Moderate', 'Hard', 'Challenging'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)
    max_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Upcoming')  # 'Upcoming', 'Started', 'Completed', 'Closed'
    staff_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    bookings = db.relationship('Booking', backref='trek', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Trek {self.title} ({self.status})>"


class Booking(db.Model):
    """Booking model recording user trek bookings."""
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Booked')  # 'Booked', 'Cancelled'
    price_paid = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Booking user_id={self.user_id} trek_id={self.trek_id} status={self.status}>"


class Notification(db.Model):
    """Notification model for user alerts."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read_status = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Notification user_id={self.user_id} read={self.read_status}>"


class ActivityLog(db.Model):
    """ActivityLog model capturing administrative actions or audit records."""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ActivityLog action={self.action} user_id={self.user_id}>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
