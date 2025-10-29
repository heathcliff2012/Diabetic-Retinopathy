from flask import render_template,url_for,flash,redirect,request,current_app
from retinopathy import app,db,bcrypt
from retinopathy.forms import RegistrationForm, LoginForm, UpdateAccountForm, PatientForm
from retinopathy.modules import User, Patient
from flask_login import login_user,current_user,logout_user, login_required
from retinopathy.efficientnet_b3 import model, preprocess_retina_image
from PIL import Image
import os
import secrets

import io
import json
from PIL import Image
from flask import Flask, jsonify, request, render_template

import torch
import torch.nn.functional as F
import timm
import cv2  # Added for your preprocessing
import numpy as np  # Added for your preprocessing
import albumentations as A  # Added for your preprocessing
from albumentations.pytorch import ToTensorV2  # Added for your preprocessing

from retinopathy import db

NUM_CLASSES = 5
MODEL_NAME = "tf_efficientnet_b3"
IMG_SIZE = 300  # Must match your training's target_size

# Create the model using timm
model = timm.create_model(MODEL_NAME, pretrained=False, num_classes=NUM_CLASSES)

# Load the saved model weights
state_dict = torch.load('efficientnet_b3.pth', map_location=torch.device('cpu'))

# Handle 'module.' prefix if it exists (from DataParallel training)
if any(key.startswith('module.') for key in state_dict.keys()):
    from collections import OrderedDict
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = k.replace('module.', '') # remove `module.`
        new_state_dict[name] = v
    model.load_state_dict(new_state_dict)
else:
    model.load_state_dict(state_dict)

# Set model to evaluation mode
model.eval()

# -----------------------------------------------------------------
# --- 3. CUSTOM PREPROCESSING (From your script) ---
# -----------------------------------------------------------------

def preprocess_retina_image(image_bytes, target_size):
    """
    This is your specific pipeline:
    1. Loads an image from bytes.
    2. Finds the main "circle" of the retina to crop out black borders.
    3. Pulls out *only* the green channel.
    4. Enhances the green channel's contrast (CLAHE).
    5. Resizes the 2D image to the model's required size (300x300).
    """
    try:
        # 1. Load image from bytes
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None: return None
        
        # 2. Find retina circle and crop
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cropped_image = image
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            cropped_image = image[y:y+h, x:x+w]

        if cropped_image.size == 0: return None
        
        # 3. Extract green channel
        green_channel = cropped_image[:, :, 1]
        
        # 4. Enhance contrast (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced_green_channel = clahe.apply(green_channel)
        
        # 5. Resize
        resized_image = cv2.resize(enhanced_green_channel, (target_size, target_size), interpolation=cv2.INTER_AREA)
        
        return resized_image
    except Exception as e:
        print(f"Error in preprocess_retina_image: {e}")
        return None

# --- 4. Albumentations Transforms (From your script) ---
# This MUST match the normalization used in your training
eval_transforms = A.Compose([
    A.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ToTensorV2(),
])

# --- 5. Define Your Class Names ---
class_names = ['class_0', 'class_1', 'class_2', 'class_3', 'class_4'] # <-- REPLACE THIS with your 5 classes

# --- 6. Prediction Function ---
def get_prediction(image_bytes):
    """
    Applies the full custom pipeline and returns a prediction.
    """
    try:
        # 1. Apply your custom CV preprocessing (crop, green, clahe, resize)
        image_2d = preprocess_retina_image(image_bytes, IMG_SIZE)
        
        if image_2d is None:
            print("Preprocessing failed, returned None.")
            return None, None

        # 2. Stack 2D grayscale image to 3-channels
        image_3d = np.stack([image_2d] * 3, axis=-1)

        # 3. Apply normalization and ToTensor
        transformed = eval_transforms(image=image_3d)['image']

        # 4. Add batch dimension and send to device (CPU for Flask)
        input_tensor = transformed.unsqueeze(0)
        
        # 5. Get model output
        with torch.no_grad():
            output = model(input_tensor)
            probabilities = torch.nn.functional.softmax(output[0], dim=0)
            
        # 6. Get top class and probability
        top_prob, top_idx = torch.max(probabilities, 0)
        
        predicted_class_name = class_names[top_idx.item()]
        predicted_prob = top_prob.item()

        return predicted_class_name, predicted_prob

    except Exception as e:
        print(f"Error during prediction: {e}")
        return None, None

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
    patients = Patient.query.filter_by(user_id=current_user.id).all()
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


# Make sure you've imported request

@app.route('/analyzeimage', methods=['GET', 'POST'])
@login_required
def analyze_image():
    form = PatientForm()

    # --- START OF TEMPORARY DEBUGGING ---
    if request.method == 'POST':
        print("-----------------------------------------")
        print("FORM HAS BEEN POSTED. CHECKING DATA...")
        
        # Manually run validation
        is_valid = form.validate()
        
        print(f"Was form valid? {is_valid}")
        print(f"FORM ERRORS: {form.errors}")
        print(f"FORM DATA RECEIVED: {request.form}")
        print("-----------------------------------------")
    # --- END OF TEMPORARY DEBUGGING ---
    
    if form.validate_on_submit():
        right_eye_picture_file = save_picture(form.right_eye_image.data)
        left_eye_picture_file = save_picture(form.left_eye_image.data)
        patient = Patient(
            patient_id=form.patient_id.data,
            name=form.name.data,
            age=form.age.data,
            sex=form.sex.data,  # <-- You were missing this!
            user_id=current_user.id,
            RightEye_image_file=right_eye_picture_file,
            LeftEye_image_file=left_eye_picture_file,
            RightEye_diagnosis=form.right_eye_diagnosis.data,
            LeftEye_diagnosis=form.left_eye_diagnosis.data
        )
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
    return render_template('scanpatient.html', title='Analyze Image', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



