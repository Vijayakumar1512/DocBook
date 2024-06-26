from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, logout_user, LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize the Flask application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'hmsprojects')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql://root:vijay1512@localhost/hms')

db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Define user loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define database models
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    usertype = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(1000))

class Patients(db.Model):
    pid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    name = db.Column(db.String(50))
    gender = db.Column(db.String(50))
    slot = db.Column(db.String(50))
    disease = db.Column(db.String(50))
    time = db.Column(db.String(50), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    dept = db.Column(db.String(50))
    number = db.Column(db.String(50))

class Doctors(db.Model):
    did = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50))
    doctorname = db.Column(db.String(50))
    dept = db.Column(db.String(50))

class Trigr(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    pid = db.Column(db.Integer)
    email = db.Column(db.String(50))
    name = db.Column(db.String(50))
    action = db.Column(db.String(50))
    timestamp = db.Column(db.String(50))

# Define routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/doctors', methods=['POST', 'GET'])
def doctors():
    if request.method == "POST":
        email = request.form.get('email')
        doctorname = request.form.get('doctorname')
        dept = request.form.get('dept')

        doctor = Doctors(email=email, doctorname=doctorname, dept=dept)
        db.session.add(doctor)
        db.session.commit()
        flash("Information is Stored", "primary")

    return render_template('doctor.html')

@app.route('/patients', methods=['POST', 'GET'])
@login_required
def patient():
    doctors = Doctors.query.all()

    if request.method == "POST":
        email = request.form.get('email')
        name = request.form.get('name')
        gender = request.form.get('gender')
        slot = request.form.get('slot')
        disease = request.form.get('disease')
        time = request.form.get('time')
        date = request.form.get('date')
        dept = request.form.get('dept')
        number = request.form.get('number')

        if len(number) != 10:
            flash("Please provide a 10-digit number", "warning")
            return render_template('patient.html', doctors=doctors)

        patient = Patients(email=email, name=name, gender=gender, slot=slot, disease=disease, time=time, date=date, dept=dept, number=number)
        db.session.add(patient)
        db.session.commit()

        flash("Booking Confirmed", "info")

    return render_template('patient.html', doctors=doctors)

@app.route('/bookings')
@login_required
def bookings():
    email = current_user.email
    page = request.args.get('page', 1, type=int)
    if current_user.usertype == "Doctor":
        patients = Patients.query.paginate(page=page, per_page=10)
    else:
        patients = Patients.query.filter_by(email=email).paginate(page=page, per_page=10)
    return render_template('booking.html', query=patients.items, pagination=patients)

@app.route("/edit/<int:pid>", methods=['POST', 'GET'])
@login_required
def edit(pid):
    patient = Patients.query.get_or_404(pid)

    if request.method == "POST":
        patient.email = request.form.get('email')
        patient.name = request.form.get('name')
        patient.gender = request.form.get('gender')
        patient.slot = request.form.get('slot')
        # Ensure disease field is not null
        patient.disease = request.form.get('disease', '')  # Provide default value if not provided
        patient.time = request.form.get('time')
        patient.date = request.form.get('date')
        patient.dept = request.form.get('dept')
        patient.number = request.form.get('number')

        db.session.commit()
        flash("Slot Updated", "success")
        return redirect('/bookings')

    return render_template('edit.html', patient=patient)


@app.route("/delete/<int:pid>", methods=['POST', 'GET'])
@login_required
def delete(pid):
    patient = Patients.query.get_or_404(pid)
    db.session.delete(patient)
    db.session.commit()
    flash("Slot Deleted Successfully", "danger")
    return redirect('/bookings')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form.get('username')
        usertype = request.form.get('usertype')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email Already Exists", "warning")
            return render_template('signup.html')

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, usertype=usertype, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Signup Successful! Please Login", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login Successful", "primary")
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash("Invalid Credentials", "danger")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout Successful", "warning")
    return redirect(url_for('login'))

@app.route('/test')
def test():
    try:
        Test.query.all()
        return 'My database is Connected'
    except Exception as e:
        app.logger.error(f"Database connection failed: {e}")
        return 'My db is not Connected'

@app.route('/details')
@login_required
def details():
    logs = Trigr.query.all()
    return render_template('trigers.html', logs=logs)

@app.route('/search', methods=['POST', 'GET'])
@login_required
def search():
    if request.method == "POST":
        query = request.form.get('search')
        doctor = Doctors.query.filter((Doctors.dept == query) | (Doctors.doctorname == query)).first()

        if doctor:
            flash("Doctor is Available", "info")
        else:
            flash("Doctor is Not Available", "danger")

    return render_template('index.html')

if __name__ == '__main__':
    if not app.debug:
        file_handler = RotatingFileHandler('error.log', maxBytes=10240, backupCount=10)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('DocBook startup')
    app.run(debug=True)
