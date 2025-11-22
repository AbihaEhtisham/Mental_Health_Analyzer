const API_URL = 'http://localhost:8000';

// DOM Elements
const reportContainer = document.getElementById('report-container');

// Initialize when page loads
document.addEventListener('DOMContentLoaded', async () => {
    const username = localStorage.getItem('currentUser');
    
    if (!username) {
        alert('Please login to view your report.');
        location.href = 'login.html';
        return;
    }
    
    await loadWeeklyReport(username);
});

async function loadWeeklyReport(username) {
    try {
        reportContainer.innerHTML = '<div class="loading">Generating your weekly report...</div>';
        
        const response = await fetch(`${API_URL}/weekly-report/${encodeURIComponent(username)}`);
        
        if (!response.ok) {
            throw new Error((await response.json()).detail);
        }
        
        const report = await response.json();
        displayReport(report);
        
    } catch (error) {
        reportContainer.innerHTML = `
            <div class="error-message">
                <h3>Unable to generate report</h3>
                <p>${error.message}</p>
                <button onclick="location.href='results.html'" class="btn btn-primary">Back to Results</button>
            </div>
        `;
    }
}

function displayReport(report) {
    const reportHTML = `
        <div class="report-content">
            <div class="report-header">
                <h2>📊 Weekly Mood Report</h2>
                <div class="report-period">${report.period}</div>
            </div>
            
            <div class="report-summary">
                <div class="summary-cards">
                    <div class="summary-card">
                        <div class="summary-value">${report.total_entries}</div>
                        <div class="summary-label">Total Entries</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value trend-${report.mood_trend}">${report.mood_trend}</div>
                        <div class="summary-label">Overall Trend</div>
                    </div>
                </div>
            </div>

            <div class="mood-distribution">
                <h3>📈 Mood Distribution</h3>
                ${Object.entries(report.mood_distribution).map(([mood, count]) => `
                    <div class="dist-item">
                        <span class="mood-name">${mood}</span>
                        <div class="dist-bar">
                            <div class="dist-fill" style="width: ${(count / report.total_entries) * 100}%"></div>
                        </div>
                        <span class="dist-count">${count}</span>
                    </div>
                `).join('')}
            </div>

            <div class="insights-section">
                <h3>💡 Insights</h3>
                ${report.insights.map(insight => `
                    <div class="insight-item">${insight}</div>
                `).join('')}
            </div>

            <div class="recommendations-section">
                <h3>🎯 Recommendations</h3>
                ${report.recommendations.map(rec => `
                    <div class="recommendation-item">${rec}</div>
                `).join('')}
            </div>
        </div>
    `;
    
    reportContainer.innerHTML = reportHTML;
}