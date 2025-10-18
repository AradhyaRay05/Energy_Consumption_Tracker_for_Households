"""
Flask Backend Application
Main application server for Energy Consumption Tracker
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import bcrypt
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_config import DatabaseConfig
from ml_models.energy_predictor import EnergyPredictor
from ml_models.visualizations import EnergyVisualizer

# Initialize Flask app
app = Flask(__name__, 
           template_folder='../frontend/templates',
           static_folder='../frontend/static')
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# Enable CORS with credentials support
CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

# Initialize components
db = DatabaseConfig()  # This now initializes the connection pool automatically
predictor = EnergyPredictor(model_path='../ml_models/models')
visualizer = EnergyVisualizer(output_dir='../frontend/static/plots')

# Verify connection pool is ready
if db.connection_pool:
    print("✓ Connection pool ready with 10 connections")
else:
    print("⚠ Connection pool failed, using fallback connections")


# ==================== UTILITY FUNCTIONS ====================

def calculate_carbon_footprint(kwh):
    """
    Calculate carbon footprint from energy consumption
    India's grid carbon intensity: ~0.82 kg CO2 per kWh
    """
    CO2_PER_KWH = 0.82  # kg CO2 per kWh (India's average)
    return kwh * CO2_PER_KWH


def generate_insights(user_id, daily_data, appliance_data):
    """Generate personalized energy-saving insights"""
    insights = []
    
    if not daily_data:
        return insights
    
    # Calculate statistics (convert Decimal to float)
    recent_consumption = [float(d['total_kwh']) for d in daily_data[:7]]
    avg_consumption = float(np.mean(recent_consumption))
    
    # High consumption alert
    if recent_consumption[0] > avg_consumption * 1.3:
        insights.append({
            'type': 'alert',
            'priority': 'high',
            'icon': '⚠️',
            'title': 'High Consumption Alert',
            'text': f'Your consumption today ({recent_consumption[0]:.2f} kWh) is 30% higher than your weekly average. Check for appliances left on.'
        })
    
    # Low consumption praise
    if recent_consumption[0] < avg_consumption * 0.8:
        insights.append({
            'type': 'success',
            'priority': 'medium',
            'icon': '🌟',
            'title': 'Great Job!',
            'text': f'Your consumption today ({recent_consumption[0]:.2f} kWh) is 20% lower than your average. Keep it up!'
        })
    
    # Peak usage time
    insights.append({
        'type': 'info',
        'priority': 'medium',
        'icon': '💡',
        'title': 'Peak Usage Optimization',
        'text': 'Your peak usage is typically between 6 PM - 9 PM. Consider shifting some activities to off-peak hours (11 PM - 6 AM) to save on costs.'
    })
    
    # Appliance recommendations
    if appliance_data and len(appliance_data) > 0:
        top_consumer = appliance_data[0]
        top_kwh = float(top_consumer["total_kwh"])
        top_cost = float(top_consumer["total_cost"])
        insights.append({
            'type': 'tip',
            'priority': 'high',
            'icon': '🔌',
            'title': 'Top Energy Consumer',
            'text': f'{top_consumer["appliance_name"]} is your highest energy consumer ({top_kwh:.1f} kWh, ₹{top_cost:.2f}). Consider upgrading to energy-efficient models.'
        })
        
        # If there are multiple appliances, suggest optimization
        if len(appliance_data) >= 3:
            total_top3_kwh = sum(float(a['total_kwh']) for a in appliance_data[:3])
            total_all_kwh = sum(float(a['total_kwh']) for a in appliance_data)
            percentage = (total_top3_kwh / total_all_kwh * 100) if total_all_kwh > 0 else 0
            insights.append({
                'type': 'info',
                'priority': 'medium',
                'icon': '📊',
                'title': 'Appliance Usage Pattern',
                'text': f'Your top 3 appliances consume {percentage:.0f}% of your total energy. Optimizing these can significantly reduce your bill.'
            })
    
    # Weekend vs weekday
    if len(daily_data) >= 14:
        weekday_data = [float(d['total_kwh']) for d in daily_data if datetime.strptime(str(d['date']), '%Y-%m-%d').weekday() < 5][:7]
        weekend_data = [float(d['total_kwh']) for d in daily_data if datetime.strptime(str(d['date']), '%Y-%m-%d').weekday() >= 5][:4]
        
        if weekday_data and weekend_data:
            weekday_avg = float(np.mean(weekday_data))
            weekend_avg = float(np.mean(weekend_data))
            
            if weekend_avg > weekday_avg * 1.2:
                diff_percent = ((weekend_avg/weekday_avg - 1) * 100)
                insights.append({
                    'type': 'info',
                    'priority': 'low',
                    'icon': '📅',
                    'title': 'Weekend Usage Pattern',
                    'text': f'Your weekend consumption ({weekend_avg:.1f} kWh) is {diff_percent:.0f}% higher than weekdays ({weekday_avg:.1f} kWh). More people at home?'
                })
            elif weekday_avg > weekend_avg * 1.2:
                diff_percent = ((weekday_avg/weekend_avg - 1) * 100)
                insights.append({
                    'type': 'info',
                    'priority': 'low',
                    'icon': '📅',
                    'title': 'Weekday Usage Pattern',
                    'text': f'Your weekday consumption ({weekday_avg:.1f} kWh) is {diff_percent:.0f}% higher than weekends. Consider reducing daytime appliance usage.'
                })
    
    # Trend analysis
    if len(daily_data) >= 7:
        first_half = np.mean([float(d['total_kwh']) for d in daily_data[3:7]])
        second_half = np.mean([float(d['total_kwh']) for d in daily_data[:3]])
        
        if second_half > first_half * 1.15:
            insights.append({
                'type': 'warning',
                'priority': 'high',
                'icon': '📈',
                'title': 'Increasing Trend Detected',
                'text': f'Your consumption is increasing. Recent average: {second_half:.1f} kWh vs earlier: {first_half:.1f} kWh. Monitor your usage closely.'
            })
        elif second_half < first_half * 0.85:
            insights.append({
                'type': 'success',
                'priority': 'medium',
                'icon': '📉',
                'title': 'Decreasing Trend - Excellent!',
                'text': f'Your consumption is decreasing! Recent average: {second_half:.1f} kWh vs earlier: {first_half:.1f} kWh. Great progress!'
            })
    
    # Money saving tip
    try:
        user = db.get_user_by_id(user_id)
        tariff_rate = float(user.get('tariff_rate', 7.00)) if user else 7.00
    except Exception as e:
        print(f"Warning: Could not get user tariff rate: {e}")
        tariff_rate = 7.00
    
    potential_savings_15 = avg_consumption * 0.15 * tariff_rate * 30
    potential_savings_25 = avg_consumption * 0.25 * tariff_rate * 30
    insights.append({
        'type': 'success',
        'priority': 'high',
        'icon': '💰',
        'title': 'Savings Opportunity',
        'text': f'By reducing consumption by 15%, you could save ₹{potential_savings_15:.2f}/month. A 25% reduction could save ₹{potential_savings_25:.2f}/month!'
    })
    
    # Carbon footprint insight
    monthly_consumption = avg_consumption * 30
    carbon_footprint = calculate_carbon_footprint(monthly_consumption)
    trees_equivalent = carbon_footprint / 20  # 1 tree absorbs ~20kg CO2/year
    insights.append({
        'type': 'info',
        'priority': 'medium',
        'icon': '🌍',
        'title': 'Environmental Impact',
        'text': f'Your monthly carbon footprint is ~{carbon_footprint:.1f} kg CO₂. That\'s equivalent to planting {trees_equivalent:.1f} trees to offset!'
    })
    
    return insights


def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name', '')
        household_size = data.get('household_size', 1)
        tariff_rate = data.get('tariff_rate', 7.00)  # Default Indian tariff rate ₹7.00/kWh
        
        # Validate input
        if not all([username, email, password]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        existing_user = db.get_user_by_username(username)
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 409
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        success = db.create_user(username, email, password_hash, full_name, household_size, tariff_rate)
        
        if success:
            return jsonify({'message': 'User registered successfully'}), 201
        else:
            return jsonify({'error': 'Registration failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """User login"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        print(f"Login attempt for user: {username}")  # Debug logging
        
        # Validate input
        if not all([username, password]):
            return jsonify({'error': 'Missing username or password'}), 400
        
        # Get user
        user = db.get_user_by_username(username)
        
        if not user:
            print(f"User not found: {username}")  # Debug logging
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            # Set session
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            
            print(f"Login successful for user: {username}")  # Debug logging
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user['email'],
                    'full_name': user['full_name']
                }
            }), 200
        else:
            print(f"Password mismatch for user: {username}")  # Debug logging
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug logging
        return jsonify({'error': str(e)}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check authentication status"""
    if 'user_id' in session:
        user = db.get_user_by_id(session['user_id'])
        return jsonify({
            'authenticated': True,
            'user': {
                'user_id': user['user_id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name']
            }
        }), 200
    else:
        return jsonify({'authenticated': False}), 200


# ==================== DASHBOARD ROUTES ====================

@app.route('/api/dashboard/summary', methods=['GET'])
@login_required
def dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        user_id = session['user_id']
        days = int(request.args.get('days', 30))
        
        print(f"Dashboard summary - User ID: {user_id}, Days: {days}")
        
        # Get data
        daily_data = db.get_daily_consumption(user_id, days=days)
        appliance_data = db.get_appliance_consumption(user_id)
        
        print(f"Daily data count: {len(daily_data) if daily_data else 0}")
        print(f"Appliance data count: {len(appliance_data) if appliance_data else 0}")
        
        if not daily_data:
            return jsonify({
                'message': 'No data available',
                'stats': {
                    'total_kwh': 0,
                    'total_cost': 0,
                    'avg_daily': 0,
                    'carbon_kg': 0
                }
            }), 200
        
        # Calculate statistics - convert Decimal to float
        total_kwh = float(sum(float(d['total_kwh']) for d in daily_data))
        total_cost = float(sum(float(d['total_cost']) for d in daily_data))
        avg_daily = total_kwh / len(daily_data)
        carbon_kg = calculate_carbon_footprint(total_kwh)
        
        print(f"Calculated: total_kwh={total_kwh}, total_cost={total_cost}, avg_daily={avg_daily}")
        
        # Find peak day - convert Decimal to float for comparison
        peak_day_data = max(daily_data, key=lambda x: float(x['total_kwh']))
        peak_day = peak_day_data['date'].strftime('%Y-%m-%d')
        
        # Calculate efficiency score (lower is better, normalize to 0-100)
        efficiency_score = max(0, 100 - (avg_daily / 30 * 100))  # Assuming 30 kWh/day is baseline
        
        stats = {
            'total_kwh': round(total_kwh, 2),
            'total_cost': round(total_cost, 2),
            'avg_daily': round(avg_daily, 2),
            'peak_day': peak_day,
            'carbon_kg': round(carbon_kg, 2),
            'efficiency_score': round(efficiency_score, 0),
            'days_analyzed': len(daily_data),
            'appliances_count': len(appliance_data) if appliance_data else 0
        }
        
        print(f"Dashboard summary stats: {stats}")
        
        return jsonify({'stats': stats}), 200
        
    except Exception as e:
        print(f"Error in dashboard_summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/insights', methods=['GET'])
@login_required
def get_insights():
    """Get personalized energy insights"""
    try:
        user_id = session['user_id']
        
        print(f"Getting insights for user_id: {user_id}")  # Debug
        
        # Get recent data
        daily_data = db.get_daily_consumption(user_id, days=30)
        appliance_data = db.get_appliance_consumption(user_id)
        
        print(f"Daily data: {len(daily_data) if daily_data else 0} records")  # Debug
        print(f"Appliance data: {len(appliance_data) if appliance_data else 0} records")  # Debug
        
        # Generate insights
        try:
            insights = generate_insights(user_id, daily_data, appliance_data)
            print(f"Generated {len(insights)} insights")  # Debug
        except Exception as insight_error:
            print(f"Error generating insights: {insight_error}")  # Debug
            import traceback
            traceback.print_exc()
            insights = []  # Return empty list on error
        
        return jsonify({'insights': insights}), 200
        
    except Exception as e:
        print(f"Error in get_insights: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== DATA ROUTES ====================

@app.route('/api/data/daily', methods=['GET'])
@login_required
def get_daily_data():
    """Get daily consumption data"""
    try:
        user_id = session['user_id']
        days = int(request.args.get('days', 30))
        
        data = db.get_daily_consumption(user_id, days=days)
        
        # Convert datetime to string
        for record in data:
            if isinstance(record['date'], datetime):
                record['date'] = record['date'].strftime('%Y-%m-%d')
        
        return jsonify({'data': data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/appliances', methods=['GET'])
@login_required
def get_appliance_data():
    """Get appliance consumption data"""
    try:
        user_id = session['user_id']
        data = db.get_appliance_consumption(user_id)
        
        return jsonify({'data': data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/monthly', methods=['GET'])
@login_required
def get_monthly_data():
    """Get monthly statistics"""
    try:
        user_id = session['user_id']
        months = int(request.args.get('months', 12))
        
        data = db.get_monthly_statistics(user_id, months=months)
        
        return jsonify({'data': data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/data/add', methods=['POST'])
@login_required
def add_energy_record():
    """Add a new energy consumption record"""
    try:
        user_id = session['user_id']
        data = request.json
        
        print(f"Add data request for user_id: {user_id}")  # Debug logging
        print(f"Request data: {data}")  # Debug logging
        
        timestamp = data.get('timestamp', datetime.now())
        appliance_name = data.get('appliance_name')
        power_usage_kwh = float(data.get('power_usage_kwh'))
        duration_hours = float(data.get('duration_hours', 1.0))
        
        # Get user's tariff rate
        user = db.get_user_by_id(user_id)
        
        if not user:
            print(f"User not found for user_id: {user_id}")  # Debug logging
            return jsonify({'error': 'User not found'}), 404
        
        # Convert Decimal to float to avoid type issues
        tariff_rate = float(user['tariff_rate'])
        cost = power_usage_kwh * tariff_rate
        
        print(f"Adding record: appliance={appliance_name}, kwh={power_usage_kwh}, cost={cost}")  # Debug logging
        
        # Add record
        success = db.add_energy_record(
            user_id, timestamp, appliance_name, 
            power_usage_kwh, cost, duration_hours
        )
        
        if success:
            print(f"Record added successfully")  # Debug logging
            return jsonify({'message': 'Record added successfully'}), 201
        else:
            print(f"Failed to add record to database")  # Debug logging
            return jsonify({'error': 'Failed to add record'}), 500
            
    except Exception as e:
        print(f"Error in add_energy_record: {str(e)}")  # Debug logging
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== PREDICTION ROUTES ====================

@app.route('/api/predict/daily', methods=['GET'])
@login_required
def predict_daily():
    """Predict energy consumption for next N days"""
    try:
        user_id = session['user_id']
        days = int(request.args.get('days', 7))
        
        print(f"Predict daily - User ID: {user_id}, Days: {days}")
        
        # Get historical data
        historical_df = db.get_data_as_dataframe(user_id)
        
        print(f"Historical data shape: {historical_df.shape if not historical_df.empty else 'EMPTY'}")
        print(f"Historical data columns: {historical_df.columns.tolist() if not historical_df.empty else 'NONE'}")
        
        if historical_df.empty or len(historical_df) < 7:
            print(f"Insufficient data: {len(historical_df)} records (need at least 7)")
            return jsonify({'error': 'Insufficient data for predictions. Add more energy records.'}), 400
        
        # Get user's tariff rate
        user = db.get_user_by_id(user_id)
        tariff_rate = float(user['tariff_rate'])
        
        print(f"User tariff rate: {tariff_rate}")
        
        # Load or train model
        try:
            predictor.load_model()
            print("Model loaded successfully")
        except Exception as e:
            print(f"Model not found, training new model: {e}")
            # Train model if not exists
            predictor.train(historical_df)
            predictor.save_model()
            print("Model trained and saved")
        
        # Make predictions
        print("Generating predictions...")
        predictions = predictor.predict_next_days(historical_df, days=days, tariff_rate=tariff_rate)
        
        print(f"Predictions shape: {predictions.shape}")
        
        # Convert to dict
        predictions_list = predictions.to_dict('records')
        
        # Convert dates to strings
        for pred in predictions_list:
            pred['date'] = pred['date'].strftime('%Y-%m-%d')
        
        print(f"Returning {len(predictions_list)} predictions")
        
        return jsonify({'predictions': predictions_list}), 200
        
    except Exception as e:
        print(f"Error in predict_daily: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict/monthly', methods=['GET'])
@login_required
def predict_monthly():
    """Predict monthly energy consumption"""
    try:
        user_id = session['user_id']
        
        # Get historical data
        historical_df = db.get_data_as_dataframe(user_id)
        
        if historical_df.empty:
            return jsonify({'error': 'Insufficient data for prediction'}), 400
        
        # Get user's tariff rate
        user = db.get_user_by_id(user_id)
        tariff_rate = user['tariff_rate']
        
        # Load or train model
        try:
            predictor.load_model()
        except:
            predictor.train(historical_df)
            predictor.save_model()
        
        # Make monthly prediction
        monthly_pred = predictor.predict_monthly(historical_df, tariff_rate=tariff_rate)
        
        return jsonify(monthly_pred), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== VISUALIZATION ROUTES ====================

@app.route('/api/visualize/daily', methods=['GET'])
@login_required
def visualize_daily():
    """Generate daily consumption visualization"""
    try:
        user_id = session['user_id']
        days = int(request.args.get('days', 30))
        format_type = request.args.get('format', 'file')  # 'file' or 'base64'
        
        print(f"Visualize daily for user_id: {user_id}, days: {days}")  # Debug
        
        daily_data = db.get_daily_consumption(user_id, days=days)
        
        print(f"Daily data retrieved: {len(daily_data) if daily_data else 0} records")  # Debug
        
        if not daily_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(daily_data)
        print(f"DataFrame shape: {df.shape}")  # Debug
        print(f"DataFrame columns: {df.columns.tolist()}")  # Debug
        
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_daily_consumption(df, days=days, return_base64=return_base64)
        
        print(f"Visualization result: {result[:100] if result else 'None'}...")  # Debug
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_daily: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/appliances', methods=['GET'])
@login_required
def visualize_appliances():
    """Generate appliance breakdown visualization"""
    try:
        user_id = session['user_id']
        format_type = request.args.get('format', 'file')
        
        print(f"Visualize appliances for user_id: {user_id}")  # Debug
        
        appliance_data = db.get_appliance_consumption(user_id)
        
        print(f"Appliance data retrieved: {len(appliance_data) if appliance_data else 0} records")  # Debug
        
        if not appliance_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(appliance_data)
        print(f"DataFrame shape: {df.shape}")  # Debug
        print(f"DataFrame columns: {df.columns.tolist()}")  # Debug
        
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_appliance_breakdown(df, return_base64=return_base64)
        
        print(f"Visualization result: {result[:100] if result else 'None'}...")  # Debug
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_appliances: {str(e)}")  # Debug
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/energy-consumption', methods=['GET'])
@login_required
def visualize_energy_consumption():
    """Generate only energy consumption chart"""
    try:
        user_id = session['user_id']
        days = int(request.args.get('days', 30))
        format_type = request.args.get('format', 'file')
        
        daily_data = db.get_daily_consumption(user_id, days=days)
        
        if not daily_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(daily_data)
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_energy_consumption_only(df, days=days, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_energy_consumption: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/cost-analysis', methods=['GET'])
@login_required
def visualize_cost_analysis():
    """Generate only cost analysis chart"""
    try:
        user_id = session['user_id']
        days = int(request.args.get('days', 30))
        format_type = request.args.get('format', 'file')
        
        daily_data = db.get_daily_consumption(user_id, days=days)
        
        if not daily_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(daily_data)
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_cost_analysis_only(df, days=days, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_cost_analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/appliance-bar', methods=['GET'])
@login_required
def visualize_appliance_bar():
    """Generate only appliance bar chart"""
    try:
        user_id = session['user_id']
        format_type = request.args.get('format', 'file')
        
        appliance_data = db.get_appliance_consumption(user_id)
        
        if not appliance_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(appliance_data)
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_appliance_bar_only(df, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_appliance_bar: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/appliance-pie', methods=['GET'])
@login_required
def visualize_appliance_pie():
    """Generate only appliance pie chart"""
    try:
        user_id = session['user_id']
        format_type = request.args.get('format', 'file')
        
        appliance_data = db.get_appliance_consumption(user_id)
        
        if not appliance_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(appliance_data)
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_appliance_pie_only(df, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_appliance_pie: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/monthly', methods=['GET'])
@login_required
def visualize_monthly():
    """Generate monthly trend visualization"""
    try:
        user_id = session['user_id']
        months = int(request.args.get('months', 12))
        format_type = request.args.get('format', 'file')
        
        monthly_data = db.get_monthly_statistics(user_id, months=months)
        
        if not monthly_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(monthly_data)
        
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_monthly_trend(df, months=months, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/hourly-pattern', methods=['GET'])
@login_required
def visualize_hourly_pattern():
    """Generate hourly consumption pattern chart"""
    try:
        user_id = session['user_id']
        format_type = request.args.get('format', 'file')
        
        # Get hourly data (if available) or simulate from daily data
        hourly_data = db.get_hourly_pattern(user_id) if hasattr(db, 'get_hourly_pattern') else None
        
        if not hourly_data:
            # Generate sample hourly pattern for demonstration
            hourly_data = []
            for hour in range(24):
                # Simulate consumption pattern (higher during evening hours)
                if 6 <= hour < 9:  # Morning peak
                    avg_kwh = np.random.uniform(2.0, 3.5)
                elif 18 <= hour < 22:  # Evening peak
                    avg_kwh = np.random.uniform(3.0, 4.5)
                else:  # Off-peak
                    avg_kwh = np.random.uniform(0.5, 2.0)
                hourly_data.append({'hour': hour, 'avg_kwh': avg_kwh})
        
        df = pd.DataFrame(hourly_data)
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_hourly_pattern(df, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_hourly_pattern: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/weekly-comparison', methods=['GET'])
@login_required
def visualize_weekly_comparison():
    """Generate weekly comparison chart"""
    try:
        user_id = session['user_id']
        format_type = request.args.get('format', 'file')
        
        # Get daily data and calculate weekly averages
        daily_data = db.get_daily_consumption(user_id, days=30)
        
        if not daily_data or len(daily_data) == 0:
            # Generate sample weekly data for demonstration
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            weekly_data = pd.DataFrame({
                'day_name': day_order,
                'avg_kwh': [
                    np.random.uniform(8, 12),  # Monday
                    np.random.uniform(8, 11),  # Tuesday
                    np.random.uniform(8, 11),  # Wednesday
                    np.random.uniform(8, 12),  # Thursday
                    np.random.uniform(9, 13),  # Friday
                    np.random.uniform(10, 15),  # Saturday (higher)
                    np.random.uniform(10, 14)   # Sunday (higher)
                ],
                'total_cost': [0]  # Placeholder
            })
        else:
            df = pd.DataFrame(daily_data)
            df['date'] = pd.to_datetime(df['date'])
            df['day_name'] = df['date'].dt.day_name()
            
            # Calculate averages by day of week
            weekly_data = df.groupby('day_name').agg({
                'total_kwh': 'mean',
                'total_cost': 'mean'
            }).reset_index()
            weekly_data.columns = ['day_name', 'avg_kwh', 'total_cost']
        
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_weekly_comparison(weekly_data, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_weekly_comparison: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/appliance-efficiency', methods=['GET'])
@login_required
def visualize_appliance_efficiency():
    """Generate appliance efficiency chart"""
    try:
        user_id = session['user_id']
        format_type = request.args.get('format', 'file')
        
        appliance_data = db.get_appliance_consumption(user_id)
        
        if not appliance_data:
            return jsonify({'error': 'No data available'}), 404
        
        df = pd.DataFrame(appliance_data)
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_appliance_efficiency(df, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_appliance_efficiency: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/visualize/appliance-usage-timeline', methods=['GET'])
@login_required
def visualize_appliance_usage_timeline():
    """Generate appliance usage timeline chart showing top appliances over time"""
    try:
        user_id = session['user_id']
        format_type = request.args.get('format', 'file')
        days = int(request.args.get('days', 7))
        
        # Get daily data and appliance data
        daily_data = db.get_daily_consumption(user_id, days=days)
        appliance_data = db.get_appliance_consumption(user_id)
        
        if not appliance_data or len(appliance_data) == 0:
            return jsonify({'error': 'No data available'}), 404
        
        # If no daily data, generate sample timeline
        if not daily_data or len(daily_data) == 0:
            dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
            appliance_df = pd.DataFrame(appliance_data).head(5)  # Top 5 appliances
            
            timeline_data = []
            for date in dates:
                for _, appliance in appliance_df.iterrows():
                    # Simulate daily variations (±20%)
                    # Convert Decimal to float
                    total_kwh = float(appliance['total_kwh'])
                    daily_kwh = (total_kwh / 30) * np.random.uniform(0.8, 1.2)
                    timeline_data.append({
                        'date': date,
                        'appliance_name': appliance['appliance_name'],
                        'kwh': daily_kwh
                    })
            timeline_df = pd.DataFrame(timeline_data)
        else:
            # In real scenario, we would join with appliance daily logs
            # For now, simulate from existing data
            dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq='D')
            appliance_df = pd.DataFrame(appliance_data).head(5)
            
            timeline_data = []
            for date in dates:
                for _, appliance in appliance_df.iterrows():
                    # Convert Decimal to float
                    total_kwh = float(appliance['total_kwh'])
                    daily_kwh = (total_kwh / 30) * np.random.uniform(0.8, 1.2)
                    timeline_data.append({
                        'date': date,
                        'appliance_name': appliance['appliance_name'],
                        'kwh': daily_kwh
                    })
            timeline_df = pd.DataFrame(timeline_data)
        
        return_base64 = (format_type == 'base64')
        result = visualizer.plot_appliance_usage_timeline(timeline_df, return_base64=return_base64)
        
        if return_base64:
            return jsonify({'image': result}), 200
        else:
            return jsonify({'filepath': result}), 200
            
    except Exception as e:
        print(f"Error in visualize_appliance_usage_timeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')


@app.route('/login')
def login_page():
    """Login page"""
    return render_template('login.html')


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 50)
    print("Energy Consumption Tracker - Backend Server")
    print("=" * 50)
    print(f"Starting Flask server...")
    print(f"Frontend directory: {app.template_folder}")
    print(f"Static directory: {app.static_folder}")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
