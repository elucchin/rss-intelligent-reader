// Gestione filtri e feed
let keywordBlacklist = [];

function setupFilters() {
    const panel = document.getElementById('filter-panel');
    if (!panel) return;
    const input = document.createElement('input');
    input.type = 'text';
    input.id = 'keywords-input';
    input.placeholder = 'Parole chiave da escludere (separate da virgola)';
    panel.appendChild(input);
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Salva Filtri';
    saveBtn.onclick = () => {
        keywordBlacklist = input.value.split(',').map(w => w.trim().toLowerCase()).filter(Boolean);
        loadArticles();
    };
    panel.appendChild(saveBtn);
    // Filtro consigliati
    const onlyRecommendedCheck = document.createElement('input');
    onlyRecommendedCheck.type = 'checkbox';
    onlyRecommendedCheck.id = 'only-recommended';
    panel.appendChild(onlyRecommendedCheck);
    const labelCheck = document.createElement('label');
    labelCheck.textContent = 'Mostra solo consigliati';
    labelCheck.htmlFor = 'only-recommended';
    panel.appendChild(labelCheck);
    onlyRecommendedCheck.onchange = () => { loadArticles(); };
}

async function loadArticles() {
    const list = document.getElementById('articles-list');
    list.innerHTML = '<p class="loading">Caricamento articoli...</p>';
    try {
        const resp = await fetch('/api/articles');
        if (!resp.ok) throw new Error('Errore caricamento');
        let articles = await resp.json();
        if (keywordBlacklist.length) {
            articles = articles.filter(a => {
                return !keywordBlacklist.some(w =>
                    (a.title && a.title.toLowerCase().includes(w)) ||
                    (a.description && a.description.toLowerCase().includes(w)) ||
                    (a.content && a.content.toLowerCase().includes(w))
                );
            });
        }
        const onlyRecommended = document.getElementById('only-recommended');
        if (onlyRecommended && onlyRecommended.checked) {
            articles = articles.filter(a => a.is_recommended);
        }
        document.getElementById('article-count').textContent = `${articles.length} articoli non letti`;
        renderArticleList(list, articles, false);
    } catch (e) {
        list.innerHTML = '<p style="color: red;">Errore caricamento articoli</p>';
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
        let badge = '';
        if (article.is_recommended) badge = '<span class="badge">Consigliato</span>';
        card.innerHTML = `
            <h3>${escapeHtml(article.title)} ${badge}</h3>
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
        el.innerHTML = `<b>${escapeHtml(f.name)}</b>: <span>${escapeHtml(f.url)}</span> <span style="color: #888">${escapeHtml(f.category || '')}</span> ` +
            `<button style='margin:0 0 0 10px;' onclick='deleteFeed(${f.id})'>Elimina</button>`;
        container.appendChild(el);
    });
}

async function deleteFeed(feedId) {
    try {
        await fetch(`/api/feed/${feedId}/delete`, { method: 'POST' });
        await loadFeeds();
        await fetchAllFeeds();
        await loadArticles();
    } catch {
        alert('Errore cancellazione feed');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupFilters();
    loadArticles();
    loadFavorites();
    loadFeeds();
    setupToolbar();
});
