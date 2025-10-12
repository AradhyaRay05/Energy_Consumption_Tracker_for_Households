# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites Check
```bash
python --version    # Should be 3.8+
mysql --version     # Should be 8.0+
```

### Step 1: Install Dependencies
```bash
cd "d:\Education\Coding\Machine Learning\Energy-Consumption-Tracker"
pip install -r requirements.txt
```

### Step 2: Set Up Database

**Option A: Using MySQL Workbench**
1. Open MySQL Workbench
2. Connect to your MySQL server
3. Go to File > Run SQL Script
4. Select `database/schema.sql`
5. Click Run

**Option B: Using Command Line**
```bash
mysql -u root -p < database/schema.sql
```

### Step 3: Configure Environment

Create `.env` file:
```bash
copy .env.example .env
```

Edit `.env` with your database password:
```
DB_PASSWORD=your_mysql_password
SECRET_KEY=your_random_secret_key_here
```

### Step 4: Generate Sample Data (Optional but Recommended)
```bash
python data/generate_sample_data.py
```

When prompted:
- User ID: `1` (press Enter)
- Days: `90` (press Enter)
- Tariff Rate: `0.12` (press Enter)
- Proceed: `y`

This will generate 90 days of realistic energy consumption data.

### Step 5: Run the Application
```bash
python backend/app.py
```

### Step 6: Access the Application

Open your browser and go to:
```
http://localhost:5000
```

### Step 7: Login

**Demo Account:**
- Username: `demo_user`
- Password: `password123`

OR create your own account by clicking "Register"

---

## 🎯 What to Try First

1. **View Dashboard** - See your energy statistics at a glance
2. **Check Insights** - Get personalized energy-saving recommendations
3. **View Charts** - Explore daily and appliance consumption visualizations
4. **Generate Predictions** - Click "Generate Predictions" to see AI forecasts
5. **Add Data** - Try adding a new energy consumption record

---

## 🔧 Troubleshooting

### Database Connection Error
- Verify MySQL is running
- Check credentials in `.env`
- Ensure `energy_tracker` database exists

### Port Already in Use
Change the port in `backend/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Module Import Errors
Ensure virtual environment is activated and all dependencies are installed:
```bash
pip install -r requirements.txt
```

### No Data Available
Run the sample data generator:
```bash
python data/generate_sample_data.py
```

---

## 📊 Sample Workflows

### Workflow 1: Track Your Daily Usage
1. Login to dashboard
2. Click "Add Data" in sidebar
3. Select appliance (e.g., "Air Conditioner")
4. Enter power usage (e.g., 3.5 kWh)
5. Set duration (e.g., 4 hours)
6. Select date/time
7. Click "Add Record"
8. View updated statistics immediately

### Workflow 2: Analyze Monthly Trends
1. Navigate to dashboard
2. Select "Last 90 Days" from dropdown
3. View daily consumption chart
4. Check appliance breakdown
5. Identify high-usage appliances
6. Read personalized insights
7. Follow recommendations to reduce costs

### Workflow 3: Plan Future Budget
1. Click "Predictions" in sidebar
2. Click "Generate Predictions"
3. View 7-day forecast
4. Check monthly estimate
5. Use predictions to plan energy usage
6. Adjust habits based on forecasts

---

## 📝 Testing the API

You can test API endpoints using `curl` or Postman:

### Test Authentication
```bash
# Register
curl -X POST http://localhost:5000/api/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"test123\",\"full_name\":\"Test User\"}"

# Login
curl -X POST http://localhost:5000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"demo_user\",\"password\":\"password123\"}" ^
  -c cookies.txt

# Get dashboard summary
curl http://localhost:5000/api/dashboard/summary?days=30 ^
  -b cookies.txt
```

---

## 🎨 Customization

### Change Tariff Rate
Update in user settings or directly in database:
```sql
UPDATE users SET tariff_rate = 0.15 WHERE user_id = 1;
```

### Modify Appliance List
Edit `frontend/templates/dashboard.html` and update the appliance dropdown.

### Change Chart Colors
Edit `ml_models/visualizations.py` and modify the `colors` dictionary.

---

## 📚 Next Steps

1. ✅ Complete this quick start guide
2. 📖 Read the full [README.md](README.md)
3. 🔍 Explore the API documentation
4. 🤖 Learn about the ML model
5. 🛠️ Customize for your needs
6. 🚀 Deploy to production (future)

---

## 💡 Tips

- **Regular Data Entry:** Enter data daily for best predictions
- **Appliance Tracking:** Track high-power appliances more carefully
- **Use Insights:** Follow the AI recommendations to save 10-15%
- **Check Predictions:** Review weekly forecasts every Monday
- **Monitor Trends:** Look for unusual spikes in consumption

---

## 🆘 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Open an issue on GitHub
- Review the code comments
- Check console logs in browser (F12)

---

**Happy Energy Tracking! ⚡**
