// API Base URL
const API_URL = 'http://localhost:8000';

// State
let currentUser = null;
let currentQuestion = 1;
const totalQuestions = 10;
let currentMoodLogId = null;
let currentSessionId = null;
let currentMood = null;

// DOM Elements
const authSection = document.getElementById('auth-section');
const quizSection = document.getElementById('quiz-section');
const resultSection = document.getElementById('result-section');
const historySection = document.getElementById('history-section');
const chatSection = document.getElementById('chat-section');
const loadingOverlay = document.getElementById('loading-overlay');

// Auth Elements
const usernameInput = document.getElementById('username-input');
const checkUserBtn = document.getElementById('check-user-btn');
const authMessage = document.getElementById('auth-message');
const authActions = document.getElementById('auth-actions');
const signupBtn = document.getElementById('signup-btn');
const loginBtn = document.getElementById('login-btn');

// Quiz Elements
const quizForm = document.getElementById('quiz-form');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const submitBtn = document.getElementById('submit-btn');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

// Result Elements
const moodIcon = document.getElementById('mood-icon');
const moodText = document.getElementById('mood-text');
const moodDescription = document.getElementById('mood-description');
const moodResult = document.getElementById('mood-result');
const retakeBtn = document.getElementById('retake-btn');
const historyBtn = document.getElementById('history-btn');
const logoutBtn = document.getElementById('logout-btn');

// History Elements
const historyList = document.getElementById('history-list');
const noHistory = document.getElementById('no-history');
const backBtn = document.getElementById('back-btn');

// Mood Data
const moodData = {
    'Happy/Calm': {
        icon: '😊',
        class: 'happy',
        description: 'You\'re feeling positive and at peace. Keep nurturing this state with activities you enjoy!'
    },
    'Neutral': {
        icon: '😐',
        class: 'neutral',
        description: 'You\'re in a balanced state. This is a good baseline - consider activities that bring you joy.'
    },
    'Stressed': {
        icon: '😰',
        class: 'stressed',
        description: 'You\'re experiencing stress. Take some deep breaths and consider relaxation techniques.'
    },
    'Depressed/Low': {
        icon: '😔',
        class: 'depressed',
        description: 'You\'re feeling low. Remember, it\'s okay to seek support. Consider talking to someone you trust.'
    },
    'Tired/Exhausted': {
        icon: '😴',
        class: 'tired',
        description: 'Your energy is depleted. Prioritize rest and self-care to recharge your batteries.'
    }
};

// Chat Elements
const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const typingIndicator = document.getElementById('typing-indicator');
const endChatBtn = document.getElementById('end-chat-btn');
const talkBtn = document.getElementById('talk-btn');
const chatMoodBadge = document.getElementById('chat-mood-badge');

// Helper Functions
function showSection(section) {
    [authSection, quizSection, resultSection, historySection, chatSection].forEach(s => {
        s.classList.add('hidden');
    });
    section.classList.remove('hidden');
}

function showMessage(message, type = 'info') {
    authMessage.textContent = message;
    authMessage.className = `message ${type}`;
    authMessage.classList.remove('hidden');
}

function hideMessage() {
    authMessage.classList.add('hidden');
}

function showLoading() {
    loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    loadingOverlay.classList.add('hidden');
}

function updateProgress() {
    const percentage = (currentQuestion / totalQuestions) * 100;
    progressFill.style.width = `${percentage}%`;
    progressText.textContent = `Question ${currentQuestion} of ${totalQuestions}`;
}

function showQuestion(num) {
    document.querySelectorAll('.question-slide').forEach(slide => {
        slide.classList.add('hidden');
    });
    document.querySelector(`[data-question="${num}"]`).classList.remove('hidden');

    // Update navigation buttons
    prevBtn.classList.toggle('hidden', num === 1);
    nextBtn.classList.toggle('hidden', num === totalQuestions);
    submitBtn.classList.toggle('hidden', num !== totalQuestions);

    updateProgress();
}

function isQuestionAnswered(num) {
    return document.querySelector(`input[name="q${num}"]:checked`) !== null;
}

function getAnswers() {
    const answers = {};
    for (let i = 1; i <= totalQuestions; i++) {
        const selected = document.querySelector(`input[name="q${i}"]:checked`);
        if (selected) {
            answers[`q${i}`] = selected.value;
        }
    }
    return answers;
}

