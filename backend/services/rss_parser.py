# backend/services/rss_parser.py
import feedparser
import logging
from datetime import datetime
from backend.models import Article, Feed
from backend.database import db
import re

logger = logging.getLogger(__name__)

class RSSParser:
    @staticmethod
    def parse_feed(feed_url):
        try:
            logger.info(f"Parsing feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logger.warning(f"Feed warning: {feed.bozo_exception}")
            return feed
        except Exception as e:
            logger.error(f"Error parsing {feed_url}: {e}")
            return None
    
    @staticmethod
    def extract_keywords(text, max_keywords=10):
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'[^\w\s]', '', text.lower())
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
        words = text.split()
        keywords = [w for w in words if len(w) > 3 and w not in stopwords]
        return list(set(keywords[:max_keywords]))
    
    @staticmethod
    def add_articles_from_feed(feed_db):
        feed_data = RSSParser.parse_feed(feed_db.url)
        if not feed_data:
            return 0
        
        added_count = 0
        try:
            for entry in feed_data.entries:
                title = entry.get('title', 'No title')
                url = entry.get('link', '')
                description = entry.get('summary', '')
                author = entry.get('author', '')
                
                published_at = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                
                guid_hash = Article.generate_hash(url, title)
                existing = Article.query.filter_by(guid_hash=guid_hash).first()
                if existing:
                    continue
                
                keywords_text = ' '.join(RSSParser.extract_keywords(f"{title} {description}"))
                
                article = Article(
                    feed_id=feed_db.id,
                    title=title,
                    description=description[:1000],
                    url=url,
                    guid_hash=guid_hash,
                    author=author,
                    published_at=published_at,
                    keywords=keywords_text
                )
                db.session.add(article)
                added_count += 1
            
            feed_db.last_fetched = datetime.utcnow()
            db.session.commit()
            logger.info(f"Feed {feed_db.name}: added {added_count} articles")
            return added_count
            
        except Exception as e:
            logger.error(f"Error adding articles from feed: {e}")
            db.session.rollback()
            return 0
