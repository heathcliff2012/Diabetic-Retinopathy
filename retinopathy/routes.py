from flask import render_template,url_for,flash,redirect,request,current_app,abort
from retinopathy import app,db,bcrypt
from retinopathy.forms import RegistrationForm, LoginForm, UpdateAccountForm, PatientForm
from retinopathy.modules import User, Patient
from flask_login import login_user,current_user,logout_user, login_required
from retinopathy.efficientnet_b3 import model, preprocess_retina_image
from PIL import Image
import os
import secrets
from PIL import Image
from flask import Flask, jsonify, request, render_template

import requests # Make sure this is imported
import base64   # ⭐️ ADD THIS IMPORT
import io       # ⭐️ ADD THIS IMPORT

from retinopathy import db

import dotenv
dotenv.load_dotenv()

HF_API_URL = dotenv.get_key('.env','HF_API_URL')

HF_API_KEY = dotenv.get_key('.env','HF_API_KEY')

AUTH_HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}"
}

def get_prediction(image_bytes):
    """
    Calls your private Hugging Face API to get a prediction.
    Returns: (diagnosis, probability, processed_image_base64_string)
    """
    try:
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{base64_image}" 

        response = requests.post(
            HF_API_URL, 
            json={ "data": [ image_data_url ] }
        )

        if not response.ok:
            print(f"API Error: {response.text}")
            return None, None, None # Return 3 Nones

        result = response.json()
        
        # --- THIS IS THE CHANGE ---
        # The API now returns two items in the 'data' array
        prediction_data = result['data'][0]
        image_data_url = result['data'][1] # ⭐️ This is the new image string
        
        predicted_class_name = prediction_data['label']
        predicted_prob = prediction_data['confidences'][0]['confidence']

        # Return all 3 items
        return predicted_class_name, predicted_prob, image_data_url

    except Exception as e:
        print(f"Error calling prediction API: {e}")
        return None, None, None # Return 3 Nones
    
def save_processed_picture(base64_data_url):
    """
    Saves a Base64 data URL string as an image file.
    Returns the filename.
    """
    if base64_data_url is None:
        return None
        
    try:
        # 1. Split the data URL "data:image/png;base64,iVBORw..."
        header, encoded = base64_data_url.split(",", 1)
        
        # 2. Decode the Base64 string
        image_data = base64.b64decode(encoded)
        
        # 3. Create a PIL Image from the bytes
        img = Image.open(io.BytesIO(image_data))
        
        # 4. Generate a unique filename (we'll save as PNG)
        random_hex = secrets.token_hex(8)
        filename = random_hex + '.png' # Save as PNG
        
        # 5. Create the full save path
        save_path = os.path.join(current_app.root_path, 
                                 'static/processed_images', 
                                 filename)
        
        # 6. Save the image
        img.save(save_path)
        
        return filename
    
    except Exception as e:
        print(f"Error saving processed picture: {e}")
        return None

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

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
    patients = Patient.query.filter_by(user_id=current_user.id).all()
    return render_template('patienthistory.html', patients=patients)

@app.route('/patient-report/<patient_id>')
@login_required
def patient_report(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    return render_template('patientreport.html', patient=patient, patient_id=patient_id)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/Eye_pictures', picture_fn)
    i = Image.open(form_picture)
    i.save(picture_path)
    return picture_fn


# Make sure you've imported request

@app.route('/analyzeimage', methods=['GET', 'POST'])
@login_required
def analyze_image():
    form = PatientForm()
    
    if form.validate_on_submit():
        
        # --- 1. Get the FileStorage objects ---
        right_eye_data = form.right_eye_image.data
        left_eye_data = form.left_eye_image.data

        # --- 2. Read the bytes for prediction ---
        # This is the first read
        right_eye_bytes = right_eye_data.read()
        left_eye_bytes = left_eye_data.read()

        # --- 3. REWIND the stream ---
        # This allows other functions (like save_picture) to read it again
        right_eye_data.seek(0)
        left_eye_data.seek(0)

        # --- 4. Save original images ---
        # This second read will now work
        right_eye_picture_file = save_picture(right_eye_data)
        left_eye_picture_file = save_picture(left_eye_data)
        
        # --- 5. Get predictions using the bytes from step 2 ---
        RightEye_diagnosis, RightEye_prediction, right_processed_array = get_prediction(right_eye_bytes)
        LeftEye_diagnosis, LeftEye_prediction, left_processed_array = get_prediction(left_eye_bytes)

        # --- 6. Save the processed images ---
        processed_right_eye_image_file = save_processed_picture(right_processed_array)
        processed_left_eye_image_file = save_processed_picture(left_processed_array)

        # --- 7. Create Patient ---
        patient = Patient(
            patient_id=form.patient_id.data,
            name=form.name.data,
            age=form.age.data,
            sex=form.sex.data, 
            user_id=current_user.id,
            
            RightEye_image_file=right_eye_picture_file,
            LeftEye_image_file=left_eye_picture_file,
            
            processed_RightEye_image_file=processed_right_eye_image_file,
            processed_LeftEye_image_file=processed_left_eye_image_file,
            
            RightEye_diagnosis=RightEye_diagnosis,
            LeftEye_diagnosis=LeftEye_diagnosis,
            RightEye_prediction=RightEye_prediction,
            LeftEye_prediction=LeftEye_prediction
        )
        
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        # Redirect to the patient's report page after success
        return redirect(url_for('patient_report', patient_id=patient.patient_id))

    return render_template('scanpatient.html', title='Analyze Image', form=form)

@app.route('/patient-report/<patient_id>/delete', methods=['POST'])
@login_required
def delete_post(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    db.session.delete(patient)
    db.session.commit()
    flash('Post Deleted!', 'success')
    return redirect(url_for('patient_history', patient_id=patient.patient_id,patient = patient))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



