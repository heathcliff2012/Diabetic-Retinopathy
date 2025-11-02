from retinopathy import app
from flask import Flask
import dotenv
dotenv.load_dotenv('.env')
port = dotenv.get_key('.env', 'PORT') or 5000

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)