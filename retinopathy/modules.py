from retinopathy import db,login_manager
from flask_login import UserMixin
from datetime import datetime
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)
    patients = db.relationship('Patient', backref = 'doctor', lazy = True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Patient(db.Model):
    patient_id = db.Column(db.String(20), unique = True, nullable = False, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    age = db.Column(db.Integer, nullable = False)
    sex = db.Column(db.String(10), nullable = False)
    RightEye_image_file = db.Column(db.String(100), nullable = False, default = 'default.jpg')
    LeftEye_image_file = db.Column(db.String(100), nullable = False, default = 'default.jpg')
    RightEye_diagnosis = db.Column(db.String(200), nullable = False)
    LeftEye_diagnosis = db.Column(db.String(200), nullable = False)
    date_uploaded = db.Column(db.DateTime, nullable = False, default = datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    processed_RightEye_image_file = db.Column(db.String(100), nullable = True)
    processed_LeftEye_image_file = db.Column(db.String(100), nullable = True)
    RightEye_prediction = db.Column(db.Integer, nullable = True)
    LeftEye_prediction = db.Column(db.Integer, nullable = True)

    def __repr__(self):
        return f"Patient('{self.name}', '{self.age}', '{self.RightEye_image_file}', '{self.LeftEye_image_file}', '{self.RightEye_diagnosis}', '{self.LeftEye_diagnosis}', '{self.date_uploaded}')"