function resetQuiz() {
    currentQuestion = 1;
    quizForm.reset();
    showQuestion(1);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// API Functions
async function checkUser(username) {
    try {
        const response = await fetch(`${API_URL}/check-user/${encodeURIComponent(username)}`);
        return await response.json();
    } catch (error) {
        console.error('Error checking user:', error);
        throw error;
    }
}

async function signup(username) {
    try {
        const response = await fetch(`${API_URL}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        return await response.json();
    } catch (error) {
        console.error('Error signing up:', error);
        throw error;
    }
}

async function login(username) {
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        return await response.json();
    } catch (error) {
        console.error('Error logging in:', error);
        throw error;
    }
}

async function detectMood(username, answers) {
    try {
        const response = await fetch(`${API_URL}/detect-mood`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, answers })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        return await response.json();
    } catch (error) {
        console.error('Error detecting mood:', error);
        throw error;
    }
}

async function getMoodHistory(username) {
    try {
        const response = await fetch(`${API_URL}/mood-history/${encodeURIComponent(username)}`);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }
        return await response.json();
    } catch (error) {
        console.error('Error getting history:', error);
        throw error;
    }
}

// Event Handlers
checkUserBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    if (!username) {
        showMessage('Please enter a username', 'error');
        return;
    }

    hideMessage();
    checkUserBtn.disabled = true;
    checkUserBtn.textContent = 'Checking...';

    try {
        const result = await checkUser(username);

        if (result.exists) {
            showMessage(`Welcome back, ${username}!`, 'success');
            loginBtn.classList.remove('hidden');
            signupBtn.classList.add('hidden');
            checkUserBtn.classList.add('hidden');  // Hide continue button
        } else {
            showMessage(`Username available! Click Sign Up to create your account.`, 'info');
            signupBtn.classList.remove('hidden');
            loginBtn.classList.add('hidden');
            checkUserBtn.classList.add('hidden');  // Hide continue button
        }
        authActions.classList.remove('hidden');
    } catch (error) {
        showMessage('Error connecting to server. Please try again.', 'error');
        checkUserBtn.disabled = false;
        checkUserBtn.textContent = 'Continue';
    }
});

signupBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    signupBtn.disabled = true;
    signupBtn.textContent = 'Creating...';

    try {
        await signup(username);
        currentUser = username;
        showSection(quizSection);
        resetQuiz();
    } catch (error) {
        showMessage(error.message, 'error');
    } finally {
        signupBtn.disabled = false;
        signupBtn.textContent = 'Sign Up';
    }
});

loginBtn.addEventListener('click', async () => {
    const username = usernameInput.value.trim();
    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';

    try {
        await login(username);
        currentUser = username;
        showSection(quizSection);
        resetQuiz();
    } catch (error) {
        showMessage(error.message, 'error');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
});

usernameInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        checkUserBtn.click();
    }
});

usernameInput.addEventListener('input', () => {
    hideMessage();
    authActions.classList.add('hidden');
    checkUserBtn.classList.remove('hidden');
    checkUserBtn.disabled = false;
    checkUserBtn.textContent = 'Continue';
});

prevBtn.addEventListener('click', () => {
    if (currentQuestion > 1) {
        currentQuestion--;
        showQuestion(currentQuestion);
    }
});

nextBtn.addEventListener('click', () => {
    if (!isQuestionAnswered(currentQuestion)) {
        alert('Please select an answer before continuing.');
        return;
    }
    if (currentQuestion < totalQuestions) {
        currentQuestion++;
        showQuestion(currentQuestion);
    }
});

quizForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Validate all questions answered
    for (let i = 1; i <= totalQuestions; i++) {
        if (!isQuestionAnswered(i)) {
            alert(`Please answer question ${i}`);
            currentQuestion = i;
            showQuestion(i);
            return;
        }
    }

    const answers = getAnswers();
    showLoading();

    try {
        const result = await detectMood(currentUser, answers);
        currentMoodLogId = result.log_id;
        currentMood = result.mood;
        displayResult(result.mood);
    } catch (error) {
        alert('Error analyzing mood: ' + error.message);
    } finally {
        hideLoading();
    }
});

function displayResult(mood) {
    const data = moodData[mood] || moodData['Neutral'];

    moodIcon.textContent = data.icon;
    moodText.textContent = mood;
    moodDescription.textContent = data.description;

    // Update mood result styling
    moodResult.className = `mood-result ${data.class}`;

    showSection(resultSection);
}

// ============== CHAT FUNCTIONS ==============

async function startChatSession() {
    try {
        const response = await fetch(`${API_URL}/chat/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: currentUser,
                mood_log_id: currentMoodLogId
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        return await response.json();
    } catch (error) {
        console.error('Error starting chat:', error);
        throw error;
    }
}

async function sendChatMessage(message) {
    try {
        const response = await fetch(`${API_URL}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentSessionId,
                message: message
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail);
        }

        return await response.json();
    } catch (error) {
        console.error('Error sending message:', error);
        throw error;
    }
}

async function endChatSession() {
    try {
        await fetch(`${API_URL}/chat/end/${currentSessionId}`, {
            method: 'POST'
        });
    } catch (error) {
        console.error('Error ending chat:', error);
    }
}

function addMessageToChat(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}`;

    const avatar = role === 'assistant' ? '👩‍⚕️' : '👤';
    const time = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-bubble">
            <div class="message-content">${formatMessageContent(content)}</div>
            <div class="message-time">${time}</div>
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessageContent(content) {
    // Convert line breaks to <br> and basic markdown
    return content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

function showTypingIndicator() {
    typingIndicator.classList.remove('hidden');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    typingIndicator.classList.add('hidden');
}

function clearChat() {
    chatMessages.innerHTML = '';
}

function updateChatMoodBadge(mood) {
    const data = moodData[mood] || moodData['Neutral'];
    chatMoodBadge.textContent = mood;
    chatMoodBadge.className = `mood-badge ${data.class}`;
}

// Chat Event Handlers
talkBtn.addEventListener('click', async () => {
    showLoading();

    try {
        const result = await startChatSession();
        currentSessionId = result.session_id;

        // Clear previous messages and setup
        clearChat();
        updateChatMoodBadge(result.mood);

        // Show chat section
        showSection(chatSection);

        // Add the greeting message
        addMessageToChat('assistant', result.greeting);

    } catch (error) {
        alert('Error starting chat session: ' + error.message);
    } finally {
        hideLoading();
    }
});

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    // Add user message to chat
    addMessageToChat('user', message);
    chatInput.value = '';

    // Show typing indicator
    showTypingIndicator();

    try {
        const result = await sendChatMessage(message);
        hideTypingIndicator();
        addMessageToChat('assistant', result.response);
    } catch (error) {
        hideTypingIndicator();
        addMessageToChat('assistant', 'I apologize, but I encountered an issue. Please try again.');
    }
});

endChatBtn.addEventListener('click', async () => {
    if (confirm('Are you sure you want to end this session?')) {
        await endChatSession();
        currentSessionId = null;
        showSection(resultSection);
    }
});

retakeBtn.addEventListener('click', () => {
    resetQuiz();
    showSection(quizSection);
});

historyBtn.addEventListener('click', async () => {
    showLoading();
    try {
        const data = await getMoodHistory(currentUser);
        displayHistory(data);
    } catch (error) {
        alert('Error loading history: ' + error.message);
    } finally {
        hideLoading();
    }
});

function displayHistory(data) {
    historyList.innerHTML = '';

    if (data.history.length === 0) {
        noHistory.classList.remove('hidden');
    } else {
        noHistory.classList.add('hidden');

        data.history.forEach(item => {
            const moodInfo = moodData[item.mood] || moodData['Neutral'];
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <span class="history-icon">${moodInfo.icon}</span>
                <div class="history-info">
                    <div class="history-mood">${item.mood}</div>
                    <div class="history-date">${formatDate(item.created_at)}</div>
                </div>
            `;
            historyList.appendChild(historyItem);
        });
    }

    showSection(historySection);
}

backBtn.addEventListener('click', () => {
    showSection(resultSection);
});

logoutBtn.addEventListener('click', () => {
    currentUser = null;
    usernameInput.value = '';
    hideMessage();
    authActions.classList.add('hidden');
    showSection(authSection);
});


// Add to moodData object
const recommendationData = {
    'Stressed': [
        'Practice 10 minutes of deep breathing daily',
        'Try progressive muscle relaxation',
        'Consider time management techniques'
    ],
    'Depressed/Low': [
        'Connect with friends or family',
        'Engage in physical activity',
        'Practice gratitude journaling'
    ],
    'Tired/Exhausted': [
        'Ensure 7-8 hours of quality sleep',
        'Take short breaks during work',
        'Stay hydrated and eat balanced meals'
    ],
    'Neutral': [
        'Maintain your current routine',
        'Try a new hobby or activity',
        'Practice mindfulness meditation'
    ],
    'Happy/Calm': [
        'Continue your positive habits',
        'Share your positivity with others',
        'Set new personal goals'
    ]
};

// Add report button to result section HTML
// Add this button to result-actions div:
// <button id="report-btn" class="btn btn-info">Weekly Report</button>

// Add event handler
document.getElementById('report-btn').addEventListener('click', async () => {
    showLoading();
    try {
        const report = await getWeeklyReport(currentUser);
        displayWeeklyReport(report);
    } catch (error) {
        alert('Error generating report: ' + error.message);
    } finally {
        hideLoading();
    }
});

async function getWeeklyReport(username) {
    const response = await fetch(`${API_URL}/weekly-report/${encodeURIComponent(username)}`);
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail);
    }
    return await response.json();
}

function displayWeeklyReport(report) {
    // Create and show report modal or new section
    const reportHTML = `
        <div class="report-modal">
            <h2>Weekly Mood Report</h2>
            <div class="report-period">${report.period}</div>
            <div class="report-summary">
                <div class="report-stat">Total Entries: ${report.total_entries}</div>
                <div class="report-stat">Trend: ${report.mood_trend}</div>
            </div>
            <div class="mood-distribution">
                <h3>Mood Distribution</h3>
                ${Object.entries(report.mood_distribution).map(([mood, count]) => `
                    <div class="mood-dist-item">
                        <span class="mood-name">${mood}</span>
                        <span class="mood-count">${count}</span>
                    </div>
                `).join('')}
            </div>
            <div class="insights">
                <h3>Insights</h3>
                ${report.insights.map(insight => `<div class="insight">${insight}</div>`).join('')}
            </div>
            <div class="recommendations">
                <h3>Recommendations</h3>
                ${report.recommendations.map(rec => `<div class="recommendation">${rec}</div>`).join('')}
            </div>
        </div>
    `;
    // Implement modal display logic
}

// Initialize
showQuestion(1);
