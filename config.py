import os

class Config:
    """Base configuration settings for the Flask application."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_24F1000174_trekking_app')
    
    # Define base directory of the project
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Path to SQLite database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'trekking.db')}"
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Custom config options if needed
    DEBUG = True
