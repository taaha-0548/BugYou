# 🐛 BugYou - Debugging Challenge Platform

[![Database](https://img.shields.io/badge/Database-PostgreSQL-blue.svg)](https://postgresql.org)
[![Backend](https://img.shields.io/badge/Backend-Flask-green.svg)](https://flask.palletsprojects.com)
[![Frontend](https://img.shields.io/badge/Frontend-Vanilla%20JS-yellow.svg)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Code Execution](https://img.shields.io/badge/Code%20Execution-Piston%20API-orange.svg)](https://piston.readthedocs.io)

A comprehensive platform for debugging challenges where users fix buggy code across multiple programming languages. Features dynamic challenge loading, output-based validation, and professional admin interface.

## 🎯 What is BugYou?

BugYou is an interactive debugging platform that helps students and developers improve their debugging skills by fixing buggy code across multiple programming languages. Each challenge presents broken code that needs to be fixed, with real-time testing and instant feedback.

**Key Features:**
- 🔤 **Multi-language Support**: Python, C++, Java, JavaScript
- 🎚️ **Difficulty Levels**: Basic, Intermediate, Advanced
- 🧪 **Real-time Testing**: Instant feedback with test cases
- 💡 **Hint System**: Progressive hints when stuck
- 👨‍💻 **Admin Interface**: Easy challenge creation for educators

## 🏗️ Project Structure

```
BugYou/
├── backend/                 # Flask API Server
│   ├── app.py              # Main Flask application
│   ├── database_config.py  # Database connection and functions
│   ├── run_server.py       # Alternative server startup
│   ├── setup_db.py         # Database setup script
│   ├── config.env          # Environment configuration
│   ├── requirements.txt    # Python dependencies
│   ├── database_setup.sql  # Database schema (creates empty tables)
│   ├── sample_data.sql     # Sample challenges (IMPORTANT!)
│   └── documentation/
├── frontend/               # Web Interface
│   ├── index.html         # Main application interface
│   ├── add_challenge.html # Admin challenge creation
│   ├── script.js          # Frontend JavaScript
│   └── styles.css         # Application styling
├── start_server.py        # Main startup script
├── README.md              # This file
└── LICENSE                # MIT License
```

## 🚀 Complete Setup Guide

### Step 1: Prerequisites and Installation

#### Required Software:
1. **Python 3.8+** - [Download here](https://www.python.org/downloads/)
2. **PostgreSQL** - [Download here](https://www.postgresql.org/download/)
3. **Git** - [Download here](https://git-scm.com/)

#### Clone the Repository:
```bash
git clone https://github.com/yourusername/BugYou.git
cd BugYou
```

#### Install Python Dependencies:
```bash
pip install -r backend/requirements.txt
```

### Step 2: Database Setup (CRITICAL)

This is the most important step! The database setup has two phases:

#### Phase 1: Install PostgreSQL
1. **Install PostgreSQL** on your system
2. **Create a database** named `bugyou`:
   ```sql
   CREATE DATABASE bugyou;
   ```
3. **Remember your credentials** (username, password, port)

#### Phase 2: Configure Database Connection
1. **Edit `backend/config.env`** with your database credentials:
   ```env
   DB_HOST=localhost
   DB_NAME=bugyou
   DB_USER=postgres
   DB_PASSWORD=your_password_here
   DB_PORT=5432
   ```

#### Phase 3: Create Database Schema
```bash
cd backend
python setup_db.py
```

**What this does:** Creates empty tables for challenges, users, sessions, etc.

#### Phase 4: Add Sample Challenges ⚠️ IMPORTANT!
**Without this step, you'll have empty tables with no challenges to work on!**

```bash
# Option 1: Using psql command line
psql -d bugyou -f sample_data.sql

# Option 2: Using PostgreSQL GUI tools (pgAdmin, DBeaver, etc.)
# Import the sample_data.sql file into your bugyou database

# Option 3: Using Python (alternative)
python -c "
import psycopg2
from database_config import DATABASE_CONFIG
conn = psycopg2.connect(**DATABASE_CONFIG)
cursor = conn.cursor()
with open('sample_data.sql', 'r') as f:
    cursor.execute(f.read())
conn.commit()
print('Sample data imported successfully!')
"
```

**What this does:** Adds 11 sample challenges across different languages and difficulty levels.

### Step 3: Start the Server

#### Option 1: Using the main startup script (Recommended)
```bash
# From project root
python start_server.py
```

#### Option 2: Using Flask directly
```bash
# From backend directory
cd backend
python app.py
```

### Step 4: Access the Platform

1. **Open your browser** to `http://localhost:5000`
2. **Verify it works** - you should see available challenges
3. **Try a challenge** - select a language and difficulty level

## 🎮 How to Use BugYou

### For Students:

1. **Select a Challenge**:
   - Choose language: Python, C++, Java, or JavaScript
   - Choose difficulty: Basic, Intermediate, or Advanced
   - Click on a challenge to start

2. **Fix the Bug**:
   - Read the problem description
   - Analyze the buggy code
   - Identify and fix the issue
   - Use hints if you get stuck

3. **Test Your Solution**:
   - Click "Run Code" to test your fix
   - Review test case results
   - Iterate until all tests pass

4. **Submit**:
   - Final validation against hidden test cases
   - Get score and feedback

### For Educators:

1. **Access Admin Interface**:
   - Click "➕ Admin" button on main page
   - Or go to `http://localhost:5000/admin`

2. **Create New Challenges**:
   - Fill in challenge details
   - Add buggy code and reference solution
   - Create test cases (3-5 recommended)
   - Add hints and learning objectives

3. **Manage Challenges**:
   - All challenges stored in database
   - Edit through admin interface
   - Set active/inactive status

## 🗄️ Database Details

### Database Architecture:
- **Type**: PostgreSQL (relational database)
- **Location**: Runs locally on your machine
- **Schema**: Separate tables for each language/difficulty combination

### Table Structure:
```
Language Tables:
├── python_basic         (Basic Python challenges)
├── python_intermediate  (Intermediate Python challenges)
├── python_advanced      (Advanced Python challenges)
├── cpp_basic           (Basic C++ challenges)
├── cpp_intermediate    (Intermediate C++ challenges)
├── cpp_advanced        (Advanced C++ challenges)
├── java_basic          (Basic Java challenges)
├── java_intermediate   (Intermediate Java challenges)
├── java_advanced       (Advanced Java challenges)
├── javascript_basic    (Basic JavaScript challenges)
├── javascript_intermediate (Intermediate JavaScript challenges)
└── javascript_advanced (Advanced JavaScript challenges)

System Tables:
├── users              (User accounts)
├── user_sessions      (Session tracking)
├── user_submissions   (Submission history)
└── user_progress      (Progress tracking)
```

### Sample Data Included:
- **11 debugging challenges** across different languages
- **Multiple difficulty levels** from basic to advanced
- **Real-world scenarios** like off-by-one errors, null handling, algorithm bugs
- **Test cases** with expected outputs for validation

## 🔧 Technical Details

### Backend (Flask API):
- **Framework**: Flask with RESTful API design
- **Database**: PostgreSQL with psycopg2 driver
- **Code Execution**: Piston API for secure sandboxed execution
- **File Structure**: Modular design with separate config and database modules

### Frontend (Web Interface):
- **Technology**: Pure HTML/CSS/JavaScript (no frameworks)
- **Code Editor**: Syntax highlighting and error detection
- **Responsive Design**: Works on desktop and mobile
- **AJAX Communication**: Real-time updates with backend

### API Endpoints:
```
GET  /                          # Main interface
GET  /admin                     # Admin interface
GET  /api/health                # Health check
GET  /api/challenge/{lang}/{diff}/{id}  # Load specific challenge
POST /api/execute               # Execute code
POST /api/submit                # Submit solution
POST /api/admin/add-challenge   # Create new challenge
```

## 🧪 Testing the Setup

### Verify Database Connection:
```bash
cd backend
python -c "
from database_config import test_connection
result = test_connection()
print('Database connection:', 'SUCCESS' if result else 'FAILED')
"
```

### Test API Endpoints:
```bash
# Health check
curl http://localhost:5000/api/health

# Load a challenge
curl http://localhost:5000/api/challenge/python/basic/1
```

### Check Sample Data:
```bash
cd backend
python -c "
from database_config import get_all_available_challenges
challenges = get_all_available_challenges()
print(f'Total challenges available: {len(challenges)}')
for c in challenges:
    print(f'- {c[\"language\"].title()} {c[\"difficulty\"].title()}: {c[\"title\"]}')
"
```

## 🐛 Troubleshooting

### Common Issues:

#### 1. Database Connection Failed
**Error**: `psycopg2.OperationalError: FATAL: password authentication failed`
**Solution**: 
- Check `backend/config.env` credentials
- Verify PostgreSQL is running
- Test connection with: `psql -h localhost -U postgres -d bugyou`

#### 2. Empty Challenge List
**Error**: No challenges appear on the website
**Solution**: 
- You forgot to import `sample_data.sql`!
- Run: `psql -d bugyou -f backend/sample_data.sql`

#### 3. Module Import Errors
**Error**: `ModuleNotFoundError: No module named 'flask'`
**Solution**: 
- Install dependencies: `pip install -r backend/requirements.txt`
- Make sure you're using the correct Python environment

#### 4. Port Already in Use
**Error**: `Address already in use`
**Solution**: 
- Change port in `backend/app.py` or kill the process using port 5000
- Or use: `python start_server.py --port 5001`

### Getting Help:
1. Check the console output for error messages
2. Verify all setup steps were completed
3. Test individual components (database, API, frontend)
4. Open an issue on GitHub with error details

## 🎯 What's Included

### Sample Challenges:
- **Python Basic**: Average calculator with division by zero bug
- **Python Intermediate**: Binary search with off-by-one error
- **Python Advanced**: Dijkstra's algorithm with multiple bugs
- **C++ Basic**: Array sum with bounds checking, max product logic
- **C++ Intermediate**: Function debugging (binary search, factorial, string reversal, palindrome check)
- **JavaScript & Java**: Additional challenges with similar patterns

### Admin Features:
- **Web-based challenge creation**
- **Test case management**
- **Code template generation**
- **Challenge activation/deactivation**
- **Progress tracking**

## 📈 Extending the Platform

### Adding New Languages:
1. Create new tables in `database_setup.sql`
2. Add language support in `database_config.py`
3. Update frontend language selector
4. Add code execution support

### Adding New Features:
1. **User Authentication**: Implement login/signup
2. **Progress Tracking**: Enhanced analytics dashboard
3. **Code Sharing**: Allow users to share solutions
4. **Competitions**: Timed challenges and leaderboards

## 🤝 Contributing

### How to Contribute:
1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Add features, fix bugs, improve documentation
4. **Test thoroughly**: Ensure all existing functionality works
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**: Describe your changes and why they're needed

### Development Setup:
```bash
# Clone your fork
git clone https://github.com/yourusername/BugYou.git
cd BugYou

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Set up database
cd backend
python setup_db.py
psql -d bugyou -f sample_data.sql

# Run tests
python -m pytest tests/
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚀 Deployment

### For Production:
1. **Use a production WSGI server** (not Flask's development server)
2. **Set up proper environment variables**
3. **Use a cloud PostgreSQL service** (AWS RDS, Google Cloud SQL, etc.)
4. **Configure HTTPS** for secure communication
5. **Set up monitoring and logging**

### Example Production Setup:
```bash
# Using gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using Docker
docker build -t bugyou .
docker run -p 5000:5000 bugyou
```

## 🎉 Getting Started Checklist

- [ ] Install Python 3.8+
- [ ] Install PostgreSQL
- [ ] Clone the repository
- [ ] Install dependencies (`pip install -r backend/requirements.txt`)
- [ ] Create database (`CREATE DATABASE bugyou;`)
- [ ] Configure credentials in `backend/config.env`
- [ ] Run database setup (`python setup_db.py`)
- [ ] Import sample data (`psql -d bugyou -f sample_data.sql`)
- [ ] Start server (`python start_server.py`)
- [ ] Open browser to `http://localhost:5000`
- [ ] Try a challenge!

## 🆘 Support

### If you encounter issues:
1. **Check this README** - most common issues are covered
2. **Review the troubleshooting section** above
3. **Check the console output** for error messages
4. **Verify all setup steps** were completed correctly
5. **Open an issue** on GitHub with:
   - Your operating system
   - Python version
   - PostgreSQL version
   - Error messages
   - Steps to reproduce

### Contact:
- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/BugYou/issues)
- **Documentation**: Check the `backend/` folder for technical documentation

---

**🎯 Ready to start debugging? Follow the setup guide above and you'll be fixing bugs in no time!** 🚀 
