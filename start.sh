#!/bin/bash
# ===============================================
# start.sh — Launch Flask app with Gunicorn on Railway
# ===============================================

# Exit on any error
set -e

echo "🚀 Starting Flask app on Railway..."

# Ensure dependencies are installed (Railway usually does this automatically)
# pip install -r requirements.txt

# Optional: run database migrations if applicable
# flask db upgrade || true

# Start your Flask app using Gunicorn
# Replace 'retinopathy:app' with your actual module and app variable
gunicorn --workers 4 --threads 2 --bind 0.0.0.0:${PORT:-10001} retinopathy:app

