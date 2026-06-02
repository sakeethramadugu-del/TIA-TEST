import { startingCash } from "./data.js";

export const state = {
    startingCash,
    cash: startingCash,
    xp: 0,
    positions: {},
    lastPrices: {},
    activityLog: [],
    tradeHistory: [],
    currentTicker: "AAPL",
    currentPrice: 0,
    currentQuestion: 0,
    currentQuestionData: null,
    currentQuizOptionOrder: [],
    lessonIndex: 0,
    lastLessonIndex: 0,
    quizCorrect: 0,
    quizTotal: 0,
    quizStreak: 0,
    bestQuizStreak: 0,
    lessonStreak: 0,
    bestLessonStreak: 0,
    goalAwarded: false,
    authenticated: false
};

const storageKey = "apexvestState";

export function loadState() {
    const saved = localStorage.getItem(storageKey);
    if (!saved) return;

    try {
        const savedState = JSON.parse(saved);
        Object.keys(savedState).forEach(key => {
            if (key in state) {
                state[key] = savedState[key];
            }
        });
    } catch (error) {
        console.warn("Failed to load saved state", error);
    }
}

export function saveState() {
    const savedState = {
        cash: state.cash,
        xp: state.xp,
        positions: state.positions,
        lastPrices: state.lastPrices,
        activityLog: state.activityLog,
        tradeHistory: state.tradeHistory,
        currentTicker: state.currentTicker,
        currentPrice: state.currentPrice,
        currentQuestion: state.currentQuestion,
        lessonIndex: state.lessonIndex,
        lastLessonIndex: state.lastLessonIndex,
        quizCorrect: state.quizCorrect,
        quizTotal: state.quizTotal,
        quizStreak: state.quizStreak,
        bestQuizStreak: state.bestQuizStreak,
        lessonStreak: state.lessonStreak,
        bestLessonStreak: state.bestLessonStreak,
        goalAwarded: state.goalAwarded
    };
    localStorage.setItem(storageKey, JSON.stringify(savedState));
}
