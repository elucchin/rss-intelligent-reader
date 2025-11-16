# backend/database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

db = SQLAlchemy()

def init_db(app):
    """Inizializza il database"""
    with app.app_context():
        db.create_all()
        print("✅ Database initialized")

def get_db_path():
    """Ritorna il path del database SQLite"""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    return f"sqlite:///{os.path.join(data_dir, 'app.db').replace(os.sep, '/')}"
