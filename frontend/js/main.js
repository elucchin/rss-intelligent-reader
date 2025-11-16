const API_BASE = 'http://localhost:5000/api';
let currentArticles = [];
let currentFavorites = [];
const articlesSection = document.getElementById('articles-section');
const favoritesSection = document.getElementById('favorites-section');
const showArticlesBtn = document.getElementById('show-articles');
const showFavoritesBtn = document.getElementById('show-favorites');
const addFeedBtn = document.getElementById('add-feed-btn');
const addFeedModal = document.getElementById('add-feed-modal');
const addFeedForm = document.getElementById('add-feed-form');
const closeAddFeedBtn = document.getElementById('close-add-feed');
const articleDetailModal = document.getElementById('article-detail-modal');
const closeArticleDetailBtn = document.getElementById('close-article-detail');
const fetchAllBtn = document.getElementById('fetch-all-btn');

document.addEventListener('DOMContentLoaded', () => {
  loadArticles();
  showArticlesBtn.addEventListener('click', () => showSection('articles'));
  showFavoritesBtn.addEventListener('click', () => showSection('favorites'));
  addFeedBtn.addEventListener('click', () => addFeedModal.classList.add('active'));
  closeAddFeedBtn.addEventListener('click', () => addFeedModal.classList.remove('active'));
  closeArticleDetailBtn.addEventListener('click', () => articleDetailModal.classList.remove('active'));
  addFeedForm.addEventListener('submit', handleAddFeed);
  fetchAllBtn.addEventListener('click', fetchAllFeeds);
  window.addEventListener('click', (e) => {
    if (e.target === addFeedModal) addFeedModal.classList.remove('active');
    if (e.target === articleDetailModal) articleDetailModal.classList.remove('active');
  });
});

async function loadArticles() {
  try {
    const response = await fetch(`${API_BASE}/articles`);
    if (!response.ok) throw new Error('Failed to load articles');
    currentArticles = await response.json();
    renderArticles();
  } catch (err) {
    console.error('Error loading articles:', err);
    alert('Error loading articles');
  }
}

async function loadFavorites() {
  try {
    const response = await fetch(`${API_BASE}/favorites`);
    if (!response.ok) throw new Error('Failed to load favorites');
    currentFavorites = await response.json();
    renderFavorites();
  } catch (err) {
    console.error('Error loading favorites:', err);
    alert('Error loading favorites');
  }
}

function renderArticles() {
  const container = document.getElementById('articles-grid');
  container.innerHTML = '';
  currentArticles.forEach(article => {
    const card = createArticleCard(article, 'article');
    container.appendChild(card);
  });
  if (currentArticles.length === 0) {
    container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No articles available</p>';
  }
}

function renderFavorites() {
  const container = document.getElementById('favorites-grid');
  container.innerHTML = '';
  currentFavorites.forEach(article => {
    const card = createArticleCard(article, 'favorite');
    container.appendChild(card);
  });
  if (currentFavorites.length === 0) {
    container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #999;">No favorites yet</p>';
  }
}

function createArticleCard(article, type) {
  const card = document.createElement('div');
  card.className = 'article-card';
  const isFavorited = currentFavorites.some(fav => fav.id === article.id);
  card.innerHTML = `
    <h3>${escapeHtml(article.title)}</h3>
    <p>${escapeHtml(article.summary || article.description || 'No summary available')}</p>
    <div class="article-meta">
      <span>${article.source || 'Unknown Source'}</span>
      <span>${formatDate(article.pub_date)}</span>
    </div>
    <div class="article-actions">
      <button class="star-btn ${isFavorited ? 'favorited' : ''}" onclick="toggleFavorite(event, ${article.id})" title="${isFavorited ? 'Remove from favorites' : 'Add to favorites'}">★</button>
    </div>
  `;
  card.addEventListener('click', (e) => {
    if (!e.target.classList.contains('star-btn')) {
      handleArticleClick(article);
    }
  });
  return card;
}

async function handleArticleClick(article) {
  try {
    await fetch(`${API_BASE}/article/${article.id}/read`, { method: 'POST' });
    showArticleDetail(article);
    loadArticles();
  } catch (err) {
    console.error('Error marking article as read:', err);
  }
}

async function toggleFavorite(event, articleId) {
  event.stopPropagation();
  try {
    const response = await fetch(`${API_BASE}/article/${articleId}/favorite`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to toggle favorite');
    loadFavorites();
    loadArticles();
  } catch (err) {
    console.error('Error toggling favorite:', err);
    alert('Error toggling favorite');
  }
}

function showArticleDetail(article) {
  document.getElementById('article-detail-title').textContent = article.title;
  document.getElementById('article-detail-source').textContent = article.source || 'Unknown';
  document.getElementById('article-detail-date').textContent = formatDate(article.pub_date);
  document.getElementById('article-detail-content').innerHTML = escapeHtml(article.content || article.summary || article.description || 'No content available');
  if (article.link) {
    document.getElementById('article-detail-link').href = article.link;
    document.getElementById('article-detail-link').style.display = 'inline-block';
  } else {
    document.getElementById('article-detail-link').style.display = 'none';
  }
  articleDetailModal.classList.add('active');
}

function showSection(section) {
  if (section === 'articles') {
    articlesSection.classList.remove('hidden');
    favoritesSection.classList.add('hidden');
    showArticlesBtn.style.background = '#667eea';
    showFavoritesBtn.style.background = '#f0f0f0';
  } else {
    articlesSection.classList.add('hidden');
    favoritesSection.classList.remove('hidden');
    showArticlesBtn.style.background = '#f0f0f0';
    showFavoritesBtn.style.background = '#667eea';
    loadFavorites();
  }
}

async function handleAddFeed(e) {
  e.preventDefault();
  const feedUrl = document.getElementById('feed-url').value.trim();
  if (!feedUrl) {
    alert('Please enter a feed URL');
    return;
  }
  try {
    const response = await fetch(`${API_BASE}/feed/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feed_url: feedUrl })
    });
    if (!response.ok) throw new Error('Failed to add feed');
    addFeedModal.classList.remove('active');
    addFeedForm.reset();
    loadArticles();
  } catch (err) {
    console.error('Error adding feed:', err);
    alert('Error adding feed. Please check the URL and try again.');
  }
}

async function fetchAllFeeds() {
  try {
    fetchAllBtn.disabled = true;
    fetchAllBtn.textContent = 'Fetching...';
    const response = await fetch(`${API_BASE}/fetch-all`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to fetch feeds');
    await loadArticles();
    fetchAllBtn.textContent = 'Fetch All Feeds';
    fetchAllBtn.disabled = false;
  } catch (err) {
    console.error('Error fetching feeds:', err);
    alert('Error fetching feeds');
    fetchAllBtn.textContent = 'Fetch All Feeds';
    fetchAllBtn.disabled = false;
  }
}

function formatDate(dateStr) {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr || 'Unknown date';
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
