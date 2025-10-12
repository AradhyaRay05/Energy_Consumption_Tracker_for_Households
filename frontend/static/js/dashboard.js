// Dashboard JavaScript
const API_URL = '/api';  // Use relative URL since we're on the same domain

// Check authentication and load user data
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/auth/status`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (!data.authenticated) {
            window.location.href = '/login';
            return false;
        }
        
        // Set username
        document.getElementById('username').textContent = data.user.username;
        return true;
    } catch (error) {
        console.error('Auth check error:', error);
        window.location.href = '/login';
        return false;
    }
}

// Logout handler
async function handleLogout() {
    try {
        await fetch(`${API_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// Load dashboard summary statistics
async function loadSummaryStats() {
    try {
        const response = await fetch(`${API_URL}/dashboard/summary?days=30`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok && data.stats) {
            document.getElementById('total-kwh').textContent = data.stats.total_kwh.toFixed(2);
            document.getElementById('total-cost').textContent = `$${data.stats.total_cost.toFixed(2)}`;
            document.getElementById('avg-daily').textContent = data.stats.avg_daily.toFixed(2);
            document.getElementById('carbon-footprint').textContent = `${data.stats.carbon_kg.toFixed(1)} kg`;
        }
    } catch (error) {
        console.error('Error loading summary stats:', error);
    }
}

// Load insights
async function loadInsights() {
    const container = document.getElementById('insights-container');
    container.innerHTML = '<div class="loading">Loading insights...</div>';
    
    try {
        const response = await fetch(`${API_URL}/dashboard/insights`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok && data.insights && data.insights.length > 0) {
            container.innerHTML = '';
            data.insights.forEach(insight => {
                const card = document.createElement('div');
                card.className = `insight-card ${insight.type}`;
                card.textContent = insight.text;
                container.appendChild(card);
            });
        } else {
            container.innerHTML = '<p class="text-muted">No insights available yet. Add more data to get personalized recommendations.</p>';
        }
    } catch (error) {
        console.error('Error loading insights:', error);
        container.innerHTML = '<p class="text-muted">Error loading insights</p>';
    }
}

// Refresh insights
function refreshInsights() {
    loadInsights();
}

// Load daily consumption chart
async function loadDailyChart() {
    const days = document.getElementById('daily-days').value;
    const container = document.getElementById('daily-chart');
    container.innerHTML = '<div class="loading">Loading chart...</div>';
    
    try {
        const response = await fetch(`${API_URL}/visualize/daily?days=${days}&format=base64`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok && data.image) {
            container.innerHTML = `<img src="${data.image}" alt="Daily Consumption Chart">`;
        } else {
            container.innerHTML = '<p class="text-muted">No data available for visualization</p>';
        }
    } catch (error) {
        console.error('Error loading daily chart:', error);
        container.innerHTML = '<p class="text-muted">Error loading chart</p>';
    }
}

// Load appliance breakdown chart
async function loadApplianceChart() {
    const container = document.getElementById('appliance-chart');
    container.innerHTML = '<div class="loading">Loading chart...</div>';
    
    try {
        const response = await fetch(`${API_URL}/visualize/appliances?format=base64`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok && data.image) {
            container.innerHTML = `<img src="${data.image}" alt="Appliance Breakdown Chart">`;
        } else {
            container.innerHTML = '<p class="text-muted">No data available for visualization</p>';
        }
    } catch (error) {
        console.error('Error loading appliance chart:', error);
        container.innerHTML = '<p class="text-muted">Error loading chart</p>';
    }
}

// Load predictions
async function loadPredictions() {
    const container = document.getElementById('predictions-container');
    container.innerHTML = '<div class="loading">Generating predictions...</div>';
    
    try {
        const response = await fetch(`${API_URL}/predict/daily?days=7`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok && data.predictions && data.predictions.length > 0) {
            let tableHTML = `
                <table class="predictions-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Predicted Consumption (kWh)</th>
                            <th>Predicted Cost ($)</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            data.predictions.forEach(pred => {
                const confidence = (pred.confidence_score * 100).toFixed(0);
                tableHTML += `
                    <tr>
                        <td>${pred.date}</td>
                        <td>${pred.predicted_kwh.toFixed(2)}</td>
                        <td>$${pred.predicted_cost.toFixed(2)}</td>
                        <td>${confidence}%</td>
                    </tr>
                `;
            });
            
            tableHTML += '</tbody></table>';
            container.innerHTML = tableHTML;
            
            // Also load monthly prediction
            loadMonthlyPrediction();
        } else {
            container.innerHTML = '<p class="text-muted">Insufficient data for predictions. Add more energy records.</p>';
        }
    } catch (error) {
        console.error('Error loading predictions:', error);
        container.innerHTML = '<p class="text-muted">Error generating predictions. Make sure you have historical data.</p>';
    }
}

// Load monthly prediction
async function loadMonthlyPrediction() {
    try {
        const response = await fetch(`${API_URL}/predict/monthly`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const container = document.getElementById('predictions-container');
            const summaryHTML = `
                <div style="background: #f0f8ff; padding: 20px; border-radius: 8px; margin-top: 20px;">
                    <h3 style="margin-bottom: 15px; color: #2E86AB;">
                        <i class="fas fa-calendar-alt"></i> Monthly Forecast
                    </h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <p style="color: #7f8c8d; margin-bottom: 5px;">Predicted Monthly Consumption</p>
                            <p style="font-size: 1.8rem; font-weight: bold; color: #2E86AB;">
                                ${data.predicted_monthly_kwh} kWh
                            </p>
                        </div>
                        <div>
                            <p style="color: #7f8c8d; margin-bottom: 5px;">Predicted Monthly Cost</p>
                            <p style="font-size: 1.8rem; font-weight: bold; color: #F18F01;">
                                $${data.predicted_monthly_cost}
                            </p>
                        </div>
                    </div>
                </div>
            `;
            container.innerHTML += summaryHTML;
        }
    } catch (error) {
        console.error('Error loading monthly prediction:', error);
    }
}

// Handle add data form
async function handleAddData(event) {
    event.preventDefault();
    
    const formData = {
        appliance_name: document.getElementById('appliance-select').value,
        power_usage_kwh: parseFloat(document.getElementById('power-usage').value),
        duration_hours: parseFloat(document.getElementById('duration').value),
        timestamp: document.getElementById('timestamp').value
    };
    
    try {
        const response = await fetch(`${API_URL}/data/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Energy record added successfully!');
            event.target.reset();
            // Refresh dashboard data
            loadDashboardData();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error('Error adding data:', error);
        alert('Connection error. Please try again.');
    }
}

// Load all dashboard data
function loadDashboardData() {
    loadSummaryStats();
    loadInsights();
    loadDailyChart();
    loadApplianceChart();
}

// Sidebar navigation
document.addEventListener('DOMContentLoaded', () => {
    const menuItems = document.querySelectorAll('.sidebar-menu a');
    
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all items
            document.querySelectorAll('.sidebar-menu li').forEach(li => {
                li.classList.remove('active');
            });
            
            // Add active class to clicked item
            item.parentElement.classList.add('active');
            
            // Show/hide sections
            const section = item.getAttribute('href').substring(1);
            
            // Hide all sections except the selected one
            document.querySelectorAll('.insights-section, .charts-section, .predictions-section, .add-data-section').forEach(sec => {
                sec.style.display = 'none';
            });
            
            // Show selected section
            if (section === 'adddata') {
                document.getElementById('add-data-section').style.display = 'block';
            } else if (section === 'insights') {
                document.querySelector('.insights-section').style.display = 'block';
            } else if (section === 'consumption' || section === 'appliances') {
                document.querySelector('.charts-section').style.display = 'grid';
            } else if (section === 'predictions') {
                document.querySelector('.predictions-section').style.display = 'block';
            } else if (section === 'overview') {
                // Show all main sections
                document.querySelector('.insights-section').style.display = 'block';
                document.querySelector('.charts-section').style.display = 'grid';
                document.querySelector('.predictions-section').style.display = 'block';
            }
        });
    });
    
    // Set current datetime for add data form
    const now = new Date();
    const dateTimeStr = now.toISOString().slice(0, 16);
    document.getElementById('timestamp').value = dateTimeStr;
});

// Initialize dashboard
(async function init() {
    const authenticated = await checkAuth();
    if (authenticated) {
        loadDashboardData();
    }
})();
