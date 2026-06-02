import { state, loadState } from "./state.js";
import { formatMoney, shuffle } from "./helpers.js";
import { fetchStock, fetchLesson, fetchQuiz, fetchLessons, fetchQuizzes, fetchAssets } from "./api.js";
import { addActivity, renderActivity, renderGlossary, renderHistory, renderGoal, updateUI, loadTip } from "./ui.js";
import { lessons, quizQuestions } from "./data.js";
import { showToast } from "./toast.js";
import { checkAchievements } from "./achievements.js";
import { loadDailyChallenges } from "./challenges.js";
import { loadStreaks } from "./streaks.js";
import { loadWatchlist, addToWatchlist } from "./watchlist.js";
import { loadMarketNews } from "./news.js";
import { loadPortfolioAnalytics } from "./analytics.js";

function showLoading() {
    const overlay = document.getElementById("loadingOverlay");
    if (overlay) overlay.classList.remove("hidden");
}

function hideLoading() {
    const overlay = document.getElementById("loadingOverlay");
    if (overlay) overlay.classList.add("hidden");
}

function showGuestConvertModal() {
    const modal = document.getElementById("guestConvertModal");
    if (modal) modal.classList.remove("hidden");
}

function hideGuestConvertModal() {
    const modal = document.getElementById("guestConvertModal");
    if (modal) modal.classList.add("hidden");
}

// Handle guest conversion form submission
document.addEventListener("DOMContentLoaded", () => {
    const guestConvertForm = document.getElementById("guestConvertForm");
    if (guestConvertForm) {
        guestConvertForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            showLoading();
            
            const username = document.getElementById("convertUsername").value;
            const email = document.getElementById("convertEmail").value;
            const password = document.getElementById("convertPassword").value;
            
            try {
                const response = await fetch("/api/guest/convert", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ username, email, password })
                });
                
                const data = await response.json();
                
                if (data.status === "success") {
                    showToast("Account created successfully! Your progress has been saved.", "success");
                    hideGuestConvertModal();
                    // Reload page to update UI
                    window.location.reload();
                } else {
                    showToast(data.error || "Conversion failed", "error");
                }
            } catch (error) {
                showToast("Conversion failed. Please try again.", "error");
            } finally {
                hideLoading();
            }
        });
    }
});

// Global function to add current stock to watchlist
window.addToWatchlistFromUI = function() {
    const ticker = state.currentTicker;
    if (ticker) {
        addToWatchlist(ticker);
    }
};

async function fetchUserState() {
    try {
        const response = await fetch("/api/user");
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        console.warn("Could not fetch user state", error);
        return null;
    }
}

function hydrateStateFromServer(user) {
    if (!user || !user.authenticated) {
        state.authenticated = false;
        // Hide guest banner if not authenticated
        const guestBanner = document.getElementById("guestBanner");
        if (guestBanner) guestBanner.classList.add("hidden");
        return;
    }

    state.authenticated = true;
    state.cash = user.cash;
    state.xp = user.xp;
    state.tradeHistory = user.tradeHistory || [];
    state.positions = {};
    state.is_guest = user.is_guest || false;

    // Show/hide guest banner based on user type
    const guestBanner = document.getElementById("guestBanner");
    if (guestBanner) {
        if (state.is_guest) {
            guestBanner.classList.remove("hidden");
        } else {
            guestBanner.classList.add("hidden");
        }
    }

    if (user.portfolio) {
        Object.keys(user.portfolio).forEach(symbol => {
            const position = user.portfolio[symbol] || {};
            state.positions[symbol] = {
                shares: position.shares || 0,
                avgCost: position.avgCost || 0
            };
        });
    }
}

async function performServerTrade(action) {
    const shares = parseFloat(document.getElementById("sharesInput").value);
    if (!shares || shares <= 0) {
        showToast("Enter a valid number of shares to trade.", "error");
        return;
    }

    const response = await fetch(`/api/trade/${action}/${state.currentTicker}/${shares}`);
    const data = await response.json();
    if (!response.ok || data.error) {
        showToast(data.error || "Trade failed.", "error");
        return;
    }

    state.cash = data.cash;
    state.xp = data.total_xp;
    state.tradeHistory = data.tradeHistory || state.tradeHistory;
    state.positions = {};
    if (data.portfolio) {
        Object.keys(data.portfolio).forEach(symbol => {
            const position = data.portfolio[symbol];
            state.positions[symbol] = {
                shares: position.shares || 0,
                avgCost: position.avgCost || 0
            };
        });
    }
    addActivity(`${action === "buy" ? "Bought" : "Sold"} ${shares} shares of ${state.currentTicker}.`);
    showToast(`${action === "buy" ? "Bought" : "Sold"} ${shares} shares of ${state.currentTicker}`, "success");
    
    // Check for achievements after trade
    if (state.authenticated && !state.is_guest) {
        checkAchievements("trade");
    }
    
    updateUI();
    renderHistory();
}

