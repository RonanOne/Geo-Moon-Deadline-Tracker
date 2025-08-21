#!/usr/bin/env bash
set -o errexit

# Install dependencies and prepare Django for production
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input