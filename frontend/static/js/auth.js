// Authentication JavaScript
const API_URL = '/api';  // Use relative URL since we're on the same domain

// Switch between login and register tabs
function switchTab(tab) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const loginTab = document.querySelector('[data-tab="login"]');
    const registerTab = document.querySelector('[data-tab="register"]');
    
    if (tab === 'login') {
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
        loginTab.classList.add('active');
        registerTab.classList.remove('active');
    } else {
        registerForm.classList.add('active');
        loginForm.classList.remove('active');
        registerTab.classList.add('active');
        loginTab.classList.remove('active');
    }
    
    // Clear messages
    document.getElementById('login-message').className = 'message hidden';
    document.getElementById('register-message').className = 'message hidden';
}

// Tab click handlers
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.auth-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchTab(tab.dataset.tab);
        });
    });
});

// Show message
function showMessage(elementId, message, type = 'error') {
    const messageEl = document.getElementById(elementId);
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('login-message', 'Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            showMessage('login-message', data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('login-message', 'Connection error. Please try again.', 'error');
        console.error('Login error:', error);
    }
}

// Handle register
async function handleRegister(event) {
    event.preventDefault();
    
    const formData = {
        username: document.getElementById('register-username').value,
        email: document.getElementById('register-email').value,
        password: document.getElementById('register-password').value,
        full_name: document.getElementById('register-fullname').value,
        household_size: parseInt(document.getElementById('household-size').value),
        tariff_rate: parseFloat(document.getElementById('tariff-rate').value)
    };
    
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('register-message', 'Registration successful! Please login.', 'success');
            setTimeout(() => {
                switchTab('login');
            }, 2000);
        } else {
            showMessage('register-message', data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('register-message', 'Connection error. Please try again.', 'error');
        console.error('Registration error:', error);
    }
}

// Check auth status on page load
async function checkAuthStatus() {
    try {
        const response = await fetch(`${API_URL}/auth/status`, {
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.authenticated && window.location.pathname === '/login') {
            window.location.href = '/dashboard';
        }
    } catch (error) {
        console.error('Auth status check error:', error);
    }
}

// Check auth on page load
if (window.location.pathname === '/login') {
    checkAuthStatus();
}
