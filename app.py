from retinopathy import app
import dotenv
dotenv.load_dotenv()

port = dotenv.get_key('.env', 'PORT')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(port), debug=True)