@app.route('/api/feed/<int:feed_id>/delete', methods=['POST'])
def delete_feed(feed_id):
    feed = Feed.query.get(feed_id)
    if not feed:
        return jsonify({'error': 'Feed non trovato'}), 404
    db.session.delete(feed)
    db.session.commit()
    return jsonify({'status': 'ok'})

# MODIFICA get_feeds per includere id
@app.route('/api/feeds')
def get_feeds():
    feeds = Feed.query.filter_by(active=True).all()
    return jsonify([
        {
            'id': f.id,
            'name': f.name,
            'url': f.url,
            'category': f.category
        } for f in feeds
    ])

# MODIFICA get_articles per restituire score
@app.route('/api/articles')
def get_articles():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    ranked_articles = Ranker.rank_articles(user)
    articles = []
    for a in ranked_articles:
        score = Ranker.calculate_article_score(a, user)
        articles.append({
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'content': a.content,
            'link': a.url,
            'source': a.feed.name,
            'pub_date': a.published_at.isoformat() if a.published_at else '',
            'summary': a.description[:200] if a.description else 'No summary',
            'score': score,
            'is_recommended': score >= 3.0
        })
    return jsonify(articles)
