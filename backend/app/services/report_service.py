from database import get_user_mood_history, get_user
from typing import Dict, List
import json

def generate_weekly_report(username: str) -> Dict:
    """
    Generate a simple weekly report using available mood data
    """
    print(f"Generating report for: {username}")
    
    user = get_user(username)
    if not user:
        raise ValueError("User not found")
    
    # Get all mood history
    mood_history = get_user_mood_history(username)
    print(f"Found {len(mood_history)} mood entries")
    
    # Use all available data for the report
    recent_mood_history = mood_history
    
    # Calculate mood distribution
    mood_distribution = {}
    for entry in recent_mood_history:
        mood = entry['mood']
        mood_distribution[mood] = mood_distribution.get(mood, 0) + 1
    
    # Generate insights based on current mood
    insights = []
    if recent_mood_history:
        latest_mood = recent_mood_history[0]['mood']  # Most recent mood
        insights.append(f"Based on your recent assessment, you're feeling {latest_mood}.")
        insights.append(f"You've completed {len(recent_mood_history)} mood assessment(s) total.")
        
        if len(recent_mood_history) > 1:
            insights.append("Regular tracking helps identify patterns in your mental wellbeing.")
        else:
            insights.append("Consider tracking your mood regularly to see patterns over time.")
    else:
        insights.append("No mood data available yet. Complete an assessment to get insights.")
    
    # Generate recommendations based on mood
    recommendations = generate_recommendations(mood_distribution)
    
    # Simple trend calculation
    mood_trend = "New user - establish baseline"
    if len(recent_mood_history) > 1:
        mood_trend = "Building your mood history"
    
    return {
        "username": username,
        "period": "Current Session",
        "total_entries": len(recent_mood_history),
        "mood_distribution": mood_distribution,
        "insights": insights,
        "recommendations": recommendations,
        "mood_trend": mood_trend
    }

def generate_recommendations(mood_distribution: Dict) -> List[str]:
    """Generate recommendations based on mood patterns"""
    recommendations = []
    
    if not mood_distribution:
        return [
            "Complete your first mood assessment to get personalized recommendations",
            "Regular tracking helps identify patterns in your mental health",
            "Consider setting a daily reminder for mood check-ins"
        ]
    
    # Get the most recent mood (first one in distribution)
    current_mood = list(mood_distribution.keys())[0] if mood_distribution else "Neutral"
    
    mood_suggestions = {
        'Happy/Calm': [
            "Great! Continue practicing self-care and mindfulness",
            "Share your positive energy with others",
            "Maintain your healthy routines"
        ],
        'Neutral': [
            "Try adding one enjoyable activity to your day",
            "Practice mindfulness to enhance emotional awareness",
            "Set small, achievable goals"
        ],
        'Stressed': [
            "Take 5-minute breaks for deep breathing",
            "Break tasks into smaller steps",
            "Prioritize self-care activities"
        ],
        'Depressed/Low': [
            "Reach out to supportive people",
            "Engage in gentle physical activity",
            "Be kind to yourself - difficult days are normal"
        ],
        'Tired/Exhausted': [
            "Focus on getting quality sleep",
            "Take short rest breaks during the day",
            "Stay hydrated and eat nutritious meals"
        ]
    }
    
    # Add mood-specific recommendations
    if current_mood in mood_suggestions:
        recommendations.extend(mood_suggestions[current_mood])
    else:
        recommendations.extend([
            "Practice gratitude daily",
            "Stay connected with supportive people",
            "Maintain a consistent sleep schedule"
        ])
    
    # Add general wellness tips
    recommendations.extend([
        "Stay hydrated throughout the day",
        "Take short walks for mental clarity",
        "Limit screen time before bed"
    ])
    
    return recommendations[:4]  # Return top 4 recommendations