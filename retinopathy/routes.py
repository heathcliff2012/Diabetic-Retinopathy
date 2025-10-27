from flask import render_template,url_for,flash,redirect,request
from retinopathy import app,db,bcrypt
from retinopathy.forms import RegistrationForm, LoginForm, UpdateAccountForm
from retinopathy.modules import User, Patient
from flask_login import login_user,current_user,logout_user, login_required
from retinopathy.efficientnet_b3 import model, preprocess_retina_image

patient_image = { 
    'date' : '2024-06-01',
    'image' : 'retinopathy/static/images/sample_retina.jpg',
    'name' : 'John Doe',
    'age'  : 45,
    'diagnosis' : 'Mild Non-Proliferative Diabetic Retinopathy',
    'mobile number': 9999999999
}

@app.route('/')
@app.route('/home')
def home():
    return render_template('try.html')


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



@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



