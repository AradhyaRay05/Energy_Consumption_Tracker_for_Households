"""
Database Configuration Module
Handles MySQL connection and common database operations
"""

import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime, timedelta
import pandas as pd

class DatabaseConfig:
    """Database configuration and connection manager"""
    
    def __init__(self):
        """Initialize database configuration"""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '3306')
        self.database = os.getenv('DB_NAME', 'energy_tracker')
        self.user = os.getenv('DB_USER', 'root')
        self.password = os.getenv('DB_PASSWORD', '')
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            # Close existing connection if any
            if self.connection:
                try:
                    self.connection.close()
                except:
                    pass
                
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=True,  # Enable autocommit to prevent locks
                use_pure=True,  # Use pure Python implementation (no C extension issues)
                ssl_disabled=True,  # Disable SSL to avoid SSL errors
                connection_timeout=10  # Add 10 second timeout
            )
            print(f"Successfully connected to MySQL database: {self.database}")
            return True
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return False
    
    def ensure_connection(self):
        """Ensure database connection is active, reconnect if needed"""
        try:
            if self.connection is None or not self.connection.is_connected():
                print("Connection lost, reconnecting...")
                return self.connect()
            return True
        except Error as e:
            print(f"Error checking connection: {e}")
            return self.connect()
    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed")
    
    def execute_query(self, query, params=None, fetch=False):
        """
        Execute a SQL query
        
        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)
            fetch: Whether to fetch results (TRUE for SELECT queries)
        
        Returns:
            Query results if fetch=True, otherwise affected row count
        """
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Check if connection exists
                if self.connection is None:
                    if not self.connect():
                        return None if fetch else 0
                
                # Try to create cursor, if it fails due to is_connected() error, reconnect
                try:
                    cursor = self.connection.cursor(dictionary=True)
                except (Error, IndexError) as cursor_error:
                    print(f"Error creating cursor: {cursor_error}, reconnecting...")
                    try:
                        if self.connection:
                            self.connection.close()
                    except:
                        pass
                    if not self.connect():
                        return None if fetch else 0
                    cursor = self.connection.cursor(dictionary=True)
                
                cursor.execute(query, params or ())
                
                if fetch:
                    results = cursor.fetchall()
                    cursor.close()
                    return results
                else:
                    # No need to commit since autocommit is enabled
                    affected_rows = cursor.rowcount
                    cursor.close()
                    return affected_rows
                    
            except Error as e:
                print(f"Error executing query (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Try to reconnect
                    try:
                        if self.connection:
                            self.connection.close()
                    except:
                        pass
                    self.connect()
                else:
                    return None if fetch else 0
        
        return None if fetch else 0
    
    def get_user_by_username(self, username):
        """Get user details by username"""
        query = "SELECT * FROM users WHERE username = %s"
        result = self.execute_query(query, (username,), fetch=True)
        return result[0] if result else None
    
    def get_user_by_id(self, user_id):
        """Get user details by ID"""
        query = "SELECT * FROM users WHERE user_id = %s"
        result = self.execute_query(query, (user_id,), fetch=True)
        return result[0] if result else None
    
    def create_user(self, username, email, password_hash, full_name, household_size=1, tariff_rate=0.12):
        """Create a new user"""
        query = """
        INSERT INTO users (username, email, password_hash, full_name, household_size, tariff_rate)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        affected = self.execute_query(query, (username, email, password_hash, full_name, household_size, tariff_rate))
        return affected > 0
    
    def get_energy_data(self, user_id, start_date=None, end_date=None, limit=None):
        """
        Get energy consumption data for a user
        
        Args:
            user_id: User ID
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            limit: Maximum number of records (optional)
        """
        query = "SELECT * FROM energy_data WHERE user_id = %s"
        params = [user_id]
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.execute_query(query, tuple(params), fetch=True)
    
    def add_energy_record(self, user_id, timestamp, appliance_name, power_usage_kwh, cost, duration_hours=1.0):
        """Add a new energy consumption record"""
        query = """
        INSERT INTO energy_data (user_id, timestamp, appliance_name, power_usage_kwh, cost, duration_hours)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        affected = self.execute_query(
            query, 
            (user_id, timestamp, appliance_name, power_usage_kwh, cost, duration_hours)
        )
        return affected > 0
    
    def get_daily_consumption(self, user_id, days=30):
        """Get daily consumption summary for the last N days"""
        query = """
        SELECT * FROM daily_consumption 
        WHERE user_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
        ORDER BY date DESC
        """
        return self.execute_query(query, (user_id, days), fetch=True)
    
    def get_appliance_consumption(self, user_id):
        """Get appliance-wise consumption summary"""
        query = "SELECT * FROM appliance_consumption WHERE user_id = %s ORDER BY total_kwh DESC"
        return self.execute_query(query, (user_id,), fetch=True)
    
    def get_monthly_statistics(self, user_id, months=12):
        """Get monthly statistics for the last N months"""
        query = """
        SELECT * FROM monthly_statistics 
        WHERE user_id = %s 
        ORDER BY year DESC, month DESC
        LIMIT %s
        """
        return self.execute_query(query, (user_id, months), fetch=True)
    
    def save_prediction(self, user_id, prediction_date, predicted_kwh, predicted_cost, 
                       confidence_score=None, prediction_type='daily'):
        """Save a prediction to the database"""
        query = """
        INSERT INTO predictions 
        (user_id, prediction_date, predicted_consumption_kwh, predicted_cost, 
         confidence_score, prediction_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        affected = self.execute_query(
            query,
            (user_id, prediction_date, predicted_kwh, predicted_cost, confidence_score, prediction_type)
        )
        return affected > 0
    
    def get_predictions(self, user_id, prediction_type='daily', limit=30):
        """Get predictions for a user"""
        query = """
        SELECT * FROM predictions 
        WHERE user_id = %s AND prediction_type = %s
        ORDER BY prediction_date DESC
        LIMIT %s
        """
        return self.execute_query(query, (user_id, prediction_type, limit), fetch=True)
    
    def add_insight(self, user_id, insight_text, insight_type='general', priority='medium'):
        """Add a personalized insight for the user"""
        query = """
        INSERT INTO insights (user_id, insight_text, insight_type, priority)
        VALUES (%s, %s, %s, %s)
        """
        affected = self.execute_query(query, (user_id, insight_text, insight_type, priority))
        return affected > 0
    
    def get_unread_insights(self, user_id, limit=10):
        """Get unread insights for a user"""
        query = """
        SELECT * FROM insights 
        WHERE user_id = %s AND is_read = FALSE
        ORDER BY priority DESC, created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (user_id, limit), fetch=True)
    
    def mark_insight_read(self, insight_id):
        """Mark an insight as read"""
        query = "UPDATE insights SET is_read = TRUE WHERE insight_id = %s"
        return self.execute_query(query, (insight_id,)) > 0
    
    def get_data_as_dataframe(self, user_id, start_date=None, end_date=None):
        """Get energy data as pandas DataFrame for ML processing"""
        data = self.get_energy_data(user_id, start_date, end_date)
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame()


# Usage Example
if __name__ == "__main__":
    # Test database connection
    db = DatabaseConfig()
    if db.connect():
        print("Database connection successful!")
        
        # Test query
        result = db.execute_query("SELECT COUNT(*) as count FROM users", fetch=True)
        print(f"Number of users: {result[0]['count']}")
        
        db.disconnect()
