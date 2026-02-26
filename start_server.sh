#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  MallNav - Start Server with Anthropic API Key
#  Edit the line below with your actual API key
# ─────────────────────────────────────────────────────────────

export ANTHROPIC_API_KEY="sk-ant-api03-YOUR_KEY_HERE"

# Optionally override other settings:
# export SECRET_KEY="your-secret-key"
# export DEBUG="True"

cd "$(dirname "$0")"
echo "Starting MallNav server..."
echo "API Key loaded from environment."
python manage.py runserver 0.0.0.0:8000
