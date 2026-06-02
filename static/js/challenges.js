/**
 * Daily Challenges System
 * Handles loading and displaying daily challenges
 */

export async function loadDailyChallenges() {
    try {
        const response = await fetch("/api/daily-challenges");
        const data = await response.json();
        
        if (data.status === "success") {
            renderDailyChallenges(data.challenges);
        }
    } catch (error) {
        console.error("Failed to load daily challenges:", error);
    }
}

function renderDailyChallenges(challenges) {
    const container = document.getElementById("dailyChallenges");
    if (!container) return;
    
    if (challenges.length === 0) {
        container.innerHTML = '<p class="small-meta">No challenges available for guests</p>';
        return;
    }
    
    container.innerHTML = "";
    
    challenges.forEach(challenge => {
        const item = document.createElement("div");
        item.className = `challenge-item ${challenge.completed ? "completed" : ""}`;
        item.innerHTML = `
            <div class="challenge-info">
                <div class="challenge-name">${challenge.name}</div>
                <div class="challenge-progress">${challenge.description} · ${challenge.current}/${challenge.target}</div>
            </div>
            <div class="challenge-reward">+${challenge.xp_reward} XP</div>
        `;
        container.appendChild(item);
    });
}
