const API_URL = 'http://localhost:8000';

// Question Data - All 10 questions in one array
const questions = [
    {
        number: 1,
        category: "Emotional Check-in",
        text: "How are you feeling right now?",
        options: [
            { value: "A", label: "Calm" },
            { value: "B", label: "Neutral" },
            { value: "C", label: "Sad" },
            { value: "D", label: "Stressed" },
            { value: "E", label: "Overwhelmed" },
            { value: "F", label: "Happy" }
        ]
    },
    {
        number: 2,
        category: "Emotional Check-in",
        text: "Which emotion describes you best today?",
        options: [
            { value: "A", label: "Anxious" },
            { value: "B", label: "Tired" },
            { value: "C", label: "Low mood" },
            { value: "D", label: "Confident" },
            { value: "E", label: "Irritable" },
            { value: "F", label: "Content" }
        ]
    },
    {
        number: 3,
        category: "Stress Check",
        text: "How stressed do you feel today?",
        options: [
            { value: "A", label: "Very low" },
            { value: "B", label: "Low" },
            { value: "C", label: "Moderate" },
            { value: "D", label: "High" },
            { value: "E", label: "Very high" }
        ]
    },
    {
        number: 4,
        category: "Stress Check",
        text: "Are you experiencing physical symptoms of stress?",
        options: [
            { value: "A", label: "No symptoms" },
            { value: "B", label: "Mild fatigue/headache" },
            { value: "C", label: "Restlessness or tension" },
            { value: "D", label: "Trouble focusing" },
            { value: "E", label: "Unable to relax / very tense" }
        ]
    },
    {
        number: 5,
        category: "Mood & Motivation",
        text: "How motivated do you feel today?",
        options: [
            { value: "A", label: "Very motivated" },
            { value: "B", label: "Somewhat motivated" },
            { value: "C", label: "Neutral" },
            { value: "D", label: "Low motivation" },
            { value: "E", label: "No motivation at all" }
        ]
    },
    {
        number: 6,
        category: "Mood & Motivation",
        text: "Have you enjoyed your usual activities lately?",
        options: [
            { value: "A", label: "Yes, completely" },
            { value: "B", label: "Mostly" },
            { value: "C", label: "Sometimes" },
            { value: "D", label: "Rarely" },
            { value: "E", label: "Not at all" }
        ]
    },
    {
        number: 7,
        category: "Mood & Motivation",
        text: "How would you describe your mental energy?",
        options: [
            { value: "A", label: "Energized" },
            { value: "B", label: "Okay" },
            { value: "C", label: "A bit drained" },
            { value: "D", label: "Exhausted" },
            { value: "E", label: "Burned out" }
        ]
    },
    {
        number: 8,
        category: "Cognitive State",
        text: "How clear is your thinking today?",
        options: [
            { value: "A", label: "Very clear" },
            { value: "B", label: "Mostly clear" },
            { value: "C", label: "A bit foggy" },
            { value: "D", label: "Confused" },
            { value: "E", label: "Overwhelmed" }
        ]
    },
    {
        number: 9,
        category: "Social & Emotional Safety",
        text: "How connected do you feel to people around you?",
        options: [
            { value: "A", label: "Very connected" },
            { value: "B", label: "Somewhat connected" },
            { value: "C", label: "Neutral" },
            { value: "D", label: "A bit isolated" },
            { value: "E", label: "Very isolated" }
        ]
    },
    {
        number: 10,
        category: "Social & Emotional Safety",
        text: "How out of control do your emotions feel today?",
        options: [
            { value: "A", label: "Very stable" },
            { value: "B", label: "Mostly stable" },
            { value: "C", label: "Somewhat unstable" },
            { value: "D", label: "Unstable" },
            { value: "E", label: "Very unstable" }
        ]
    }
];

// State
let currentQuestionIndex = 0;
let userAnswers = JSON.parse(localStorage.getItem('moodAnswers') || '{}');

// DOM Elements
const questionElement = document.getElementById('questionElement');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');

// Initialize the questionnaire
function initQuestionnaire() {
    loadQuestion(currentQuestionIndex);
    updateProgress();
    updateNavigation();
}

// Load question
function loadQuestion(index) {
    const question = questions[index];
    
    let questionHTML = `
        <div class="question-category">${question.category}</div>
        <div class="question-text">${question.text}</div>
        <div class="options">
    `;
    
    question.options.forEach(option => {
        const isSelected = userAnswers[`q${question.number}`] === option.value;
        questionHTML += `
            <div class="option ${isSelected ? 'selected' : ''}" onclick="selectOption('${option.value}', ${question.number})">
                ${option.label}
            </div>
        `;
    });
    
    questionHTML += `</div>`;
    questionElement.innerHTML = questionHTML;
    
    updateNavigation();
}

