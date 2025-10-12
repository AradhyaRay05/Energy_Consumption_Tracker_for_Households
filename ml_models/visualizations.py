"""
Data Visualization Module
Creates charts and graphs for energy consumption analysis
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Flask
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import io
import base64

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class EnergyVisualizer:
    """Creates visualizations for energy consumption data"""
    
    def __init__(self, output_dir='static/plots'):
        """
        Initialize visualizer
        
        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Color palette
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'accent': '#F18F01',
            'success': '#06A77D',
            'warning': '#F77F00',
            'danger': '#D62828'
        }
    
    def _save_figure(self, fig, filename, return_base64=False):
        """
        Save figure to file or return as base64 string
        
        Args:
            fig: Matplotlib figure object
            filename: Output filename
            return_base64: If True, return base64 encoded string instead of saving
        
        Returns:
            Filepath or base64 string
        """
        if return_base64:
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            return f"data:image/png;base64,{img_base64}"
        else:
            filepath = os.path.join(self.output_dir, filename)
            fig.savefig(filepath, dpi=100, bbox_inches='tight')
            plt.close(fig)
            return filepath
    
    def plot_daily_consumption(self, daily_data, days=30, save_as='daily_consumption.png', return_base64=False):
        """
        Plot daily energy consumption trend
        
        Args:
            daily_data: DataFrame with columns: date, total_kwh, total_cost
            days: Number of recent days to plot
            save_as: Output filename
            return_base64: Return as base64 string
        
        Returns:
            Filepath or base64 string
        """
        df = daily_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').tail(days)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Energy consumption plot
        ax1.plot(df['date'], df['total_kwh'], 
                marker='o', linewidth=2, markersize=4,
                color=self.colors['primary'], label='Daily Consumption')
        ax1.fill_between(df['date'], df['total_kwh'], alpha=0.3, color=self.colors['primary'])
        ax1.set_title('Daily Energy Consumption (kWh)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date', fontsize=11)
        ax1.set_ylabel('Energy (kWh)', fontsize=11)
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Rotate x-axis labels
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Cost plot
        ax2.bar(df['date'], df['total_cost'], 
               color=self.colors['accent'], alpha=0.7, label='Daily Cost')
        ax2.set_title('Daily Energy Cost ($)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=11)
        ax2.set_ylabel('Cost ($)', fontsize=11)
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.legend()
        
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        plt.tight_layout()
        return self._save_figure(fig, save_as, return_base64)
    
    def plot_appliance_breakdown(self, appliance_data, top_n=10, save_as='appliance_breakdown.png', return_base64=False):
        """
        Plot appliance-wise energy consumption
        
        Args:
            appliance_data: DataFrame with columns: appliance_name, total_kwh, total_cost
            top_n: Number of top appliances to show
            save_as: Output filename
            return_base64: Return as base64 string
        """
        df = appliance_data.copy()
        df = df.sort_values('total_kwh', ascending=False).head(top_n)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar chart
        bars = ax1.barh(df['appliance_name'], df['total_kwh'], 
                       color=self.colors['secondary'], alpha=0.7)
        ax1.set_title('Energy Consumption by Appliance (kWh)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Energy (kWh)', fontsize=11)
        ax1.set_ylabel('Appliance', fontsize=11)
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Add value labels
        for bar in bars:
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{width:.2f}', ha='left', va='center', fontsize=9)
        
        # Pie chart
        colors_pie = sns.color_palette("husl", len(df))
        wedges, texts, autotexts = ax2.pie(df['total_kwh'], labels=df['appliance_name'], 
                                           autopct='%1.1f%%', startangle=90,
                                           colors=colors_pie)
        ax2.set_title('Energy Distribution by Appliance', fontsize=14, fontweight='bold')
        
        # Improve pie chart text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
        
        plt.tight_layout()
        return self._save_figure(fig, save_as, return_base64)
    
    def plot_hourly_pattern(self, hourly_data, save_as='hourly_pattern.png', return_base64=False):
        """
        Plot average energy consumption by hour of day
        
        Args:
            hourly_data: DataFrame with timestamp and power_usage_kwh
            save_as: Output filename
            return_base64: Return as base64 string
        """
        df = hourly_data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['timestamp'].dt.hour
        
        # Calculate average consumption per hour
        hourly_avg = df.groupby('hour')['power_usage_kwh'].mean().reset_index()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.bar(hourly_avg['hour'], hourly_avg['power_usage_kwh'], 
                     color=self.colors['success'], alpha=0.7)
        
        # Highlight peak hours
        peak_hour = hourly_avg.loc[hourly_avg['power_usage_kwh'].idxmax(), 'hour']
        bars[int(peak_hour)].set_color(self.colors['danger'])
        
        ax.set_title('Average Energy Consumption by Hour of Day', fontsize=14, fontweight='bold')
        ax.set_xlabel('Hour of Day', fontsize=11)
        ax.set_ylabel('Average Energy (kWh)', fontsize=11)
        ax.set_xticks(range(24))
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add peak hour annotation
        ax.annotate(f'Peak Hour: {int(peak_hour)}:00', 
                   xy=(peak_hour, hourly_avg.loc[hourly_avg['hour'] == peak_hour, 'power_usage_kwh'].values[0]),
                   xytext=(peak_hour + 2, hourly_avg['power_usage_kwh'].max() * 0.9),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2),
                   fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        return self._save_figure(fig, save_as, return_base64)
    
    def plot_weekly_pattern(self, daily_data, save_as='weekly_pattern.png', return_base64=False):
        """
        Plot average energy consumption by day of week
        
        Args:
            daily_data: DataFrame with date and total_kwh
            save_as: Output filename
            return_base64: Return as base64 string
        """
        df = daily_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        
        # Calculate average consumption per day of week
        weekly_avg = df.groupby('day_of_week')['total_kwh'].mean().reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        colors = [self.colors['primary'] if i < 5 else self.colors['accent'] for i in range(7)]
        
        bars = ax.bar(range(7), weekly_avg['total_kwh'], color=colors, alpha=0.7)
        ax.set_title('Average Energy Consumption by Day of Week', fontsize=14, fontweight='bold')
        ax.set_xlabel('Day of Week', fontsize=11)
        ax.set_ylabel('Average Energy (kWh)', fontsize=11)
        ax.set_xticks(range(7))
        ax.set_xticklabels(days, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height,
                   f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        return self._save_figure(fig, save_as, return_base64)
    
    def plot_prediction_vs_actual(self, actual_data, predicted_data, days=30, 
                                  save_as='prediction_comparison.png', return_base64=False):
        """
        Plot predicted vs actual consumption
        
        Args:
            actual_data: DataFrame with date and total_kwh (actual)
            predicted_data: DataFrame with date and predicted_kwh
            days: Number of days to show
            save_as: Output filename
            return_base64: Return as base64 string
        """
        actual = actual_data.copy().tail(days)
        actual['date'] = pd.to_datetime(actual['date'])
        
        predicted = predicted_data.copy()
        predicted['date'] = pd.to_datetime(predicted['date'])
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot actual data
        ax.plot(actual['date'], actual['total_kwh'], 
               marker='o', linewidth=2, markersize=5,
               color=self.colors['primary'], label='Actual', alpha=0.8)
        
        # Plot predictions
        ax.plot(predicted['date'], predicted['predicted_kwh'], 
               marker='s', linewidth=2, markersize=5, linestyle='--',
               color=self.colors['danger'], label='Predicted', alpha=0.8)
        
        # Add prediction range (confidence interval)
        if 'confidence_score' in predicted.columns:
            lower_bound = predicted['predicted_kwh'] * 0.9
            upper_bound = predicted['predicted_kwh'] * 1.1
            ax.fill_between(predicted['date'], lower_bound, upper_bound, 
                           color=self.colors['danger'], alpha=0.2)
        
        ax.set_title('Energy Consumption: Actual vs Predicted', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date', fontsize=11)
        ax.set_ylabel('Energy (kWh)', fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=11)
        
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        plt.tight_layout()
        
        return self._save_figure(fig, save_as, return_base64)
    
    def plot_monthly_trend(self, monthly_data, months=12, save_as='monthly_trend.png', return_base64=False):
        """
        Plot monthly energy consumption trend
        
        Args:
            monthly_data: DataFrame with year, month, total_kwh, total_cost
            months: Number of recent months to plot
            save_as: Output filename
            return_base64: Return as base64 string
        """
        df = monthly_data.copy()
        df['date'] = pd.to_datetime(df[['year', 'month']].assign(day=1))
        df = df.sort_values('date').tail(months)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Bar chart with line overlay
        bars = ax.bar(range(len(df)), df['total_kwh'], 
                     color=self.colors['secondary'], alpha=0.6, label='Monthly Consumption')
        ax2 = ax.twinx()
        line = ax2.plot(range(len(df)), df['total_cost'], 
                       color=self.colors['warning'], marker='o', linewidth=2,
                       label='Monthly Cost')
        
        # Formatting
        month_labels = df['date'].dt.strftime('%b %Y')
        ax.set_xticks(range(len(df)))
        ax.set_xticklabels(month_labels, rotation=45, ha='right')
        ax.set_title('Monthly Energy Consumption and Cost', fontsize=14, fontweight='bold')
        ax.set_xlabel('Month', fontsize=11)
        ax.set_ylabel('Energy (kWh)', fontsize=11, color=self.colors['secondary'])
        ax2.set_ylabel('Cost ($)', fontsize=11, color=self.colors['warning'])
        ax.grid(True, alpha=0.3, axis='y')
        
        # Combine legends
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        plt.tight_layout()
        return self._save_figure(fig, save_as, return_base64)
    
    def create_dashboard_summary(self, stats_dict, save_as='dashboard_summary.png', return_base64=False):
        """
        Create a summary visualization with key statistics
        
        Args:
            stats_dict: Dictionary with keys: total_kwh, total_cost, avg_daily, peak_day, etc.
            save_as: Output filename
            return_base64: Return as base64 string
        """
        fig = plt.figure(figsize=(12, 6))
        gs = fig.add_gridspec(2, 3, hspace=0.4, wspace=0.3)
        
        # Define stat cards
        stats = [
            ('Total Consumption', f"{stats_dict.get('total_kwh', 0):.2f} kWh", self.colors['primary']),
            ('Total Cost', f"${stats_dict.get('total_cost', 0):.2f}", self.colors['accent']),
            ('Avg Daily Usage', f"{stats_dict.get('avg_daily', 0):.2f} kWh", self.colors['success']),
            ('Peak Day', f"{stats_dict.get('peak_day', 'N/A')}", self.colors['danger']),
            ('Carbon Footprint', f"{stats_dict.get('carbon_kg', 0):.1f} kg CO₂", self.colors['warning']),
            ('Efficiency Score', f"{stats_dict.get('efficiency_score', 0):.0f}/100", self.colors['secondary'])
        ]
        
        # Create stat cards
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        
        for (row, col), (title, value, color) in zip(positions, stats):
            ax = fig.add_subplot(gs[row, col])
            ax.text(0.5, 0.6, value, ha='center', va='center', 
                   fontsize=20, fontweight='bold', color=color)
            ax.text(0.5, 0.3, title, ha='center', va='center',
                   fontsize=12, color='gray')
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            
            # Add background
            rect = plt.Rectangle((0.05, 0.1), 0.9, 0.8, 
                                fill=True, facecolor=color, alpha=0.1,
                                edgecolor=color, linewidth=2)
            ax.add_patch(rect)
        
        fig.suptitle('Energy Consumption Dashboard', fontsize=16, fontweight='bold', y=0.98)
        
        return self._save_figure(fig, save_as, return_base64)


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-09-01', end='2024-10-10', freq='D')
    daily_data = pd.DataFrame({
        'date': dates,
        'total_kwh': np.random.uniform(15, 35, len(dates)),
        'total_cost': np.random.uniform(1.8, 4.2, len(dates))
    })
    
    appliance_data = pd.DataFrame({
        'appliance_name': ['Air Conditioner', 'Refrigerator', 'TV', 'Washing Machine', 
                          'Dishwasher', 'Microwave', 'Computer'],
        'total_kwh': [120, 80, 45, 35, 30, 15, 25],
        'total_cost': [14.4, 9.6, 5.4, 4.2, 3.6, 1.8, 3.0]
    })
    
    # Create visualizer
    viz = EnergyVisualizer(output_dir='plots')
    
    # Generate plots
    viz.plot_daily_consumption(daily_data)
    viz.plot_appliance_breakdown(appliance_data)
    
    print("Visualizations created successfully!")
