# backend/services/ranker.py
from backend.models import Article, ArticleRead, Favorite, UserInterest
from backend.database import db
from datetime import datetime, timedelta
import math

class Ranker:
    CLICK_WEIGHT = 0.8
    FAVORITE_WEIGHT = 0.3
    DECAY_DAYS = 30
    
    @staticmethod
    def calculate_article_score(article, user):
        score = 0.0
        
        if article.keywords:
            keywords = article.keywords.split()
            for keyword in keywords:
                interest = UserInterest.query.filter_by(user_id=user.id, keyword=keyword).first()
                if interest:
                    score += (interest.implicit_weight * Ranker.CLICK_WEIGHT)
                    score += (interest.explicit_weight * Ranker.FAVORITE_WEIGHT)
        
        days_old = (datetime.utcnow() - article.fetched_at).days
        decay_factor = math.exp(-(days_old / Ranker.DECAY_DAYS))
        score *= decay_factor
        
        recent_bonus = 5.0 if days_old < 1 else (2.0 if days_old < 3 else 0.5)
        score += recent_bonus
        
        return max(score, 0.1)
    
    @staticmethod
    def rank_articles(user):
        unread = Article.query.filter(
            ~Article.reads.any(ArticleRead.user_id == user.id)
        ).all()
        
        scored = [(Ranker.calculate_article_score(article, user), article) for article in unread]
        scored.sort(reverse=True, key=lambda x: x[0])
        
        return [article for score, article in scored]
    
    @staticmethod
    def update_interests_from_click(user, article):
        if article.keywords:
            for keyword in article.keywords.split():
                interest = UserInterest.query.filter_by(user_id=user.id, keyword=keyword).first()
                if not interest:
                    interest = UserInterest(user_id=user.id, keyword=keyword)
                    db.session.add(interest)
                interest.implicit_weight += 2.0
                interest.last_updated = datetime.utcnow()
        db.session.commit()