// Select an option
function selectOption(value, questionNumber) {
    userAnswers[`q${questionNumber}`] = value;
    localStorage.setItem('moodAnswers', JSON.stringify(userAnswers));
    loadQuestion(currentQuestionIndex);
}

// Next question
function nextQuestion() {
    const currentQuestion = questions[currentQuestionIndex];
    
    if (!userAnswers[`q${currentQuestion.number}`]) {
        alert('Please select an answer before continuing.');
        return;
    }
    
    if (currentQuestionIndex < questions.length - 1) {
        currentQuestionIndex++;
        loadQuestion(currentQuestionIndex);
        updateProgress();
    } else {
        submitQuiz();
    }
}

// Previous question
function previousQuestion() {
    if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        loadQuestion(currentQuestionIndex);
        updateProgress();
    }
}

// Update progress bar
function updateProgress() {
    const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
    progressBar.style.width = `${progress}%`;
    progressText.textContent = `Question ${currentQuestionIndex + 1} of ${questions.length}`;
}

// Update navigation buttons
function updateNavigation() {
    const isFirstQuestion = currentQuestionIndex === 0;
    const isLastQuestion = currentQuestionIndex === questions.length - 1;
    
    prevBtn.disabled = isFirstQuestion;
    
    if (isLastQuestion) {
        nextBtn.textContent = 'See Results';
    } else {
        nextBtn.textContent = 'Next Question';
    }
}

// Submit all answers to API
async function submitQuiz() {
    // Validate all questions are answered
    for (let i = 0; i < questions.length; i++) {
        if (!userAnswers[`q${questions[i].number}`]) {
            alert(`Please answer question ${questions[i].number}`);
            currentQuestionIndex = i;
            loadQuestion(i);
            updateNavigation();
            return;
        }
    }
    
    const username = localStorage.getItem('currentUser') || sessionStorage.getItem('currentUser');
    if (!username) {
        alert('Please login again.');
        window.location.href = 'login.html';  // CHANGED TO login.html
        return;
    }
    
    try {
        // Show loading state
        document.body.style.cursor = 'wait';
        nextBtn.disabled = true;
        nextBtn.textContent = 'Analyzing...';
        
        // Send to backend API
        const response = await fetch(`${API_URL}/detect-mood`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({ 
                username: username, 
                answers: userAnswers 
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Server error');
        }
        
        const result = await response.json();
        
        // Save mood result for results page
        localStorage.setItem('currentMood', result.mood);
        localStorage.setItem('currentMoodLogId', result.log_id);
        
        // Clear answers for next time
        localStorage.removeItem('moodAnswers');
        
        // Redirect to results page
        window.location.href = 'results.html';
        
    } catch (error) {
        console.error('Error analyzing mood:', error);
        alert('Error analyzing your mood: ' + error.message);
        
        // Fallback: Show basic results based on answers
        showBasicResults();
        
    } finally {
        document.body.style.cursor = 'default';
        nextBtn.disabled = false;
        nextBtn.textContent = 'See Results';
    }
}

// Fallback function if API fails
function showBasicResults() {
    // Simple scoring logic based on answers
    let totalScore = 0;
    const answerValues = Object.values(userAnswers);
    
    answerValues.forEach(answer => {
        // Convert A=1, B=2, C=3, D=4, E=5, F=6 for scoring
        const score = answer.charCodeAt(0) - 64; // A=1, B=2, etc.
        totalScore += score;
    });
    
    const averageScore = totalScore / questions.length;
    let mood = '';
    
    if (averageScore <= 2) {
        mood = 'Positive';
    } else if (averageScore <= 3.5) {
        mood = 'Neutral';
    } else {
        mood = 'Needs Support';
    }
    
    // Save basic results
    localStorage.setItem('currentMood', mood);
    localStorage.setItem('currentMoodLogId', 'local-' + Date.now());
    localStorage.removeItem('moodAnswers');
    
    // Redirect to results page
    window.location.href = 'results.html';
}

// Logout function
function logout() {
    if (confirm('Are you sure you want to logout?')) {
        localStorage.removeItem('currentUser');
        sessionStorage.removeItem('currentUser');
        localStorage.removeItem('moodAnswers');
        window.location.href = 'login.html';  // CHANGED TO login.html
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initQuestionnaire);