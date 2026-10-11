#!/bin/bash
echo "Starting Rudra Bot (Developed by Ravi King)..."
gunicorn bot:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 120
