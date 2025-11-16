document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadArticles();
    loadFavorites();
    loadFeeds();
    setupToolbar();
});

function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            document.getElementById(btn.dataset.tab).classList.add('active');
            
            if (btn.dataset.tab === 'articles') loadArticles();
            if (btn.dataset.tab === 'favorites') loadFavorites();
            if (btn.dataset.tab === 'feeds') loadFeeds();
        });
    });
}

function setupToolbar() {
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) refreshBtn.addEventListener('click', fetchAllFeeds);

    const addFeedBtn = document.getElementById('add-feed-btn');
    if (addFeedBtn) addFeedBtn.addEventListener('click', () => {
        document.getElementById('add-feed-form').style.display = 'block';
        addFeedBtn.style.display = 'none';
    });
    const cancelFeedBtn = document.getElementById('cancel-feed-btn');
    if (cancelFeedBtn) cancelFeedBtn.addEventListener('click', () => {
        document.getElementById('add-feed-form').style.display = 'none';
        addFeedBtn.style.display = 'inline-block';
    });
    const saveFeedBtn = document.getElementById('save-feed-btn');
    if (saveFeedBtn) saveFeedBtn.addEventListener('click', handleAddFeed);
}

const API_BASE = '/api';

async function loadArticles() {
    const list = document.getElementById('articles-list');
    list.innerHTML = '<p class="loading">Caricamento articoli...</p>';
    try {
        const resp = await fetch(`${API_BASE}/articles`);
        if (!resp.ok) throw new Error('Errore caricamento');
        const articles = await resp.json();
        document.getElementById('article-count').textContent = `${articles.length} articoli non letti`;
        renderArticleList(list, articles, false);
    } catch (e) {
        list.innerHTML = '<p style="color: red;">Errore caricamento articoli</p>';
    }
}

async function loadFavorites() {
    const list = document.getElementById('favorites-list');
    list.innerHTML = '<p class="loading">Caricamento preferiti...</p>';
    try {
        const resp = await fetch(`${API_BASE}/favorites`);
        if (!resp.ok) throw new Error('Errore caricamento');
        const favorites = await resp.json();
        document.getElementById('favorites-count').textContent = `${favorites.length} preferiti`;
        renderArticleList(list, favorites, true);
    } catch (e) {
        list.innerHTML = '<p style="color: red;">Errore caricamento preferiti</p>';
    }
}

async function loadFeeds() {
    const list = document.getElementById('feeds-list');
    list.innerHTML = '<p class="loading">Caricamento feed...</p>';
    try {
        const resp = await fetch(`${API_BASE}/feeds`);
        if (!resp.ok) throw new Error('Errore caricamento');
        const feeds = await resp.json();
        renderFeedList(list, feeds);
    } catch (e) {
        list.innerHTML = '<p style="color: red;">Errore caricamento feed</p>';
    }
}

function renderArticleList(container, articles, isFavorite) {
    container.innerHTML = '';
    if (!articles.length) {
        container.innerHTML = '<p style="color: #999;">Nessun elemento disponibile</p>';
        return;
    }
    articles.forEach(article => {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.innerHTML = `
            <h3>${escapeHtml(article.title)}</h3>
            <p>${escapeHtml(article.summary || article.description || 'Nessun riassunto disponibile')}</p>
            <div class="article-meta">
                <span>${article.source || 'Fonte sconosciuta'}</span>
                <span>${formatDate(article.pub_date)}</span>
            </div>
            <div class="article-actions">
                <button class="star-btn${article.is_favorite || isFavorite ? ' favorited' : ''}" title="Preferito" onclick="event.stopPropagation();toggleFavorite(${article.id});">★</button>
                <a class="open-article" href="${article.link}" target="_blank" onclick="event.stopPropagation();">Apri</a>
            </div>
        `;
        card.addEventListener('click', () => {
            markReadAndShowModal(article);
        });
        container.appendChild(card);
    });
}

function renderFeedList(container, feeds) {
    container.innerHTML = '';
    if (!feeds.length) {
        container.innerHTML = '<p>Nessun feed configurato.</p>';
        return;
    }
    feeds.forEach(f => {
        const el = document.createElement('div');
        el.className = 'feed-item';
        el.innerHTML = `<b>${escapeHtml(f.name)}</b>: <span>${escapeHtml(f.url)}</span> <span style="color: #888">${escapeHtml(f.category || '')}</span>`;
        container.appendChild(el);
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('it-IT');
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

async function toggleFavorite(articleId) {
    try {
        await fetch(`${API_BASE}/article/${articleId}/favorite`, {
            method: 'POST'
        });
        await loadArticles();
        await loadFavorites();
    } catch (e) {
        alert('Errore nel salvataggio del preferito');
    }
}

async function markReadAndShowModal(article) {
    try {
        await fetch(`${API_BASE}/article/${article.id}/read`, { method: 'POST' });
    } catch{}
    // modal semplicizzata
    const modal = document.getElementById('article-modal');
    const detail = document.getElementById('article-detail');
    detail.innerHTML = `
        <h2>${escapeHtml(article.title)}</h2>
        <div><b>Fonte:</b> ${escapeHtml(article.source || '')}</div>
        <div><b>Data:</b> ${formatDate(article.pub_date)}</div>
        <p>${escapeHtml(article.content || article.summary || article.description || '')}</p>
        <a href="${article.link}" target="_blank">Leggi l'articolo completo</a>
    `;
    modal.style.display = 'block';
    modal.querySelector('.close').onclick = () => {
        modal.style.display = 'none';
    };
    window.onclick = event => {
        if (event.target === modal) modal.style.display = 'none';
    };
}

async function handleAddFeed(e) {
    e.preventDefault();
    const feedUrl = document.getElementById('feed-url-input').value.trim();
    const name = document.getElementById('feed-name-input').value.trim();
    if (!feedUrl) {
        alert('Inserire URL del feed');
        return;
    }
    try {
        await fetch(`${API_BASE}/feed/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 'feed_url': feedUrl, 'name': name })
        });
        document.getElementById('add-feed-form').style.display = 'none';
        document.getElementById('add-feed-btn').style.display = 'inline-block';
        await loadFeeds();
        await fetchAllFeeds();
        await loadArticles();
    } catch {
        alert("Errore durante aggiunta feed");
    }
}

async function fetchAllFeeds() {
    const btn = document.getElementById('refresh-btn');
    if (btn) btn.disabled = true;
    try {
        await fetch(`${API_BASE}/fetch-all`, { method: 'POST' });
        await loadArticles();
    } catch {
        alert('Errore aggiornamento feed');
    }
    if (btn) btn.disabled = false;
}