export async function loadStock(overrideTicker) {
    showLoading();
    const ticker = (overrideTicker || document.getElementById("tickerInput").value.trim() || state.currentTicker).toUpperCase();
    const data = await fetchStock(ticker);

    if (data.error) {
        hideLoading();
        showToast(data.error, "error");
        return;
    }

    state.currentTicker = data.ticker;
    state.currentPrice = data.price;
    state.lastPrices[state.currentTicker] = state.currentPrice;

    document.getElementById("tickerInput").value = state.currentTicker;
    document.getElementById("ticker").innerText = data.ticker;
    document.getElementById("companyName").innerText = data.name;
    document.getElementById("price").innerText = formatMoney(data.price);
    document.getElementById("change").innerText = `${data.change}% today`;
    document.getElementById("open").innerText = formatMoney(data.open);
    document.getElementById("high").innerText = formatMoney(data.high);
    document.getElementById("low").innerText = formatMoney(data.low);
    document.getElementById("quoteTime").innerText = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    drawChart(data.chart);
    addActivity(`Loaded quote for ${state.currentTicker}.`);
    showToast(`Loaded quote for ${state.currentTicker}`, "info");
    hideLoading();
    updateUI();
    renderHistory();
}

export async function buyStock() {
    if (state.authenticated) {
        await performServerTrade("buy");
        return;
    }

    const shares = parseFloat(document.getElementById("sharesInput").value);
    if (!shares || shares <= 0) {
        showToast("Enter a valid number of shares to buy.", "error");
        return;
    }

    const total = shares * state.currentPrice;
    if (total > state.cash) {
        showToast("You do not have enough cash for this purchase.", "error");
        return;
    }

    const current = state.positions[state.currentTicker] || { shares: 0, avgCost: 0 };
    const newShares = current.shares + shares;
    const newAvgCost = newShares === 0 ? 0 : ((current.shares * current.avgCost) + (shares * state.currentPrice)) / newShares;
    state.positions[state.currentTicker] = { shares: newShares, avgCost: newAvgCost };
    state.cash -= total;
    state.xp += 12;
    state.tradeHistory.unshift(`Buy ${shares} ${state.currentTicker} @ ${formatMoney(state.currentPrice)}`);
    if (state.tradeHistory.length > 10) state.tradeHistory.pop();
    addActivity(`Bought ${shares} shares of ${state.currentTicker} at ${formatMoney(state.currentPrice)}.`);
    showToast(`Bought ${shares} shares of ${state.currentTicker}`, "success");
    
    // Check for achievements after trade
    checkAchievements("trade");
    
    updateUI();
    renderHistory();
}

export async function sellStock() {
    if (state.authenticated) {
        await performServerTrade("sell");
        return;
    }

    const shares = parseFloat(document.getElementById("sharesInput").value);
    const position = state.positions[state.currentTicker];

    if (!shares || shares <= 0) {
        showToast("Enter a valid number of shares to sell.", "error");
        return;
    }
    if (!position || position.shares < shares) {
        showToast("You don't own enough shares of this ticker.", "error");
        return;
    }

    const profit = shares * (state.currentPrice - position.avgCost);
    position.shares -= shares;
    if (position.shares <= 0) delete state.positions[state.currentTicker];
    state.cash += shares * state.currentPrice;
    state.xp += 18;
    state.tradeHistory.unshift(`Sell ${shares} ${state.currentTicker} @ ${formatMoney(state.currentPrice)} (${profit >= 0 ? "+" : ""}${formatMoney(profit)})`);
    if (state.tradeHistory.length > 10) state.tradeHistory.pop();
    addActivity(`Sold ${shares} shares of ${state.currentTicker} at ${formatMoney(state.currentPrice)} for ${profit >= 0 ? "+" : ""}${formatMoney(profit)}.`);
    showToast(`Sold ${shares} shares of ${state.currentTicker}`, "success");
    
    // Check for achievements after trade
    checkAchievements("trade");
    
    updateUI();
    renderHistory();
}

