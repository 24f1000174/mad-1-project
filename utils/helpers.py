from extensions import db
from database.models import ActivityLog, Notification

def log_activity(user_id, action, details=None):
    """Utility to log user actions to the ActivityLog table."""
    try:
        log = ActivityLog(
            user_id=user_id,
            action=action,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {str(e)}")

def create_notification(user_id, message):
    """Utility to send system notification alerts to users."""
    try:
        notif = Notification(
            user_id=user_id,
            message=message
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {str(e)}")
