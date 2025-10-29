from flask import render_template,url_for,flash,redirect,request,current_app
from retinopathy import app,db,bcrypt
from retinopathy.forms import RegistrationForm, LoginForm, UpdateAccountForm, PatientForm
from retinopathy.modules import User, Patient
from flask_login import login_user,current_user,logout_user, login_required
from retinopathy.efficientnet_b3 import model, preprocess_retina_image
from PIL import Image
import os
import secrets

patients = [
    {
        'id': 1,
        'name': 'John Doe',
        'age': 45,
        'sex': 'Male',
        'date': '11-11-11'
    },
    {
        'id': 2,
        'name': 'Jane Smith',
        'age': 50,
        'sex': 'Female',
        'date': '12-12-12'
    }
]       


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember = form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/patienthistory')
@login_required
def patient_history():
    #patients = Patient.query.filter_by(user_id=current_user.id).all()
    return render_template('patienthistory.html', patients=patients)

@app.route('/patient-report/<int:patient_id>')
@login_required
def patient_report(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patientreport.html', patient=patient)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/Eye_pictures', picture_fn)
    i = Image.open(form_picture)
    i.save(picture_path)
    return picture_fn


@app.route('/analyzeimage', methods=['GET', 'POST'])
@login_required
def analyze_image():
    form = PatientForm()
    if form.validate_on_submit():
        # --- 1. SAVE THE IMAGE FILES FIRST ---
        if form.right_eye_image.data:
            right_image_filename = save_picture(form.right_eye_image.data)
        else:
            right_image_filename = 'default.jpg' # Or handle as required
            
        if form.left_eye_image.data:
            left_image_filename = save_picture(form.left_eye_image.data)
        else:
            left_image_filename = 'default.jpg' # Or handle as required

        # --- 2. CREATE PATIENT WITH THE *FILENAMES* ---
        patient = Patient(
            patient_id=form.patient_id.data,
            name=form.name.data,
            age=form.age.data,
            sex=form.sex.data,
            right_eye_file=right_image_filename,
            left_eye_file=left_image_filename
        )
        flash("Patient data Created", "Success")
        patient = Patient(
            patient_id=form.patient_id.data,
            name=form.name.data,
            age=form.age.data,
            sex=form.sex.data,
            right_eye_file=right_image_filename,
            left_eye_file=left_image_filename
        )

        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('home', patient_id=patient.id))
    return render_template('scanpatient.html',form=form, title='Scan Patient')


    # --- 4. RENDER TEMPLATE on GET request or if form is INVALID ---
    # This 'return' is now *outside* the 'if' block.
    return render_template('scanpatient.html',form=form, title='Scan Patient')
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html', title='About')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