export function showHint() {
    const question = state.currentQuestionData;
    if (!question) return;
    const hintText = question.hint || "Think about the key words in the question to choose the best answer.";
    const hint = document.getElementById("quizHint");
    hint.innerText = `Hint: ${hintText}`;
    hint.classList.remove("hidden");
}

function showRewardBanner(message) {
    const banner = document.getElementById("rewardBanner");
    banner.innerText = message;
    banner.classList.remove("hidden");
    banner.classList.add("reward-banner");
    setTimeout(() => {
        banner.classList.add("hidden");
    }, 2600);
}

function hideRewardBanner() {
    const banner = document.getElementById("rewardBanner");
    banner.classList.add("hidden");
}

export async function answerQuiz(index) {
    const question = state.currentQuestionData;
    if (!question) return;

    const selected = state.currentQuizOptionOrder[index] || { index };
    const answeredIndex = selected.index;
    const correctIndex = question.answer;
    const feedback = document.getElementById("quizFeedback");
    const explanationBox = document.getElementById("quizExplanation");
    const nextButton = document.getElementById("nextQuizButton");
    const buttons = document.querySelectorAll(".quizButtons button");

    state.quizTotal += 1;
    if (answeredIndex === correctIndex) {
        state.cash += 250;
        state.xp += 50;
        state.quizCorrect += 1;
        state.quizStreak += 1;
        state.bestQuizStreak = Math.max(state.bestQuizStreak, state.quizStreak);
        feedback.className = "quiz-feedback success";
        feedback.innerText = `Correct! You earned $250 and 50 XP.`;
        addActivity(`Answered quiz correctly: ${question.q}`);
        if (state.quizStreak >= 3) {
            showRewardBanner(`Streak bonus! ${state.quizStreak} correct answers in a row.`);
        }
    } else {
        state.quizStreak = 0;
        feedback.className = "quiz-feedback error";
        feedback.innerText = `Incorrect. The right answer was: ${question.opts[correctIndex]}`;
        addActivity(`Missed quiz question: ${question.q}`);
    }

    explanationBox.innerText = question.explanation || "This answer helps you learn more about the correct choice.";
    explanationBox.classList.remove("hidden");
    nextButton.classList.remove("hidden");
    document.getElementById("showHintButton").disabled = true;
    buttons.forEach(button => {
        button.disabled = true;
    });
    updateUI();
}

export async function nextQuizQuestion() {
    state.currentQuestion = (state.currentQuestion + 1) % quizQuestions.length;
    await loadQuestion();
    updateUI();
}

export async function loadQuestion() {
    state.currentQuestionData = await fetchQuiz(state.currentQuestion);
    state.currentQuizOptionOrder = shuffle(state.currentQuestionData.opts.map((text, index) => ({ text, index })));
    document.getElementById("question").innerText = state.currentQuestionData.q;
    const buttons = document.querySelectorAll(".quizButtons button");
    buttons.forEach((button, index) => {
        button.innerText = state.currentQuizOptionOrder[index].text;
        button.disabled = false;
    });

    document.getElementById("quizFeedback").className = "quiz-feedback";
    document.getElementById("quizFeedback").innerText = "Choose an answer to test your knowledge.";
    document.getElementById("quizExplanation").classList.add("hidden");
    document.getElementById("quizHint").classList.add("hidden");
    document.getElementById("nextQuizButton").classList.add("hidden");
    document.getElementById("rewardBanner").classList.add("hidden");
    document.getElementById("showHintButton").disabled = false;
}

export async function loadLesson(index) {
    const previousIndex = state.lessonIndex;
    state.lessonIndex = index;
    if (state.lessonIndex >= lessons.length) {
        state.lessonIndex = 0;
    }

    if (state.lessonIndex !== previousIndex) {
        state.lessonStreak += 1;
        state.bestLessonStreak = Math.max(state.bestLessonStreak, state.lessonStreak);
        state.lastLessonIndex = state.lessonIndex;
    }

    state.currentLessonData = await fetchLesson(state.lessonIndex);
    document.getElementById("lessonTitle").innerText = state.currentLessonData.title;
    document.getElementById("lessonContent").innerText = state.currentLessonData.content;

    const highlights = document.getElementById("lessonHighlights");
    highlights.innerHTML = "";
    (state.currentLessonData.highlights || []).forEach(point => {
        const item = document.createElement("li");
        item.innerText = point;
        highlights.appendChild(item);
    });

    const example = document.getElementById("lessonExample");
    example.innerHTML = state.currentLessonData.example ? `<strong>Real example:</strong> ${state.currentLessonData.example}` : "";

    const challenge = document.getElementById("lessonChallenge");
    challenge.innerHTML = state.currentLessonData.challenge ? `<strong>Try this:</strong> ${state.currentLessonData.challenge}` : "";

    const lessonBadge = document.getElementById("lessonBadge");
    lessonBadge.innerText = state.currentLessonData.highlights && state.currentLessonData.highlights[0]
        ? `Lesson ${state.lessonIndex + 1} of ${lessons.length} • Focus: ${state.currentLessonData.highlights[0]}`
        : `Lesson ${state.lessonIndex + 1} of ${lessons.length}`;

    document.getElementById("lessonProgress").innerText = `Lesson ${state.lessonIndex + 1} of ${lessons.length}`;
}

