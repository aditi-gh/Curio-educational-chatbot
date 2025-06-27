import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure Flask app
app.secret_key = os.getenv('SECRET_KEY')  # Get from .env file 

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')  # Get from .env file
if not GOOGLE_API_KEY:
    raise ValueError("No GOOGLE_API_KEY set in environment variables")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(id=user_data[0], username=user_data[1])
    return None

# Predefined educational prompts and responses
EDUCATIONAL_PROMPTS = {
    "math": {
        "algebra": "Algebra is a branch of mathematics dealing with symbols and the rules for manipulating those symbols.",
        "geometry": "Geometry is a branch of mathematics concerned with questions of shape, size, and the properties of space.",
        "calculus": "Calculus is the mathematical study of continuous change."
    },
    "science": {
        "physics": "Physics is the natural science that studies matter, its motion and behavior through space and time.",
        "chemistry": "Chemistry is the scientific study of the properties and behavior of matter.",
        "biology": "Biology is the natural science that studies life and living organisms."
    },
    "history": {
        "world": "World history encompasses the study of significant events throughout human history across all regions.",
        "american": "American history covers the major events and developments in what is now the United States."
    },
    "literature": {
        "english": "English literature includes written works in the English language from various countries.",
        "american": "American literature refers to written or literary work produced in the United States."
    }
}

def is_educational_topic(topic):
    """Check if the topic is educational by querying Gemini"""
    try:
        response = model.generate_content(
            f"Is '{topic}' an educational topic suitable for a school or university curriculum? Answer only 'yes' or 'no'."
        )
        return response.text.strip().lower() == 'yes'
    except Exception as e:
        print(f"Error checking educational topic: {e}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(id=user_data[0], username=user_data[1])
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('chat'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chat'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if len(username) < 4:
            flash('Username must be at least 4 characters long', 'error')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('register'))
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', 
                          (username, generate_password_hash(password)))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username already exists', 'error')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('home'))

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html', username=current_user.username)

@app.route('/get_response', methods=['POST'])
@login_required
def get_response():
    user_input = request.json['user_input'].lower()
    response = None
    
    # Check predefined prompts first
    found = False
    for category, topics in EDUCATIONAL_PROMPTS.items():
        if category in user_input:
            for topic, answer in topics.items():
                if topic in user_input:
                    response = answer
                    found = True
                    break
            if found:
                break
    
    # If not found in predefined, check if it's educational
    if not found:
        if is_educational_topic(user_input):
            try:
                gemini_response = model.generate_content(
                    f"Provide a concise educational answer (under 200 words) to: {user_input}"
                )
                response = gemini_response.text
            except Exception as e:
                print(f"Error generating response: {e}")
                response = "Sorry, I couldn't process your educational question at the moment."
        else:
            response = "This is an educational chatbot. Your question doesn't appear to be related to education."
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().strftime('%I:%M %p')
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    # Check if essential environment variables are set
    if not app.secret_key:
        raise ValueError("No SECRET_KEY set in environment variables")
    app.run(debug=True)