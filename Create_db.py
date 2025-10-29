from retinopathy import app, db 
from retinopathy.modules import Patient
from flask_login import current_user
 # Change 'your_app_file' to the name of your .py file

# Make sure to import your User model
from retinopathy.modules import User, Patient 
from retinopathy import app, db

# No current_user here

with app.app_context():
    db.drop_all()
    db.create_all()
    
    # 1. Find the user you want to link the patient to
    # For example, let's find the user with the primary key of 1
    user = User.query.get(1) 

    # if user:
    #     # 2. Create the patient using that user's ID
    #     patient = Patient(
    #         patient_id='P001', 
    #         name='John Doe', 
    #         age=45, 
    #         sex='M',
    #         date_uploaded='2024-01-01', 
    #         RightEye_image_file='default.jpg', 
    #         LeftEye_image_file='default.jpg', 
    #         RightEye_diagnosis='No significant history', 
    #         LeftEye_diagnosis='No significant history', 
    #         user_id=user.id  # <-- Use the ID from the user object
    #     )
    #     db.session.add(patient)
    #     db.session.commit()
    #     print("Database tables created and sample data added.")
    # else:
    #     print("User not found. Could not add patient.")

    # Query for all patients of the user
    if user:
        patients = Patient.query.filter_by(user_id=user.id).all()
        print(f"Found {len(patients)} patients for user {user.id}:")
        print(user.username, user.email)
        for patient in patients:
            print(f"Patient ID: {patient.patient_id}, Name: {patient.name}, Age: {patient.age}")
    else:
        print("User not found. Cannot query patients.")