export function nextLesson() {
    loadLesson((state.lessonIndex + 1) % lessons.length);
}

export function chooseLesson(index) {
    loadLesson(index);
    addActivity(`Opened lesson ${index + 1}`);
}

export async function chooseQuiz(index) {
    state.currentQuestion = index;
    await loadQuestion();
    addActivity(`Opened quiz ${index + 1}`);
}

export async function loadLessonLibrary() {
    const container = document.getElementById("lessonLibrary");
    const list = await fetchLessons();
    container.innerHTML = "";
    list.forEach((lesson, idx) => {
        const item = document.createElement("button");
        item.className = "activity-row library-button";
        item.type = "button";
        item.innerHTML = `<strong>${idx + 1}. ${lesson.title}</strong>`;
        item.addEventListener("click", () => chooseLesson(idx));
        container.appendChild(item);
    });
}

export async function populateStockDropdown() {
    const select = document.getElementById('stockSelect');
    if (!select) return;
    try {
        const assets = await fetchAssets();
        select.innerHTML = '<option value="">Select a stock...</option>';
        assets.sort((a, b) => a.ticker.localeCompare(b.ticker)).forEach(asset => {
            const opt = document.createElement('option');
            opt.value = asset.ticker;
            opt.text = `${asset.ticker} — ${asset.name}`;
            select.appendChild(opt);
        });
        select.addEventListener('change', (e) => {
            const ticker = e.target.value;
            if (ticker) {
                document.getElementById('tickerInput').value = ticker;
                loadStock(ticker);
            }
        });
    } catch (err) {
        console.error('populateStockDropdown failed', err);
    }
}

export async function loadQuizLibrary() {
    const container = document.getElementById("quizLibrary");
    const list = await fetchQuizzes();
    container.innerHTML = "";
    list.forEach((question, idx) => {
        const item = document.createElement("button");
        item.className = "activity-row library-button";
        item.type = "button";
        item.innerHTML = `<strong>${idx + 1}. ${question.q}</strong>`;
        item.addEventListener("click", () => chooseQuiz(idx));
        container.appendChild(item);
    });
}

export function resetGame() {
    if (!confirm("Reset your portfolio and start again?")) return;
    localStorage.removeItem("apexvestState");
    location.reload();
}

