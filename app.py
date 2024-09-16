# Import dependencies -- reuse code others have given us.
import sqlite3
import os
from markupsafe import escape 
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask("app")
app.secret_key = 'your_secret_key'  # Used for secure session management

# The database configuration
DATABASE = os.environ.get("FLASK_DATABASE", "app.db")

# Functions to help connect to the database and clean up when this application ends.
def get_db_connection():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# Create the users table if it doesn't exist
def create_users_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Create the users table on app startup
create_users_table()

# Home route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/information')
def information():
    return render_template('information.html')

@app.route('/booking')
def booking():
    return render_template('booking.html')

@app.route('/gym_booking')
def gym_booking():
    return render_template('gym_booking.html')

@app.route('/purchase')
def purchase():
    return render_template('purchase.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password_hash = generate_password_hash(password)  # Hash the password

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)', (email, password_hash))
            conn.commit()
            flash('Registration successful, please log in.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('This email is already registered, please use another email.')
        finally:
            conn.close()

    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['email']
            flash('Login successful.')
            return redirect(url_for('home'))
        else:
            flash('Incorrect username or password, please try again.')

    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have successfully logged out.')
    return redirect(url_for('home'))

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.office365.com'  # mail server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'u5523690@live.warwick.ac.uk'  # my email
app.config['MAIL_PASSWORD'] = 'your_password'                # my email password
mail = Mail(app)

@app.route('/send_confirmation', methods=['POST'])
def send_confirmation():
    data = request.get_json()
    user_email = session.get('username')  # Assume user's email is stored in session upon login
    date = data.get('date')

    if user_email:
        msg = Message('Booking Confirmation', sender='u5523690@live.warwick.ac.uk', recipients=[user_email])
        msg.body = f'Your gym booking has been successfully confirmed for the date: {date}.'
        mail.send(msg)
        return jsonify({'message': 'Email sent successfully!'}), 200
    return jsonify({'message': 'Failed to send email.'}), 400

# Initialize cart
def initialize_cart():
    if 'cart' not in session:
        session['cart'] = []

# Add to cart route
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    initialize_cart()
    # Check if the cart already has an item
    if len(session['cart']) >= 1:
        flash('Only one product can be in the cart, please remove the existing product first.')
        return redirect(url_for('cart'))

    product_name = request.form.get('product_name')
    product_price = request.form.get('product_price')
    session['cart'].append({'name': product_name, 'price': product_price})
    session.modified = True  # Mark the session as modified
    flash(f"{product_name} has been added to the cart!")
    return redirect(url_for('cart'))

# Display the cart
@app.route('/cart')
def cart():
    initialize_cart()
    cart_items = session['cart']
    return render_template('cart.html', cart_items=cart_items)

# Display the checkout page
@app.route('/checkout')
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash("Your cart is empty, please add a product first.")
        return redirect(url_for('purchase'))
    return render_template('checkout.html', cart_items=cart_items)

# Clear the cart route
@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    flash("Your cart has been cleared.")
    return redirect(url_for('cart'))

if __name__ == '__main__':
    app.run(debug=True)
