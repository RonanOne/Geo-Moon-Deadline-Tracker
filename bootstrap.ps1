param(
  [Parameter(Mandatory=$true)]
  [string]$RepoUrl,            # e.g. https://github.com/RonanOne/Geo-Moon-Deadline-Tracker.git
  [string]$Branch = "main",
  [string]$ProjectPkg = "core",
  [string]$AppPkg = "deadlines"
)

$ErrorActionPreference = "Stop"

function Ensure-File {
  param([string]$Path, [string]$Content)
  $dir = Split-Path $Path -Parent
  if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
  if (-not (Test-Path $Path)) { $Content | Out-File -Encoding utf8 $Path }
}

function Ensure-Dir { param([string]$Path) if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null } }

Write-Host "==> Normalizing filenames"
if ((Test-Path ".\manage") -and -not (Test-Path ".\manage.py")) { Rename-Item ".\manage" "manage.py" }
if ((Test-Path ".\requirements") -and -not (Test-Path ".\requirements.txt")) { Rename-Item ".\requirements" "requirements.txt" }
if ((Test-Path ".\README") -and -not (Test-Path ".\README.md")) { Rename-Item ".\README" "README.md" }

Write-Host "==> Project layout checks"
Ensure-Dir $ProjectPkg
Ensure-Dir "$AppPkg\migrations"
Ensure-File "$ProjectPkg\__init__.py" ""
Ensure-File "$AppPkg\__init__.py" ""
Ensure-File "$AppPkg\migrations\__init__.py" ""

# Minimal apps.py if missing
$appsPy = @"
from django.apps import AppConfig
class DeadlinesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "$AppPkg"
"@
if (-not (Test-Path "$AppPkg\apps.py")) { $appsPy | Out-File -Encoding utf8 "$AppPkg\apps.py" }

Write-Host "==> .gitignore"
$gitignore = @"
# Python/Django
__pycache__/
*.py[cod]
*.log
*.sqlite3
.env
*.env
.venv/
env/
local_settings.py

# Static & media
staticfiles/
media/

# Celery
celerybeat-schedule*
"@
Ensure-File ".gitignore" $gitignore

Write-Host "==> .env.example"
$envExample = @"
# Django
DJANGO_SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=.onrender.com,localhost,127.0.0.1

# Email (Brevo example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=94660d001@smtp-brevo.com
EMAIL_HOST_PASSWORD=REPLACE_ME

# Broker for Celery (filled from Render redis in deploy)
REDIS_URL=redis://localhost:6379

# Optional DB (if your settings support it)
# DATABASE_URL=postgres://user:pass@host:5432/dbname
"@
Ensure-File ".env.example" $envExample

Write-Host "==> Render blueprint (render.yaml)"
$renderYaml = @"
services:
  - type: web
    name: django-web
    env: python
    plan: free
    buildCommand: |
      pip install -r requirements.txt
      python manage.py migrate --noinput
      python manage.py collectstatic --noinput
    startCommand: gunicorn $ProjectPkg.wsgi:application --preload --bind 0.0.0.0:8000
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: DJANGO_SECRET_KEY
        sync: false
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: .onrender.com
      - key: EMAIL_BACKEND
        sync: false
      - key: EMAIL_HOST
        sync: false
      - key: EMAIL_PORT
        sync: false
      - key: EMAIL_USE_TLS
        sync: false
      - key: EMAIL_HOST_USER
        sync: false
      - key: EMAIL_HOST_PASSWORD
        sync: false
      - key: REDIS_URL
        fromService:
          type: redis
          name: redis
          property: connectionString

  - type: worker
    name: celery-worker
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A $ProjectPkg worker -l info
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: DJANGO_SECRET_KEY
        sync: false
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: .onrender.com
      - key: REDIS_URL
        fromService:
          type: redis
          name: redis
          property: connectionString

  - type: worker
    name: celery-beat
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A $ProjectPkg beat -l info --pidfile /opt/beat/beat.pid --schedule /opt/beat/celerybeat-schedule
    disk:
      name: beat-disk
      mountPath: /opt/beat
      sizeGB: 1
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: DJANGO_SECRET_KEY
        sync: false
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: .onrender.com
      - key: REDIS_URL
        fromService:
          type: redis
          name: redis
          property: connectionString

  - type: redis
    name: redis
    ipAllowList: []
"@
Ensure-File "render.yaml" $renderYaml

Write-Host "==> Git init/commit/push"
if (-not (Test-Path ".git")) { git init | Out-Null }
git add .
if ((git status --porcelain) -ne $null) {
  git commit -m "chore: normalize structure, add render blueprint & env example"
}
git branch -M $Branch
$hasRemote = (git remote) -match "^origin$"
if ($hasRemote) { git remote remove origin }
git remote add origin $RepoUrl
git push -u origin $Branch

Write-Host "==> GitHub Action to trigger Render deploy on each push"
Ensure-Dir ".github\workflows"
$gha = @'
name: Deploy to Render
on:
  push:
    branches: [$Branch]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Render deploy
        env:
          RENDER_SERVICE_ID: ${{ secrets.RENDER_SERVICE_ID }}
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -s -X POST "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys" \
            -H "Authorization: Bearer $RENDER_API_KEY" \
            -H "Content-Type: application/json" \
            -d '{}'
'@
$gha | Out-File -Encoding utf8 ".github\workflows\deploy-render.yml"

git add .github/workflows/deploy-render.yml
git commit -m "ci: trigger Render deploy on push" | Out-Null 2>&1
git push

Write-Host ""
Write-Host "All set."
Write-Host "Next:"
Write-Host "  1) In GitHub → Settings → Secrets and variables → Actions, add:"
Write-Host "     - RENDER_API_KEY       (from Render dashboard)"
Write-Host "     - RENDER_SERVICE_ID    (from your Render web service URL)"
Write-Host "  2) In Render: New → Blueprint → select this repo (render.yaml)."
Write-Host "     Set DJANGO_SECRET_KEY and email vars when prompted."
