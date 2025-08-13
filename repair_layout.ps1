param(
  [string]$Project = "core",
  [string]$App = "deadlines"
)

$ErrorActionPreference = "Stop"

function Ensure-Dir { param([string]$Path) if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null } }
function Ensure-File { param([string]$Path) if (-not (Test-Path $Path)) { New-Item -ItemType File -Path $Path | Out-Null } }
function Replace-InFile {
  param([string]$Path,[string]$Pattern,[string]$Replacement)
  if (Test-Path $Path) {
    (Get-Content $Path -Raw) -replace $Pattern, $Replacement | Set-Content -Encoding UTF8 $Path
  }
}

# Ensure dirs/migrations
Ensure-Dir $Project
Ensure-Dir "$App\migrations"
Ensure-File "$App\migrations\__init__.py"

# Move *project* files from app → project
$projFiles = "settings.py","urls.py","wsgi.py","celery.py"
foreach ($f in $projFiles) {
  if (Test-Path "$App\$f") { Move-Item -Force "$App\$f" "$Project\$f" }
}

# Move *app* files from project → app
$appFiles = "admin.py","models.py","tasks.py"
foreach ($f in $appFiles) {
  if (Test-Path "$Project\$f") { Move-Item -Force "$Project\$f" "$App\$f" }
}

# apps.py (if missing)
if (-not (Test-Path "$App\apps.py")) {
@"
from django.apps import AppConfig
class DeadlinesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "$App"
"@ | Out-File -Encoding utf8 "$App\apps.py"
}

# Point Django to core.settings
Replace-InFile "manage.py" 'DJANGO_SETTINGS_MODULE\s*=\s*["'']deadlines\.settings["'']' 'DJANGO_SETTINGS_MODULE = "core.settings"'
Replace-InFile "$Project\wsgi.py" 'DJANGO_SETTINGS_MODULE\s*=\s*["'']deadlines\.settings["'']' 'DJANGO_SETTINGS_MODULE = "core.settings"'
Replace-InFile "$Project\celery.py" 'os\.environ\.setdefault\(\s*["'']DJANGO_SETTINGS_MODULE["'']\s*,\s*["'']deadlines\.settings["'']\s*\)' 'os.environ.setdefault("DJANGO_SETTINGS_MODULE","core.settings")'

# Ensure INSTALLED_APPS includes deadlines
if (Test-Path "$Project\settings.py") {
  $s = Get-Content "$Project\settings.py" -Raw
  if ($s -notmatch 'deadlines\.apps\.DeadlinesConfig') {
    $s = $s -replace 'INSTALLED_APPS\s*=\s*\[', "INSTALLED_APPS = [`n    'deadlines.apps.DeadlinesConfig',"
    $s | Set-Content -Encoding UTF8 "$Project\settings.py"
  }
}

# Commit & push
git add .
git commit -m "fix: normalize Django layout (core project, deadlines app)" 2>$null
git push
Write-Host "Layout fixed & pushed."
