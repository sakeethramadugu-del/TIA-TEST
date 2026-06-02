import { lessons, quizQuestions } from "./data.js";

async function safeFetchJSON(path, options = {}) {
    try {
        const response = await fetch(path, {
            headers: { "Content-Type": "application/json" },
            ...options
        });
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`Failed fetch ${path}:`, error);
        return { error: "Request failed", status: "error" };
    }
}

export async function fetchStock(ticker) {
    return safeFetchJSON(`/stock/${ticker}`);
}

export async function fetchLesson(index) {
    try {
        const response = await safeFetchJSON(`/lesson/${index}`);
        return response.error ? lessons[index] : response;
    } catch (error) {
        return lessons[index];
    }
}

export async function fetchQuiz(index) {
    try {
        const response = await safeFetchJSON(`/quiz/${index}`);
        return response.error ? quizQuestions[index] : response;
    } catch (error) {
        return quizQuestions[index];
    }
}

export async function fetchLessons() {
    try {
        const data = await safeFetchJSON("/lessons");
        return data.error ? lessons : data;
    } catch (error) {
        return lessons;
    }
}

export async function fetchQuizzes() {
    try {
        const data = await safeFetchJSON("/quizzes");
        return data.error ? quizQuestions : data;
    } catch (error) {
        return quizQuestions;
    }
}

export async function fetchAssets() {
    try {
        const data = await safeFetchJSON('/api/assets');
        return data.error ? [] : data.assets || [];
    } catch (err) {
        return [];
    }
}
