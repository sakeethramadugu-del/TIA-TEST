import { lessons, quizQuestions } from "./data.js";

export async function fetchStock(ticker) {
    const response = await fetch(`/stock/${ticker}`);
    return response.json();
}

export async function fetchLesson(index) {
    try {
        const response = await fetch(`/lesson/${index}`);
        const lesson = await response.json();
        return lesson.error ? lessons[index] : lesson;
    } catch (error) {
        return lessons[index];
    }
}

export async function fetchQuiz(index) {
    try {
        const response = await fetch(`/quiz/${index}`);
        const question = await response.json();
        return question.error ? quizQuestions[index] : question;
    } catch (error) {
        return quizQuestions[index];
    }
}

export async function fetchLessons() {
    const response = await fetch("/lessons");
    const data = await response.json();
    return data.error ? lessons : data;
}

export async function fetchQuizzes() {
    const response = await fetch("/quizzes");
    const data = await response.json();
    return data.error ? quizQuestions : data;
}

export async function fetchAssets() {
    try {
        const response = await fetch('/api/assets');
        const data = await response.json();
        return data.error ? [] : data.assets;
    } catch (err) {
        return [];
    }
}
