/**
 * Watchlist System
 * Handles loading, adding, and removing watchlist items
 */

import { showToast } from "./toast.js";

export async function loadWatchlist() {
    try {
        const response = await fetch("/api/watchlist");
        const data = await response.json();
        
        if (data.status === "success") {
            renderWatchlist(data.watchlist);
        }
    } catch (error) {
        console.error("Failed to load watchlist:", error);
    }
}

function renderWatchlist(watchlist) {
    const container = document.getElementById("watchlist");
    if (!container) return;
    
    if (watchlist.length === 0) {
        container.innerHTML = '<p class="small-meta">No items in watchlist</p>';
        return;
    }
    
    container.innerHTML = "";
    
    watchlist.forEach(item => {
        const watchlistItem = document.createElement("div");
        watchlistItem.className = "watchlist-item";
        watchlistItem.innerHTML = `
            <div class="watchlist-info">
                <div class="watchlist-ticker">${item.ticker}</div>
                <div class="watchlist-name">${item.name}</div>
            </div>
            <div class="watchlist-price">$${item.price.toFixed(2)}</div>
            <button class="watchlist-remove" onclick="removeFromWatchlist('${item.ticker}')">×</button>
        `;
        
        // Click to load stock
        watchlistItem.addEventListener("click", (e) => {
            if (!e.target.classList.contains("watchlist-remove")) {
                const tickerInput = document.getElementById("tickerInput");
                if (tickerInput) {
                    tickerInput.value = item.ticker;
                }
                if (typeof window.loadStock === "function") {
                    window.loadStock(item.ticker);
                }
            }
        });
        
        container.appendChild(watchlistItem);
    });
}

export async function addToWatchlist(ticker) {
    try {
        const response = await fetch("/api/watchlist", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ ticker })
        });
        
        const data = await response.json();
        
        if (data.status === "success") {
            showToast(data.message, "success");
            loadWatchlist();
        } else {
            showToast(data.error || "Failed to add to watchlist", "error");
        }
    } catch (error) {
        console.error("Failed to add to watchlist:", error);
        showToast("Failed to add to watchlist", "error");
    }
}

export async function removeFromWatchlist(ticker) {
    try {
        const response = await fetch("/api/watchlist", {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ ticker })
        });
        
        const data = await response.json();
        
        if (data.status === "success") {
            showToast(data.message, "success");
            loadWatchlist();
        } else {
            showToast(data.error || "Failed to remove from watchlist", "error");
        }
    } catch (error) {
        console.error("Failed to remove from watchlist:", error);
        showToast("Failed to remove from watchlist", "error");
    }
}

// Make removeFromWatchlist available globally for onclick
window.removeFromWatchlist = removeFromWatchlist;
