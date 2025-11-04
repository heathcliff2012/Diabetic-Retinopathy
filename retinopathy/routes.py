from xmlrpc import client
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
import base64   # ⭐ ADD THIS IMPORT
import io       # ⭐ ADD THIS IMPORT

# from gradio_client import Client, handle_file

# from retinopathy.api import get_prediction





from retinopathy import db

import dotenv
dotenv.load_dotenv()

from gradio_client import Client, handle_file
import base64
import io
from PIL import Image
import os
import secrets
from flask import current_app
import shutil

def get_prediction(img_path):
    client = Client("Godslayer98465/cnn")

    try:
        result = client.predict(
            image_pil=handle_file(img_path),
            api_name="/predict"
        )

        # This assumes 'result' is a tuple: (classification_dict, image_path)
        classification_data = result[0] 
        processed_image_path = result[1]

        confidence = classification_data['confidences'][0]['confidence']
        label = classification_data['label']

        return confidence, label, processed_image_path

    except Exception as e:
        print(f"An error occurred during prediction: {e}")
        # --- THIS IS THE FIX ---
        # Return a 3-item tuple of Nones to prevent the TypeError
        return None, None, None

	
import os
import secrets
from PIL import Image
import shutil  # Import shutil to move files
from flask import current_app # Import Flask's app context

def save_processed_picture(temp_image_path):
    """
    Takes the path to a temporary image, converts it to PNG,
    and saves it to the app's static/processed_images folder.
    
    This is designed to run INSIDE a Flask application.
    """
    if temp_image_path is None:
        return None
        
    try:
        # 1. Open the temporary image file
        img = Image.open(temp_image_path)
        
        # 2. Generate a unique filename (saving as PNG)
        random_hex = secrets.token_hex(8)
        filename = random_hex + '.png'
        
        # 3. Create the full save path USING FLASK'S APP CONTEXT
        save_dir = os.path.join(current_app.root_path, 
                                'static/processed_images')
        save_path = os.path.join(save_dir, filename)
        
        # 4. Make sure the directory exists
        os.makedirs(save_dir, exist_ok=True)
        
        # 5. Save the image as a new PNG file
        # PIL will handle the conversion from .webp (or other) to .png
        img.save(save_path)
        
        return filename
    
    except Exception as e:
        print(f"Error saving processed picture: {e}")
        return None
    
    finally:
        # 6. CRITICAL: Clean up the temporary file
        # This runs whether the try block succeeded or failed.
        if temp_image_path and os.path.exists(temp_image_path):
            try:
                # You can use os.remove() or...
                # ...if it's a whole directory, use shutil.rmtree()
                
                # Let's find the parent temp folder Gradio created
                temp_folder = os.path.dirname(temp_image_path)
                if "gradio" in temp_folder:
                    shutil.rmtree(temp_folder)
                else:
                    os.remove(temp_image_path) # Fallback to just removing the file
                    
            except Exception as e:
                # Log this error, but don't crash the app
                print(f"Warning: Failed to clean up temp file: {e}")

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
        # --- 1. Get uploaded files ---
        right_eye_data = form.right_eye_image.data
        left_eye_data = form.left_eye_image.data

        # --- 2. Save uploaded images to static/Eye_pictures ---
        right_eye_picture_file = save_picture(right_eye_data)
        left_eye_picture_file = save_picture(left_eye_data)

        # --- 3. Build absolute paths for prediction ---
        right_eye_path = os.path.join(app.root_path, 'static/Eye_pictures', right_eye_picture_file)
        left_eye_path = os.path.join(app.root_path, 'static/Eye_pictures', left_eye_picture_file)

        # --- 4. Get model predictions safely ---
        RightEye_diagnosis, RightEye_prediction, right_processed_array = get_prediction(right_eye_path)
        LeftEye_diagnosis, LeftEye_prediction, left_processed_array = get_prediction(left_eye_path)

        # --- 5. Fallback values if model failed ---
        RightEye_diagnosis = RightEye_diagnosis or "Unknown"
        LeftEye_diagnosis = LeftEye_diagnosis or "Unknown"
        RightEye_prediction = RightEye_prediction or 0.0
        LeftEye_prediction = LeftEye_prediction or 0.0

        # --- 6. Save processed images (returned by model) ---
        processed_right_eye_image_file = save_processed_picture(right_processed_array)
        processed_left_eye_image_file = save_processed_picture(left_processed_array)

        # --- 7. Create and save new Patient record ---
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

        # Redirect to patient report
        return redirect(url_for('patient_report', patient_id=patient.patient_id))

    # If GET or invalid form, show page again
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