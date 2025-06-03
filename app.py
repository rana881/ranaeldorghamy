from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask import session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from model.deployment import predict
from database import db, Attack, User  # We'll need to create User model

app = Flask(__name__)
app.secret_key = 'QWERTYUI'  # <-- Add this line

# Configure database (Using SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///xss_attacks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with Flask app
db.init_app(app)

# Create database tables (only needed once)
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login-page', methods=['GET'])
def login_page():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Check if user exists and password is correct
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session['user_id'] = user.id
        session['user_email'] = user.email
        return jsonify({'message': 'Welcome to the app'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/signup-page', methods=['GET'])
def signup_page():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    # Basic validation
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    elif User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    else:
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'Account created successfully! redirection to login page.'}), 200

@app.route('/profile')
def profile_page():
    # Get current user from database
    user = User.query.get(session['user_id'])
    
    return render_template('profile.html',
                         current_user=user)
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('query')
    results = predict(search_query)

    new_result = Attack(text=search_query, text_result=results['prediction'])
    db.session.add(new_result)
    db.session.commit()

    # untill the secuirty model is added
    return jsonify({'results': results['prediction']})

@app.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.get_json()

    results = {}
    
    for key, value in data.items():
        sentiment = predict(value)
        results[key] = sentiment['prediction']

        new_result = Attack(text=value, text_result=sentiment['prediction'])
        db.session.add(new_result)

    db.session.commit()

    # untill the secuirty model is added
    return jsonify({'results': results})


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)