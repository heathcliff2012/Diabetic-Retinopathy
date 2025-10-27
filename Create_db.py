from retinopathy import app, db  # Change 'your_app_file' to the name of your .py file

with app.app_context():
    db.create_all()

print("Database tables created.")

