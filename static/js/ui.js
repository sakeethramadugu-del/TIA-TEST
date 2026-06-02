import { state, saveState } from "./state.js";
import { goal, levels, tips, glossaryItems, quizQuestions } from "./data.js";
import { formatMoney } from "./helpers.js";

export function addActivity(message) {
    const timestamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    state.activityLog.unshift(`${timestamp} — ${message}`);
    if (state.activityLog.length > 6) state.activityLog.pop();
    renderActivity();
    saveState();
}

export function renderActivity() {
    const container = document.getElementById("activityLog");
    container.innerHTML = "";
    if (state.activityLog.length === 0) {
        container.innerText = "No activity yet";
        return;
    }
    state.activityLog.forEach(entry => {
        const row = document.createElement("div");
        row.className = "activity-row";
        row.textContent = entry;
        container.appendChild(row);
    });
}

export function getLevel(xpPoints) {
    let title = levels[0].title;
    for (const level of levels) {
        if (xpPoints >= level.threshold) title = level.title;
    }
    return title;
}

export function renderGlossary() {
    const grid = document.getElementById("glossaryGrid");
    grid.innerHTML = "";
    glossaryItems.forEach(item => {
        const element = document.createElement("div");
        element.className = "glossary-item";
        element.innerHTML = `<strong>${item.term}</strong><span>${item.definition}</span>`;
        grid.appendChild(element);
    });
}

export function renderHistory() {
    const history = document.getElementById("tradeHistory");
    history.innerHTML = "";
    if (state.tradeHistory.length === 0) {
        history.innerText = "No trades yet";
        return;
    }
    state.tradeHistory.slice(0, 6).forEach(entry => {
        const row = document.createElement("div");
        row.className = "activity-row";
        row.textContent = entry;
        history.appendChild(row);
    });
}

export function renderGoal(currentValue) {
    const progress = Math.min(1, currentValue / goal.target);
    document.getElementById("goalDescription").innerText = goal.description;
    document.getElementById("goalProgress").style.width = `${Math.round(progress * 100)}%`;
    document.getElementById("goalText").innerText = `${formatMoney(currentValue)} / ${formatMoney(goal.target)}`;
}

export function updateUI() {
    document.getElementById("cash").innerText = formatMoney(state.cash);
    document.getElementById("level").innerText = getLevel(state.xp);
    const portfolioDiv = document.getElementById("portfolio");
    portfolioDiv.innerHTML = "";

    const portfolioValue = Object.keys(state.positions).reduce((total, symbol) => {
        const position = state.positions[symbol];
        const price = state.lastPrices[symbol] || state.currentPrice;
        return total + position.shares * price;
    }, 0);

    document.getElementById("portfolioValue").innerText = formatMoney(state.cash + portfolioValue);
    
    // Calculate portfolio change percentage
    const portfolioChangePercent = ((state.cash + portfolioValue - state.startingCash) / state.startingCash) * 100;
    const portfolioChangeEl = document.getElementById("portfolioChange");
    if (portfolioChangeEl) {
        portfolioChangeEl.innerText = `${portfolioChangePercent >= 0 ? "+" : ""}${portfolioChangePercent.toFixed(2)}% change`;
        portfolioChangeEl.style.color = portfolioChangePercent >= 0 ? "#22C55E" : "#EF4444";
    }

    const profit = state.cash + portfolioValue - state.startingCash;
    document.getElementById("profit").innerText = `${profit >= 0 ? "+" : ""}${formatMoney(profit)}`;
    document.getElementById("profit").style.color = profit >= 0 ? "#22C55E" : "#EF4444";
    
    // Add profit percentage display
    const profitPercentEl = document.getElementById("profitPercent");
    if (profitPercentEl) {
        profitPercentEl.innerText = `${portfolioChangePercent >= 0 ? "+" : ""}${portfolioChangePercent.toFixed(2)}%`;
        profitPercentEl.style.color = portfolioChangePercent >= 0 ? "#22C55E" : "#EF4444";
    }

    renderGoal(state.cash + portfolioValue);

    // Update XP progress bar
    const xpProgressEl = document.getElementById("xpProgress");
    const xpToNextEl = document.getElementById("xpToNext");
    const xpEl = document.getElementById("xp");
    if (xpProgressEl && xpToNextEl && xpEl) {
        xpEl.innerText = `${state.xp} XP`;
        const currentLevel = Math.floor(state.xp / 100) + 1;
        const xpInCurrentLevel = state.xp % 100;
        const xpToNextLevel = 100 - xpInCurrentLevel;
        
        xpProgressEl.style.width = `${xpInCurrentLevel}%`;
        xpToNextEl.innerText = `${xpInCurrentLevel} / 100 XP to next level`;
    }

    if (Object.keys(state.positions).length === 0) {
        portfolioDiv.innerText = "No holdings yet";
    } else {
        Object.keys(state.positions).forEach(symbol => {
            const position = state.positions[symbol];
            const price = state.lastPrices[symbol] || state.currentPrice;
            const value = position.shares * price;
            const gain = position.shares * (price - position.avgCost);
            const row = document.createElement("div");
            row.className = "holding-row";
            row.innerHTML = `
                <div>
                    <strong>${symbol}</strong>
                    <small>${position.shares} shares @ ${formatMoney(position.avgCost)}</small>
                </div>
                <div>
                    <strong>${formatMoney(value)}</strong>
                    <small>${gain >= 0 ? "+" : ""}${formatMoney(gain)}</small>
                </div>
            `;
            portfolioDiv.appendChild(row);
        });
    }

    document.getElementById("quizStatus").innerText = `Question ${state.currentQuestion + 1} of ${quizQuestions.length} • Earn cash and XP`;
    document.getElementById("quizScore").innerText = `${state.quizCorrect} / ${state.quizTotal}`;
    document.getElementById("quizStreak").innerText = `Current quiz streak: ${state.quizStreak}`;
    document.getElementById("lessonStreak").innerText = state.lessonStreak;
    document.getElementById("bestLessonStreak").innerText = `Best streak: ${state.bestLessonStreak}`;
    document.getElementById("investmentTip").innerText = tips[Math.floor(Math.random() * tips.length)];

    if (!state.goalAwarded && state.cash + portfolioValue >= goal.target) {
        state.goalAwarded = true;
        state.xp += goal.rewardXP;
        addActivity(`Goal reached: ${goal.description}. Earned ${goal.rewardXP} XP.`);
    }
    renderActivity();
    saveState();
}

export function loadTip() {
    const tip = tips[Math.floor(Math.random() * tips.length)];
    document.getElementById("investmentTip").innerText = tip;
}
