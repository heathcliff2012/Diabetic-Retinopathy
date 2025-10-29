from retinopathy import app, db 
from retinopathy.modules import Patient
 # Change 'your_app_file' to the name of your .py file

with app.app_context():
    db.create_all()
    print(Patient.query.all())

print("Database tables created.")


