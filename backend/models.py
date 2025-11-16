# backend/models.py
from backend.database import db
from datetime import datetime
import hashlib

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    article_reads = db.relationship('ArticleRead', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')

class Feed(db.Model):
    __tablename__ = 'feeds'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    category = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    last_fetched = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    articles = db.relationship('Article', backref='feed', lazy=True, cascade='all, delete-orphan')

class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey('feeds.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    url = db.Column(db.String(500))
    guid_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    author = db.Column(db.String(200))
    published_at = db.Column(db.DateTime)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    keywords = db.Column(db.Text)
    reads = db.relationship('ArticleRead', backref='article', lazy=True, cascade='all, delete-orphan')
    favorites_list = db.relationship('Favorite', backref='article', lazy=True, cascade='all, delete-orphan')
    
    @staticmethod
    def generate_hash(url, title):
        combined = f"{url}:{title}".encode('utf-8')
        return hashlib.sha256(combined).hexdigest()

class ArticleRead(db.Model):
    __tablename__ = 'article_reads'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False, index=True)
    read_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    click_weight = db.Column(db.Float, default=1.0)
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='unique_user_article_read'),)

class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False, index=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    __table_args__ = (db.UniqueConstraint('user_id', 'article_id', name='unique_user_article_favorite'),)

class UserInterest(db.Model):
    __tablename__ = 'user_interests'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    keyword = db.Column(db.String(200), nullable=False, index=True)
    category = db.Column(db.String(100))
    implicit_weight = db.Column(db.Float, default=0.0)
    explicit_weight = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'keyword', name='unique_user_keyword'),)
