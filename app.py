from retinopathy import app
import os


port = int(os.environ.get("PORT", 10001))


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=port, debug=True)