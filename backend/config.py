# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FETCH_INTERVAL = int(os.getenv('FETCH_INTERVAL', 600))
    MAX_ARTICLES = int(os.getenv('MAX_ARTICLES', 100))
    CLICK_WEIGHT = 0.8
    FAVORITE_WEIGHT = 0.3
    DECAY_DAYS = 30

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()
