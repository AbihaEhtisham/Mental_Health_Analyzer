from datetime import datetime, timedelta
import sys
import os

# Add the current directory to Python path so we can import from the same folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection
from typing import Dict, List

def generate_weekly_report(username: str) -> Dict:
    """Generate weekly mood report with insights and recommendations"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get last 7 days of mood data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    cursor.execute("""
        SELECT mood, created_at, answers
        FROM mood_logs ml
        JOIN users u ON ml.user_id = u.id
        WHERE u.username = ? AND date(ml.created_at) BETWEEN date(?) AND date(?)
        ORDER BY ml.created_at
    """, (username, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))
    
    mood_data = cursor.fetchall()
    conn.close()
    
    # Analyze mood patterns
    mood_counts = {}
    for entry in mood_data:
        mood = entry["mood"]
        mood_counts[mood] = mood_counts.get(mood, 0) + 1
    
    # Generate insights
    insights = generate_insights(mood_data, mood_counts)
    recommendations = generate_recommendations(mood_counts, insights)
    
    return {
        "username": username,
        "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        "total_entries": len(mood_data),
        "mood_distribution": mood_counts,
        "insights": insights,
        "recommendations": recommendations,
        "mood_trend": "improving" if is_trend_improving(mood_data) else "stable" if is_trend_stable(mood_data) else "needs_attention"
    }

def generate_insights(mood_data, mood_counts):
    """Generate insights from mood data"""
    insights = []
    
    if mood_counts.get("Stressed", 0) > 3:
        insights.append("You've experienced stress multiple times this week. Consider stress management techniques.")
    
    if mood_counts.get("Depressed/Low", 0) > 2:
        insights.append("There were several low mood days. Regular exercise and social connection might help.")
    
    if len(mood_data) >= 3 and all(mood["mood"] in ["Happy/Calm", "Neutral"] for mood in mood_data[-3:]):
        insights.append("Great! Your mood has been consistently positive recently.")
    
    if not insights:
        insights.append("Your mood patterns show normal variation. Continue monitoring how you feel.")
    
    return insights

def generate_recommendations(mood_counts, insights):
    """Generate personalized recommendations"""
    recommendations = []
    
    if mood_counts.get("Stressed", 0) > 2:
        recommendations.extend([
            "Practice 10 minutes of deep breathing daily",
            "Try progressive muscle relaxation before bed",
            "Consider time management techniques"
        ])
    
    if mood_counts.get("Tired/Exhausted", 0) > 2:
        recommendations.extend([
            "Ensure 7-8 hours of quality sleep",
            "Take short breaks during work",
            "Stay hydrated and maintain balanced nutrition"
        ])
    
    if mood_counts.get("Depressed/Low", 0) > 1:
        recommendations.extend([
            "Connect with friends or family regularly",
            "Engage in light physical activity",
            "Practice gratitude journaling"
        ])
    
    # Default wellness recommendations
    if not recommendations:
        recommendations = [
            "Continue with your current wellness routine",
            "Practice mindfulness meditation",
            "Stay connected with loved ones"
        ]
    
    return recommendations[:3]  # Return top 3 recommendations

def is_trend_improving(mood_data):
    """Check if mood trend is improving"""
    if len(mood_data) < 3:
        return False
    
    positive_moods = ["Happy/Calm", "Neutral"]
    recent_positive = sum(1 for mood in mood_data[-3:] if mood["mood"] in positive_moods)
    return recent_positive >= 2

def is_trend_stable(mood_data):
    """Check if mood trend is stable"""
    if len(mood_data) < 2:
        return True
    return len(set(mood["mood"] for mood in mood_data[-3:])) == 1