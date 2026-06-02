/**
 * Streak System
 * Handles loading and displaying user streaks
 */

export async function loadStreaks() {
    try {
        const response = await fetch("/api/streaks");
        const data = await response.json();
        
        if (data.status === "success") {
            renderStreaks(data.streaks);
        }
    } catch (error) {
        console.error("Failed to load streaks:", error);
    }
}

function renderStreaks(streaks) {
    const container = document.getElementById("streaks");
    if (!container) return;
    
    if (Object.keys(streaks).length === 0) {
        container.innerHTML = '<p class="small-meta">No streaks available for guests</p>';
        return;
    }
    
    container.innerHTML = "";
    
    const streakIcons = {
        "login": "🔥",
        "learning": "📚",
        "trading": "💹"
    };
    
    const streakNames = {
        "login": "Login Streak",
        "learning": "Learning Streak",
        "trading": "Trading Streak"
    };
    
    Object.keys(streaks).forEach(streakType => {
        const streak = streaks[streakType];
        const item = document.createElement("div");
        item.className = "streak-item";
        item.innerHTML = `
            <div class="streak-info">
                <div class="streak-name">${streakNames[streakType] || streakType}</div>
                <div class="streak-best">Best: ${streak.best} days</div>
            </div>
            <div class="streak-badge">
                <span style="font-size: 20px;">${streakIcons[streakType] || "🔥"}</span>
            </div>
            <div class="streak-count">${streak.current}</div>
        `;
        container.appendChild(item);
    });
}
