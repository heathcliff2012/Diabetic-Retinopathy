#!/bin/bash
set -e

# Start the Flask app with Gunicorn
gunicorn --bind 0.0.0.0:${PORT:-10001} retinopathy:app
