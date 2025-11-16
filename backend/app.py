import os
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import logging
from datetime import datetime, timedelta

from backend.database import db, init_db, get_db_path
from backend.config import get_config
from backend.models import User, Feed, Article, ArticleRead, Favorite, UserInterest
from backend.services.rss_parser import RSSParser
from backend.services.ranker import Ranker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config=None):
    """Application factory for creating Flask app instances."""
    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    app = Flask(__name__, template_folder=template_path, static_folder=template_path)
    app.config['SQLALCHEMY_DATABASE_URI'] = get_db_path()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    if config:
        app.config.update(config)
    
    db.init_app(app)
    CORS(app)
    
    with app.app_context():
        db.create_all()
    
    # Session handler
    @app.before_request
    def ensure_user():
        if 'user_id' not in session:
            user = User.query.filter_by(username='default_user').first()
            if not user:
                user = User(username='default_user')
                db.session.add(user)
                db.session.commit()
            session['user_id'] = user.id
    
    # Frontend routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    # API routes
    @app.route('/api/articles')
    def get_articles():
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        ranked_articles = Ranker.rank_articles(user)
        articles = [{
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'content': a.content,
            'link': a.url,
            'source': a.feed.name,
            'pub_date': a.published_at.isoformat(),
            'summary': a.description[:200] if a.description else 'No summary',
        } for a in ranked_articles]
        
        return jsonify(articles)
    
    @app.route('/api/article/<int:article_id>/read', methods=['POST'])
    def mark_article_read(article_id):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        article = Article.query.get(article_id)
        
        if not user or not article:
            return jsonify({'error': 'Not found'}), 404
        
        # Mark as read
        read = ArticleRead(user_id=user.id, article_id=article.id)
        db.session.add(read)
        
        # Learn from click (implicit interest - weight 0.8)
        if article.keywords:
            for keyword in article.keywords.split():
                interest = UserInterest.query.filter_by(user_id=user.id, keyword=keyword).first()
                
                if not interest:
                    interest = UserInterest(user_id=user.id, keyword=keyword)
                    db.session.add(interest)
                
                interest.implicit_weight += 0.8
        
        db.session.commit()
        return jsonify({'status': 'ok'})
    
    @app.route('/api/article/<int:article_id>/favorite', methods=['POST'])
    def toggle_favorite(article_id):
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        article = Article.query.get(article_id)
        
        if not user or not article:
            return jsonify({'error': 'Not found'}), 404
        
        fav = Favorite.query.filter_by(user_id=user.id, article_id=article.id).first()
        
        if fav:
            db.session.delete(fav)
        else:
            fav = Favorite(user_id=user.id, article_id=article.id)
            db.session.add(fav)
        
        # Learn from favorite (explicit interest - weight 0.3)
        if article.keywords:
            for keyword in article.keywords.split():
                interest = UserInterest.query.filter_by(user_id=user.id, keyword=keyword).first()
                
                if not interest:
                    interest = UserInterest(user_id=user.id, keyword=keyword)
                    db.session.add(interest)
                
                interest.explicit_weight += 1.0
        
        db.session.commit()
        return jsonify({'status': 'ok', 'is_favorite': bool(not fav)})
    
    @app.route('/api/favorites')
    def get_favorites():
        user_id = session.get('user_id')
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        favorites = user.favorites
        articles = [{
            'id': f.article.id,
            'title': f.article.title,
            'description': f.article.description,
            'content': f.article.content,
            'link': f.article.url,
            'source': f.article.feed.name,
            'pub_date': f.article.published_at.isoformat(),
            'summary': f.article.description[:200] if f.article.description else 'No summary',
            'added_at': f.added_at.isoformat()
        } for f in favorites]
        
        return jsonify(articles)
    
    @app.route('/api/feeds')
    def get_feeds():
        feeds = Feed.query.filter_by(active=True).all()
        
        return jsonify([{
            'id': f.id,
            'name': f.name,
            'url': f.url,
            'category': f.category
        } for f in feeds])
    
    @app.route('/api/feed/add', methods=['POST'])
    def add_feed():
        data = request.json
        feed_url = data.get('feed_url')
        feed_name = data.get('name', feed_url)
        
        existing = Feed.query.filter_by(url=feed_url).first()
        
        if existing:
            return jsonify({'error': 'Feed already exists'}), 400
        
        feed = Feed(name=feed_name, url=feed_url)
        db.session.add(feed)
        db.session.commit()
        
        RSSParser.add_articles_from_feed(feed)
        
        return jsonify({'status': 'ok', 'feed_id': feed.id})
    
    @app.route('/api/fetch-all', methods=['POST'])
    def fetch_all_feeds():
        feeds = Feed.query.filter_by(active=True).all()
        total_added = 0
        
        for feed in feeds:
            added = RSSParser.add_articles_from_feed(feed)
            total_added += added
        
        return jsonify({'status': 'ok', 'articles_added': total_added})
    
    return app
