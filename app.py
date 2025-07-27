
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'uncbudget2025'

DB_NAME = os.path.join(os.path.dirname(__file__), 'budgeter.db')

def init_db():
    if not os.path.exists(DB_NAME):
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute("""CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL)""")
            c.execute("""CREATE TABLE IF NOT EXISTS expenses (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            category TEXT,
                            amount REAL,
                            date TEXT,
                            FOREIGN KEY(user_id) REFERENCES users(id))""")

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            try:
                conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
                conn.commit()
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                return 'Username already exists.'
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect(DB_NAME) as conn:
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE username=? AND password=?', (username, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect(url_for('dashboard'))
            else:
                return 'Login failed. Check your credentials.'
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('SELECT category, amount, date FROM expenses WHERE user_id=?', (user_id,))
        expenses = c.fetchall()
    return render_template('dashboard.html', expenses=expenses)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    category = request.form['category']
    amount = float(request.form['amount'])
    date = datetime.now().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('INSERT INTO expenses (user_id, category, amount, date) VALUES (?, ?, ?, ?)',
                     (session['user_id'], category, amount, date))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/loan_calculator', methods=['GET', 'POST'])
def loan_calculator():
    result = None
    if request.method == 'POST':
        loan = float(request.form['loan'])
        rate = float(request.form['rate']) / 100 / 12
        term = int(request.form['term']) * 12
        if rate == 0:
            monthly = loan / term
        else:
            monthly = loan * rate * (1 + rate)**term / ((1 + rate)**term - 1)
        result = round(monthly, 2)
    return render_template('loan_calculator.html', result=result)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
