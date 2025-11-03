try:
    from retinopathy import app
except Exception as e:
    import sys
    print("Failed to import 'app' from 'retinopathy' package:", e, file=sys.stderr)
    raise

import os

debug = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes")


if __name__ == '__main__':
    app.run(host="0.0.0.0:8080" debug=debug)