export function drawChart(prices) {
    try {
        const canvas = document.getElementById("chart");
        if (!canvas) return;
        const wrapper = canvas.closest('.chart-wrap');
        if (wrapper) {
            // ensure wrapper has a usable height; let Chart.js handle pixel ratio
            const height = wrapper.clientHeight || 220;
            canvas.style.height = height + 'px';
        }

        console.log('drawChart called, Chart defined?', typeof Chart !== 'undefined');
        console.log('drawChart prices length:', prices && prices.length);
        if (prices && prices.length) {
            const min = Math.min(...prices);
            const max = Math.max(...prices);
            console.log('drawChart min,max:', min, max);
        }

        if (!prices || !Array.isArray(prices) || prices.length === 0) {
            // show empty placeholder by clearing existing chart
            if (window.chart) {
                console.log('drawChart: existing window.chart', window.chart);
                if (typeof window.chart.destroy === 'function') {
                    window.chart.destroy();
                } else {
                    console.warn('drawChart: window.chart has no destroy()', window.chart);
                }
                window.chart = null;
            }
            // draw a simple empty background so the user sees the chart area
            canvas.getContext && canvas.getContext('2d') && canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
            return;
        }

        const ctx = canvas.getContext("2d");
        // draw a small test marker so user can visually confirm canvas is writable
        try {
            ctx.save();
            ctx.fillStyle = '#FF2D55';
            ctx.fillRect(6, 6, 10, 10);
            ctx.restore();
        } catch (e) {
            console.warn('canvas draw test failed', e);
        }
        if (window.chart) {
            console.log('drawChart: existing window.chart before new Chart', window.chart);
            if (typeof window.chart.destroy === 'function') {
                window.chart.destroy();
            } else {
                console.warn('drawChart: existing window.chart has no destroy()', window.chart);
            }
        }

        const hoverDotPlugin = {
            id: 'hoverDot',
            beforeInit(chart) {
                chart._hoverDotIndex = chart.data && chart.data.datasets && chart.data.datasets[0]
                    ? chart.data.datasets[0].data.length - 1
                    : 0;
                const canvas = chart.canvas;
                const handler = function (evt) {
                    const rect = canvas.getBoundingClientRect();
                    const x = evt.clientX - rect.left;
                    const xScale = chart.scales.x;
                    if (!xScale) return;
                    const xValue = xScale.getValueForPixel(x);
                    let idx = Math.round(xValue) - 1;
                    idx = Math.max(0, Math.min(chart.data.datasets[0].data.length - 1, idx));
                    if (chart._hoverDotIndex !== idx) {
                        chart._hoverDotIndex = idx;
                        chart.draw();
                    }
                };
                canvas.addEventListener('mousemove', handler);
                chart._hoverDotHandler = handler;
            },
            beforeDestroy(chart) {
                if (chart._hoverDotHandler && chart.canvas) {
                    chart.canvas.removeEventListener('mousemove', chart._hoverDotHandler);
                }
            },
            afterDraw(chart, args, options) {
                const idx = chart._hoverDotIndex;
                if (idx == null) return;
                const meta = chart.getDatasetMeta(0);
                const pt = meta && meta.data && meta.data[idx];
                if (!pt) return;
                const ctx2 = chart.ctx;
                ctx2.save();
                ctx2.beginPath();
                ctx2.arc(pt.x, pt.y, options && options.radius ? options.radius : 6, 0, 2 * Math.PI);
                ctx2.fillStyle = (options && options.color) || '#FFFFFF';
                ctx2.fill();
                ctx2.lineWidth = (options && options.borderWidth) || 2;
                ctx2.strokeStyle = (options && options.borderColor) || 'rgba(0,0,0,0.18)';
                ctx2.stroke();
                ctx2.restore();
            }
        };

        window.chart = new Chart(ctx, {
            plugins: [hoverDotPlugin],
            type: "line",
            data: {
                labels: prices.map((_, index) => index + 1),
                datasets: [{
                    data: prices,
                    borderColor: "#FFFFFF",
                    backgroundColor: "rgba(255,255,255,0.06)",
                    fill: false,
                    borderWidth: 3,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: "#FFFFFF",
                    pointHoverBorderColor: "#FFFFFF",
                    tension: 0.35
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {
                    mode: 'nearest',
                    intersect: false
                },
                plugins: {
                    legend: { display: false },
                    hoverDot: { color: '#FFFFFF', radius: 6, borderColor: 'rgba(0,0,0,0.18)', borderWidth: 2 },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                    }
                },
                scales: {
                    x: { display: false },
                    y: {
                        ticks: { color: "#E2E8F0" },
                        grid: { color: "rgba(148,163,184,0.12)" }
                    }
                }
            }
        });
    } catch (err) {
        console.error('drawChart error:', err);
    }
}

window.loadStock = loadStock;
window.buyStock = buyStock;
window.sellStock = sellStock;
window.showHint = showHint;
window.answerQuiz = answerQuiz;
window.nextQuizQuestion = nextQuizQuestion;
window.nextLesson = nextLesson;
window.resetGame = resetGame;

window.onload = async () => {
    const user = await fetchUserState();
    if (user && user.authenticated) {
        hydrateStateFromServer(user);
    } else {
        loadState();
    }
    renderGlossary();
    renderHistory();
    document.getElementById("tickerInput").value = state.currentTicker;
    await Promise.all([
        populateStockDropdown(),
        loadStock(),
        loadQuestion(),
        loadLesson(state.lessonIndex),
        loadLessonLibrary(),
        loadQuizLibrary()
    ]);
    loadTip();
    updateUI();
    
    // Load additional features
    loadDailyChallenges();
    loadStreaks();
    loadWatchlist();
    loadMarketNews();
    loadPortfolioAnalytics();
};
