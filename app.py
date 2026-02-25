from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, send_file)
import sqlite3, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

app = Flask(__name__)
app.secret_key = 'kavisDairyMilkSecret2026!'
DATABASE = 'dairy.db'
EXCEL_FILE = 'dairy_data.xlsx'


# ───────────────── DATABASE HELPERS ─────────────────

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    db = get_db()

    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT,
            password TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            unit TEXT DEFAULT 'litre',
            emoji TEXT DEFAULT '🥛',
            stock INTEGER DEFAULT 100,
            category TEXT DEFAULT 'Milk'
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT DEFAULT 'Confirmed',
            address TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        );
    ''')

    # Create admin if not exists
    if not db.execute("SELECT id FROM users WHERE username='admin'").fetchone():
        db.execute(
            "INSERT INTO users (name,username,email,password,is_admin) VALUES (?,?,?,?,?)",
            ('Administrator', 'admin', 'admin@kavifarm.com',
             generate_password_hash('admin123'), 1)
        )

    db.commit()
    db.close()


# ───────────────── ROUTES ─────────────────

@app.route('/')
def index():
    db = get_db()
    products = db.execute("SELECT * FROM products LIMIT 6").fetchall()
    db.close()
    return render_template('index.html', products=products)


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        db.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['is_admin'] = bool(user['is_admin'])
            return redirect(url_for('dashboard'))

        flash("Invalid credentials")

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()

    if session.get('is_admin'):
        users = db.execute("SELECT * FROM users").fetchall()
        db.close()
        return render_template('dashboard.html', users=users)

    db.close()
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ───────────────── EXCEL EXPORT ─────────────────

@app.route('/export')
def export_excel():
    if not os.path.exists(EXCEL_FILE):
        flash("No Excel file found")
        return redirect(url_for('dashboard'))

    return send_file(EXCEL_FILE, as_attachment=True)


# ───────────────── IMPORTANT PART FOR RENDER ─────────────────

init_db()   # ✅ MUST be outside __main__


# ───────────────── RUN FOR LOCAL ONLY ─────────────────

if __name__ == '__main__':
    app.run(debug=True, port=8080)
