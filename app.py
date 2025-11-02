from retinopathy import app
import dotenv
dotenv.load_dotenv('.env')
port = dotenv.get_key('.env', 'PORT') or 5000

if __name__ == '__main__':
    app.run(debug=True)