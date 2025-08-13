# Deadline Tracker

This project is a lightweight deadline and event tracker built with Django and Celery.  It
lets you record upcoming deadlines, assign one or more labels to each event (for example
“Vacancy”, “Project” or “Work”), and schedule multiple reminder notifications in advance
of each due date.  Events can be imported in bulk via a CSV file and grouped by label
within your dashboard.  The initial implementation uses email as the delivery channel
for reminders, but the architecture is designed to allow additional channels such as
Telegram, SMS and web push in the future.

## Features

* Create, edit and delete events with a title, description, due date and time, status
  (open/done/archived) and one or more labels.
* Manage labels independently of events: create new labels, rename or delete existing
  labels and assign a colour for display.
* Schedule multiple reminders per event.  Each reminder stores an absolute send time
  calculated from the due date minus a configurable offset.  Only unsent reminders
  are sent, and every send is logged to avoid duplicates.
* Import events from a CSV file.  The import command accepts a `labels` column which
  automatically creates new labels if they don’t already exist for the user.
* Daily digest emails summarising upcoming events grouped by label.

## Quickstart

This repository does not include dependencies, so you will need to install the
requirements yourself before running the project.  The steps below use virtualenv
and Python 3.11, but any recent version of Python 3 should work.

```bash
# Clone the repository and change into the project directory
cd deadline_tracker

# Create a virtual environment and activate it
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations and create a superuser
python manage.py migrate
python manage.py createsuperuser

# Start a local Redis server (or use a hosted Redis instance)
redis-server &

# In one terminal tab, start the Django development server
python manage.py runserver

# In a second terminal tab, start the Celery worker
celery -A deadlines worker -l info

# In a third terminal tab, start the Celery beat scheduler
celery -A deadlines beat -l info

# Open http://127.0.0.1:8000/admin in your browser and log in with your superuser
# account to manage events, labels and reminders.
```

## Deployment

For production, configure the following environment variables:

| Variable            | Purpose                                                          |
|---------------------|------------------------------------------------------------------|
| `DJANGO_SECRET_KEY` | A long random string used for cryptographic signing              |
| `DATABASE_URL`      | PostgreSQL connection string (e.g. `postgres://…`)               |
| `REDIS_URL`         | Redis connection string (e.g. `redis://localhost:6379/0`)        |
| `EMAIL_BACKEND`     | Fully qualified backend (e.g. `django.core.mail.backends.smtp`)  |
| `EMAIL_HOST`        | SMTP server host                                                 |
| `EMAIL_PORT`        | SMTP server port                                                 |
| `EMAIL_HOST_USER`   | SMTP user name                                                  |
| `EMAIL_HOST_PASSWORD` | SMTP password                                                   |
| `DEFAULT_FROM_EMAIL`| From address used when sending reminders                        |

You will also need to configure at least two processes for Celery (a worker and a beat
scheduler) alongside your web process.  A sample Procfile might look like this:

```
web: gunicorn deadlines.wsgi
worker: celery -A deadlines worker -l info
beat: celery -A deadlines beat -l info
```

## License

This project is provided for demonstration purposes and carries no warranty.  You are
free to modify and adapt it to your own needs.