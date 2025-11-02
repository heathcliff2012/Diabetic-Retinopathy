from flask import Flask
from flask_sqlalchemy import SQLAlchemy 
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
import dotenv
dotenv.load_dotenv('.env')

app = Flask(__name__)

app.config['SECRET_KEY'] = dotenv.get_key('.env', 'SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = dotenv.get_key('.env', 'SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
migrate = Migrate(app, db)

from retinopathy import routes