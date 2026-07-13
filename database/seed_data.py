import sys
import os
from datetime import date, timedelta, datetime

# Adjust path to find modules in parent folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions import db
from database.models import User, Profile, Trek, Booking, Notification, ActivityLog

def seed_all_data():
    """Seeds the database with default admin and mock data for testing."""
    
    # 1. Seed Admin if not exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@trekking.com',
            role='admin',
            status='approved'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.flush() # Get admin.id
        
        profile = Profile(
            user_id=admin.id,
            full_name='System Administrator',
            phone='9876543210',
            address='Admin Headquarters'
        )
        db.session.add(profile)
        print("Admin user seeded (Username: admin, Password: admin123)")

    # 2. Seed Staff users if not exists
    staff_data = [
        {'username': 'staff_approved', 'email': 'staff1@trekking.com', 'status': 'approved', 'name': 'John Doe (Approved Staff)'},
        {'username': 'staff_pending', 'email': 'staff2@trekking.com', 'status': 'pending', 'name': 'Jane Smith (Pending Staff)'},
        {'username': 'staff_blacklisted', 'email': 'staff3@trekking.com', 'status': 'blacklisted', 'name': 'Bob Johnson (Blacklisted Staff)'}
    ]
    
    seeded_staff = {}
    for sd in staff_data:
        u = User.query.filter_by(username=sd['username']).first()
        if not u:
            u = User(
                username=sd['username'],
                email=sd['email'],
                role='staff',
                status=sd['status']
            )
            u.set_password('password123')
            db.session.add(u)
            db.session.flush()
            
            p = Profile(
                user_id=u.id,
                full_name=sd['name'],
                phone='9000000001',
                address='Staff Quarter 1'
            )
            db.session.add(p)
            seeded_staff[sd['username']] = u
            print(f"Staff user seeded: {sd['username']} (Status: {sd['status']})")
        else:
            seeded_staff[sd['username']] = u

    # 3. Seed Trekkers if not exists
    trekker_data = [
        {'username': 'trekker_jack', 'email': 'jack@gmail.com', 'status': 'approved', 'name': 'Jack Ryan'},
        {'username': 'trekker_alice', 'email': 'alice@gmail.com', 'status': 'approved', 'name': 'Alice Cooper'},
        {'username': 'trekker_blacklisted', 'email': 'black@gmail.com', 'status': 'blacklisted', 'name': 'Blacklisted Trekker'}
    ]
    
    seeded_trekkers = {}
    for td in trekker_data:
        u = User.query.filter_by(username=td['username']).first()
        if not u:
            u = User(
                username=td['username'],
                email=td['email'],
                role='trekker',
                status=td['status']
            )
            u.set_password('password123')
            db.session.add(u)
            db.session.flush()
            
            p = Profile(
                user_id=u.id,
                full_name=td['name'],
                phone='9888888888',
                address='Trekker Lane, City A',
                emergency_contact='9999999999',
                medical_conditions='None'
            )
            db.session.add(p)
            seeded_trekkers[td['username']] = u
            print(f"Trekker user seeded: {td['username']} (Status: {td['status']})")
        else:
            seeded_trekkers[td['username']] = u

    # 4. Seed Treks if empty
    if Trek.query.count() == 0:
        today = date.today()
        
        treks_to_seed = [
            {
                'title': 'Himalayan Valley Trek',
                'description': 'A beautiful high-altitude trek crossing panoramic alpine meadows and freezing glacial lakes.',
                'difficulty': 'Hard',
                'start_date': today + timedelta(days=15),
                'end_date': today + timedelta(days=22),
                'price': 15000.0,
                'max_slots': 15,
                'available_slots': 15,
                'status': 'Upcoming',
                'staff': seeded_staff.get('staff_approved')
            },
            {
                'title': 'Western Ghats Ridge Walk',
                'description': 'Explore lush green valleys, steep ridges, and heavy cloud covers in this moderate weekend trek.',
                'difficulty': 'Moderate',
                'start_date': today + timedelta(days=5),
                'end_date': today + timedelta(days=7),
                'price': 3500.0,
                'max_slots': 20,
                'available_slots': 19, # One slot booked for demo
                'status': 'Upcoming',
                'staff': seeded_staff.get('staff_approved')
            },
            {
                'title': 'Nilgiri Hill Trail',
                'description': 'An easy trail walking through aromatic tea plantations and dense shola forests.',
                'difficulty': 'Easy',
                'start_date': today - timedelta(days=10),
                'end_date': today - timedelta(days=7),
                'price': 2000.0,
                'max_slots': 10,
                'available_slots': 8,
                'status': 'Completed',
                'staff': seeded_staff.get('staff_approved')
            },
            {
                'title': 'Roopkund Lake Expedition',
                'description': 'Challenging high altitude trek to the mystery skeleton lake in Uttarakhand.',
                'difficulty': 'Challenging',
                'start_date': today + timedelta(days=30),
                'end_date': today + timedelta(days=38),
                'price': 18000.0,
                'max_slots': 12,
                'available_slots': 12,
                'status': 'Upcoming',
                'staff': None # Unassigned staff to test assigning
            }
        ]
        
        seeded_treks = []
        for t_data in treks_to_seed:
            t = Trek(
                title=t_data['title'],
                description=t_data['description'],
                difficulty=t_data['difficulty'],
                start_date=t_data['start_date'],
                end_date=t_data['end_date'],
                price=t_data['price'],
                max_slots=t_data['max_slots'],
                available_slots=t_data['available_slots'],
                status=t_data['status'],
                staff_id=t_data['staff'].id if t_data['staff'] else None
            )
            db.session.add(t)
            db.session.flush()
            seeded_treks.append(t)
            print(f"Trek seeded: {t.title}")
            
        # 5. Create a booking demo
        if len(seeded_treks) > 1 and 'trekker_jack' in seeded_trekkers:
            b = Booking(
                user_id=seeded_trekkers['trekker_jack'].id,
                trek_id=seeded_treks[1].id, # Western Ghats (id index 1)
                booking_date=datetime.utcnow() - timedelta(days=1),
                status='Booked',
                price_paid=seeded_treks[1].price
            )
            db.session.add(b)
            
            # Action log entry
            log = ActivityLog(
                user_id=seeded_trekkers['trekker_jack'].id,
                action='Trek Booking',
                details=f"Booked trek: {seeded_treks[1].title} paying Rs. {seeded_treks[1].price}"
            )
            db.session.add(log)
            print(f"Demo booking seeded for {seeded_trekkers['trekker_jack'].username} on {seeded_treks[1].title}")

    db.session.commit()
    print("Database seeding completed.")
