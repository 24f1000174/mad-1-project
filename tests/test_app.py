import unittest
import os
import sys

# Adjust path to find modules in parent folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from database.models import User, Trek, Booking, Profile

class TrekAppTestCase(unittest.TestCase):
    def setUp(self):
        """Set up a temporary testing database."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up the database."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_registration_and_login(self):
        """Test registration, status checking, and login."""
        # 1. Register a Trekker
        response = self.client.post('/auth/register', data={
            'role': 'trekker',
            'username': 'testtrekker',
            'email': 'trekker@test.com',
            'password': 'password123',
            'full_name': 'Test Trekker',
            'phone': '1234567890',
            'address': 'Test City'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful', response.data)
        
        # 2. Check if Trekker is approved automatically
        user = User.query.filter_by(username='testtrekker').first()
        self.assertEqual(user.status, 'approved')

        # 3. Register a Staff
        response = self.client.post('/auth/register', data={
            'role': 'staff',
            'username': 'teststaff',
            'email': 'staff@test.com',
            'password': 'password123',
            'full_name': 'Test Staff',
            'phone': '1234567890',
            'address': 'Test City'
        }, follow_redirects=True)
        self.assertIn(b'Registration successful', response.data)
        
        # 4. Check if Staff needs admin approval (is pending)
        staff = User.query.filter_by(username='teststaff').first()
        self.assertEqual(staff.status, 'pending')

        # 5. Verify pending staff login redirection
        response = self.client.post('/auth/login', data={
            'username_or_email': 'teststaff',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Account Pending Approval', response.data)

    def test_booking_logic_and_slots(self):
        """Test trek booking service logic and slot decrement/increment."""
        from services.trek_service import TrekService
        from services.booking_service import BookingService
        from datetime import date, timedelta
        
        # 1. Create a Staff and a Trekker
        staff = User(username='staff1', email='s1@test.com', role='staff', status='approved')
        staff.set_password('password')
        trekker = User(username='trekker1', email='t1@test.com', role='trekker', status='approved')
        trekker.set_password('password')
        db.session.add_all([staff, trekker])
        db.session.commit()
        
        # 2. Create a Trek
        trek, err = TrekService.create_trek(
            title="Himalayan Pass",
            description="High altitude pass trek.",
            difficulty="Hard",
            price=5000.0,
            max_slots=10,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            staff_id=staff.id
        )
        self.assertIsNotNone(trek)
        self.assertEqual(trek.available_slots, 10)
        
        # 3. Book the Trek
        booking, msg = BookingService.book_trek(trekker.id, trek.id)
        self.assertIsNotNone(booking)
        self.assertEqual(trek.available_slots, 9)
        self.assertEqual(booking.status, 'Booked')
        
        # 4. Cancel the booking
        success, msg = BookingService.cancel_booking(trekker.id, booking.id)
        self.assertTrue(success)
        self.assertEqual(trek.available_slots, 10)
        self.assertEqual(booking.status, 'Cancelled')

if __name__ == '__main__':
    unittest.main()
