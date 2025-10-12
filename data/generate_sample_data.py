"""
Sample Data Generator
Generates realistic energy consumption data for testing
"""

import mysql.connector
from datetime import datetime, timedelta
import random
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

from database.db_config import DatabaseConfig

# Appliance profiles (name, typical_kwh_per_use, usage_probability)
APPLIANCES = [
    ('Air Conditioner', 3.5, 0.3, [17, 18, 19, 20, 21, 22]),  # Evening hours
    ('Refrigerator', 0.15, 0.95, list(range(24))),  # All day
    ('Washing Machine', 1.2, 0.15, [8, 9, 10, 19, 20]),  # Morning and evening
    ('Dryer', 2.5, 0.1, [9, 10, 20, 21]),
    ('Dishwasher', 1.5, 0.2, [20, 21, 22]),  # Evening
    ('Microwave', 0.3, 0.4, [7, 8, 12, 13, 18, 19, 20]),  # Meal times
    ('Electric Oven', 2.0, 0.15, [12, 18, 19]),  # Lunch and dinner
    ('Television', 0.15, 0.6, [18, 19, 20, 21, 22, 23]),  # Evening
    ('Computer', 0.2, 0.5, [9, 10, 11, 14, 15, 16, 19, 20]),  # Work hours
    ('Water Heater', 3.0, 0.3, [6, 7, 8, 19, 20, 21]),  # Morning and evening
    ('LED Lights', 0.01, 0.8, [6, 7, 8, 18, 19, 20, 21, 22, 23]),  # Morning and evening
]


def generate_sample_data(user_id, days=90, tariff_rate=0.12):
    """
    Generate sample energy consumption data
    
    Args:
        user_id: User ID to generate data for
        days: Number of days of data to generate
        tariff_rate: Cost per kWh
    """
    db = DatabaseConfig()
    db.connect()
    
    records_added = 0
    start_date = datetime.now() - timedelta(days=days)
    
    print(f"Generating {days} days of sample data for user {user_id}...")
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Weekend vs weekday variation
        is_weekend = current_date.weekday() >= 5
        activity_multiplier = 1.3 if is_weekend else 1.0
        
        # Generate hourly records
        for hour in range(24):
            timestamp = current_date.replace(hour=hour, minute=random.randint(0, 59))
            
            # Determine which appliances to use this hour
            for appliance_name, typical_kwh, base_prob, active_hours in APPLIANCES:
                # Adjust probability based on time of day
                if hour in active_hours:
                    probability = base_prob * activity_multiplier
                else:
                    probability = base_prob * 0.3  # Lower probability outside active hours
                
                # Random chance to use this appliance
                if random.random() < probability:
                    # Add some variation to power usage
                    variation = random.uniform(0.8, 1.2)
                    power_usage = typical_kwh * variation
                    
                    # Duration (most appliances run for 1 hour, some longer)
                    if appliance_name in ['Refrigerator', 'Water Heater']:
                        duration = 1.0
                    else:
                        duration = random.uniform(0.5, 2.0)
                    
                    # Calculate cost
                    cost = power_usage * tariff_rate
                    
                    # Add record
                    success = db.add_energy_record(
                        user_id=user_id,
                        timestamp=timestamp,
                        appliance_name=appliance_name,
                        power_usage_kwh=round(power_usage, 4),
                        cost=round(cost, 2),
                        duration_hours=round(duration, 2)
                    )
                    
                    if success:
                        records_added += 1
        
        # Progress update
        if (day + 1) % 10 == 0:
            print(f"Progress: {day + 1}/{days} days completed...")
    
    db.disconnect()
    print(f"\nData generation complete!")
    print(f"Total records added: {records_added}")
    return records_added


def main():
    """Main function"""
    print("=" * 60)
    print("Energy Consumption Tracker - Sample Data Generator")
    print("=" * 60)
    
    # Get user input
    user_id = input("Enter user ID (default: 1): ").strip() or "1"
    days = input("Enter number of days (default: 90): ").strip() or "90"
    tariff_rate = input("Enter tariff rate $/kWh (default: 0.12): ").strip() or "0.12"
    
    try:
        user_id = int(user_id)
        days = int(days)
        tariff_rate = float(tariff_rate)
        
        # Confirm
        print(f"\nGenerating data with:")
        print(f"  User ID: {user_id}")
        print(f"  Days: {days}")
        print(f"  Tariff Rate: ${tariff_rate}/kWh")
        
        confirm = input("\nProceed? (y/n): ").strip().lower()
        
        if confirm == 'y':
            generate_sample_data(user_id, days, tariff_rate)
        else:
            print("Operation cancelled.")
            
    except ValueError as e:
        print(f"Error: Invalid input - {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
