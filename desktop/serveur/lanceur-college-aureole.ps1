param()

# Lanceur lance par le raccourci « College Aureole » :
#   1. demarre PostgreSQL (service, mode Manuel)
#   2. demarre le service « College Aureole - Serveur » (mode Manuel)
#   3. attend que /api/health reponde (<= 20 s)
#   4. lance le client Tauri
# Erreurs affichees dans une boite de dialogue (fenetre PowerShell masquee).

$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

function AfficherErreur([string]$message) {
  try {
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    [void][System.Windows.Forms.MessageBox]::Show(
      $message,
      'College Aureole',
      'OK',
      [System.Windows.Forms.MessageBoxIcon]::Error)
  } catch {
    Write-Output $message
  }
}

# ── 1) PostgreSQL ──────────────────────────────────────────────────────────────
$pg = Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue |
  Sort-Object Name -Descending | Select-Object -First 1
if (-not $pg) {
  AfficherErreur "Service PostgreSQL introuvable.`n`nInstallez PostgreSQL puis creez la base 'collegeaureole'."
  exit 1
}
if ($pg.Status -ne 'Running') {
  try {
    Start-Service -Name $pg.Name -ErrorAction Stop
  } catch {
    AfficherErreur "Impossible de demarrer PostgreSQL ($($pg.Name)).`n`n$($_.Exception.Message)`n`nEffectuez un clic droit sur le raccourci puis 'Exécuter en tant qu'administrateur'."
    exit 1
  }
}

# ── 2) Service serveur ─────────────────────────────────────────────────────────
$svc = Get-Service -Name 'CollegeAureoleServeur' -ErrorAction SilentlyContinue
if (-not $svc) {
  AfficherErreur "Le service 'College Aureole - Serveur' est introuvable.`n`nReinstallez l'application."
  exit 1
}
if ($svc.Status -ne 'Running') {
  try {
    Start-Service -Name $svc.Name -ErrorAction Stop
  } catch {
    AfficherErreur "Impossible de demarrer le serveur.`n`n$($_.Exception.Message)`n`nEffectuez un clic droit sur le raccourci puis 'Exécuter en tant qu'administrateur'."
    exit 1
  }
}

# ── 3) Attend /api/health pour que le client n'arrive pas sur le boot ──────
$port = '8000'
$envPath = Join-Path $dir '.env'
if (Test-Path -LiteralPath $envPath) {
  foreach ($ligne in [System.IO.File]::ReadAllLines($envPath)) {
    if ($ligne -like 'AUREOLE_PORT=*') { $port = $ligne.Substring('AUREOLE_PORT='.Length); break }
  }
}

$ok = $false
for ($i = 0; $i -lt 20; $i++) {
  try {
    $r = Invoke-WebRequest -Uri "http://localhost:$port/api/health" -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { $ok = $true; break }
  } catch { }
  Start-Sleep -Milliseconds 1000
}
if (-not $ok) {
  AfficherErreur "Le serveur ne repond pas encore sur le port $port.`n`nConsultez le journal :`n$dir\college-aureole-service.out.log`n`nOu relancez le double-clic dans quelques secondes."
  exit 1
}

# ── 4) Client ──────────────────────────────────────────────────────────────────
$client = Join-Path $dir 'client\College Aureole.exe'
if (-not (Test-Path -LiteralPath $client)) {
  AfficherErreur "Client introuvable : $client"
  exit 1
}
Start-Process -FilePath $client
exit 0