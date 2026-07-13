from app import create_app
from extensions import db
from database.seed_data import seed_all_data

def run_seed():
    """Main seed entrypoint script to create database and fill mock data."""
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_all_data()
        print("Database created and seeded successfully!")

if __name__ == '__main__':
    run_seed()
