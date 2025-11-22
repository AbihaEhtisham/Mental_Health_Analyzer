// In results.html - Update the moodConfig to match LLM output
const moodConfig = {
    'Happy/Calm': {
        emoji: '😊',
        title: 'Happy & Calm',
        description: 'Your responses indicate excellent mental wellbeing! You\'re experiencing positive emotions, good stress management, and healthy coping mechanisms. Continue practicing self-care and mindfulness to maintain this wonderful balance.',
        score: 'Excellent Mood'
    },
    'Neutral': {
        emoji: '😐',
        title: 'Neutral & Stable',
        description: 'You\'re in a stable emotional state with balanced moods. While not experiencing extreme highs or lows, you might benefit from incorporating more joyful activities into your routine to enhance overall satisfaction.',
        score: 'Stable Mood'
    },
    'Stressed': {
        emoji: '😥',
        title: 'Stressed & Overwhelmed',
        description: 'You appear to be dealing with significant stress. Break tasks into smaller steps, practice time management, and ensure you\'re getting adequate rest. Remember to prioritize self-care during demanding times.',
        score: 'High Stress'
    },
    'Depressed/Low': {
        emoji: '😔',
        title: 'Feeling Low',
        description: 'You seem to be experiencing some emotional discomfort or low mood. Remember that it\'s okay to feel this way sometimes. Consider reaching out to supportive people or engaging in activities that usually lift your spirits.',
        score: 'Needs Support'
    },
    'Tired/Exhausted': {
        emoji: '😴',
        title: 'Fatigued & Drained',
        description: 'Your energy levels seem low, which can affect mood and motivation. Focus on getting quality sleep, proper nutrition, and gentle movement. Consider whether you need more rest or a change in routine.',
        score: 'Low Energy'
    }
};

// Function to display mood results
function displayMoodResult(mood) {
    const moodData = moodConfig[mood] || moodConfig['Neutral'];
    
    const moodIcon = document.getElementById('mood-icon');
    const moodText = document.getElementById('mood-text');
    const moodScore = document.getElementById('mood-score');
    const moodDescription = document.getElementById('mood-description');
    const moodResult = document.getElementById('mood-result');

    // Update content
    moodIcon.textContent = moodData.emoji;
    moodText.textContent = moodData.title;
    moodScore.textContent = moodData.score;
    moodDescription.textContent = moodData.description;

    // Update styling based on mood type
    moodResult.className = 'mood-result';
    if (mood === 'Happy/Calm') {
        moodResult.classList.add('mood-positive');
    } else if (mood === 'Neutral') {
        moodResult.classList.add('mood-neutral');
    } else {
        moodResult.classList.add('mood-support');
    }
}