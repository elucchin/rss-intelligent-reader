# backend/app.py
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

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend')
app.config['SQLALCHEMY_DATABASE_URI'] = get_db_path()
app.config.from_object(get_config())

db.init_app(app)
CORS(app)

init_db(app)

@app.before_request
def ensure_user():
    if 'user_id' not in session:
        user = User.query.first()
        if not user:
            user = User(username='default_user')
            db.session.add(user)
            db.session.commit()
        session['user_id'] = user.id

@app.route('/')
def index():
    return render_template('index.html')

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
        'url': a.url,
        'author': a.author,
        'feed_name': a.feed.name,
        'published_at': a.published_at.isoformat() if a.published_at else None,
        'is_favorite': any(f.article_id == a.id for f in user.favorites)
    } for a in ranked_articles[:50]]
    
    return jsonify(articles)

@app.route('/api/article/<int:article_id>/read', methods=['POST'])
def mark_read(article_id):
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    article = Article.query.get(article_id)
    
    if not article or not user:
        return jsonify({'error': 'Not found'}), 404
    
    read = ArticleRead.query.filter_by(user_id=user.id, article_id=article.id).first()
    if not read:
        read = ArticleRead(user_id=user.id, article_id=article.id)
        db.session.add(read)
    
    Ranker.update_interests_from_click(user, article)
    db.session.commit()
    
    return jsonify({'status': 'ok'})

@app.route('/api/article/<int:article_id>/favorite', methods=['POST'])
def toggle_favorite(article_id):
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    article = Article.query.get(article_id)
    
    if not article or not user:
        return jsonify({'error': 'Not found'}), 404
    
    fav = Favorite.query.filter_by(user_id=user.id, article_id=article.id).first()
    if fav:
        db.session.delete(fav)
    else:
        fav = Favorite(user_id=user.id, article_id=article.id)
        db.session.add(fav)
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
        'url': f.article.url,
        'feed_name': f.article.feed.name,
        'added_at': f.added_at.isoformat()
    } for f in favorites]
    
    return jsonify(articles)

@app.route('/api/feeds')
def get_feeds():
    feeds = Feed.query.filter_by(active=True).all()
    return jsonify([{'id': f.id, 'name': f.name, 'url': f.url, 'category': f.category} for f in feeds])

@app.route('/api/feed/add', methods=['POST'])
def add_feed():
    data = request.json
    feed_url = data.get('url')
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

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, host='0.0.0.0', port=5000)
