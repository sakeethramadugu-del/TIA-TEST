/**
 * Market News System
 * Handles loading and displaying market news with caching
 */

const NEWS_CACHE_KEY = "market_news_cache";
const NEWS_CACHE_DURATION = 30 * 60 * 1000; // 30 minutes

export async function loadMarketNews() {
    try {
        // Check cache first
        const cached = getCachedNews();
        if (cached) {
            renderNews(cached);
            return;
        }
        
        // Fetch from API
        const response = await fetch("/api/news");
        const data = await response.json();
        
        if (data.status === "success") {
            cacheNews(data.news);
            renderNews(data.news);
        }
    } catch (error) {
        console.error("Failed to load market news:", error);
        renderNewsError();
    }
}

function getCachedNews() {
    try {
        const cached = localStorage.getItem(NEWS_CACHE_KEY);
        if (!cached) return null;
        
        const { data, timestamp } = JSON.parse(cached);
        const now = Date.now();
        
        if (now - timestamp > NEWS_CACHE_DURATION) {
            localStorage.removeItem(NEWS_CACHE_KEY);
            return null;
        }
        
        return data;
    } catch (error) {
        console.error("Failed to get cached news:", error);
        return null;
    }
}

function cacheNews(news) {
    try {
        const cacheData = {
            data: news,
            timestamp: Date.now()
        };
        localStorage.setItem(NEWS_CACHE_KEY, JSON.stringify(cacheData));
    } catch (error) {
        console.error("Failed to cache news:", error);
    }
}

function renderNews(news) {
    const container = document.getElementById("marketNews");
    if (!container) return;
    
    if (!news || news.length === 0) {
        container.innerHTML = '<p class="small-meta">No news available</p>';
        return;
    }
    
    container.innerHTML = "";
    
    news.forEach(item => {
        const newsItem = document.createElement("div");
        newsItem.className = "news-item";
        newsItem.innerHTML = `
            <div class="news-title">${item.title}</div>
            <div class="news-summary">${item.summary}</div>
            <div class="news-meta">
                <span class="news-source">${item.source}</span>
                <span>${item.timestamp}</span>
            </div>
        `;
        
        // Click to open news (mock behavior)
        newsItem.addEventListener("click", () => {
            if (item.url && item.url !== "#") {
                window.open(item.url, "_blank");
            }
        });
        
        container.appendChild(newsItem);
    });
}

function renderNewsError() {
    const container = document.getElementById("marketNews");
    if (!container) return;
    
    container.innerHTML = '<p class="small-meta">Failed to load news. Please try again later.</p>';
}
