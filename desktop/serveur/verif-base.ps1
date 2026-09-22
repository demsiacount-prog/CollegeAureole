param(
    [string]$Utilisateur,
    [string]$MotDePasse
)

# Pré-vol installateur : vérifie que le rôle fourni peut réellement se
# connecter à la base 'collegeaureole' (PostgreSQL est un prérequis configuré
# AVANT l'installation). Code retour : 0 = OK, non nul = échec (cause émise
# sur la sortie standard afin d'être affichée par l'installeur NSIS).

$ErrorActionPreference = 'Stop'

$pgBase = 'C:\Program Files\PostgreSQL'
$pgDirs = @(Get-ChildItem $pgBase -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending)
if ($pgDirs.Count -eq 0) {
    Write-Output "PostgreSQL introuvable sous $pgBase : installez PostgreSQL puis créez le rôle et la base 'collegeaureole'."
    exit 2
}

$psql = Join-Path $pgDirs[0].FullName 'bin\psql.exe'
if (-not (Test-Path -LiteralPath $psql)) {
    Write-Output "psql introuvable : $psql"
    exit 2
}

# Jamais d'invite de mot de passe (PGCONNECT_TIMEOUT + -w) : ne peut pas bloquer.
$env:PGPASSWORD = $MotDePasse
$env:PGCONNECT_TIMEOUT = '5'

$sortie = & $psql -h 127.0.0.1 -p 5432 -U $Utilisateur -d collegeaureole -w -q -t -c 'SELECT 1' 2>&1
$code = $LASTEXITCODE
if ($code -ne 0) {
    Write-Output "Connexion à la base 'collegeaureole' refusée pour l'utilisateur '$Utilisateur' (code $code) :"
    Write-Output $sortie
} else {
    Write-Output "Connexion à la base 'collegeaureole' : OK."
}
exit $code