param(
    [string]$Utilisateur,
    [string]$MotDePasse,
    [int]$PortHttp,
    [string]$EnvPath
)

# Génère (ou régénère) le fichier .env de l'installation mono-poste.
# - Hôte/port/base sont fixés : localhost:5432 / collegeaureole.
# - Identifiants percent-encodés dans DATABASE_URL (robuste face aux
#   caractères spéciaux @ : / % etc.).
# - JWT_SECRET_KEY est conservée si un .env existant en contient une.
# Écriture en UTF-8 sans BOM (lu par python-dotenv au démarrage du backend).

function New-JwtSecret {
    "$([guid]::NewGuid().ToString('N'))$([guid]::NewGuid().ToString('N'))"
}

$existant = $null
if (Test-Path -LiteralPath $EnvPath) {
    foreach ($l in [System.IO.File]::ReadAllLines($EnvPath)) {
        if ($l.StartsWith('JWT_SECRET_KEY=')) {
            $existant = $l.Substring('JWT_SECRET_KEY='.Length)
            break
        }
    }
}
$jwt = if ($existant) { $existant } else { New-JwtSecret }

$userEnc = [Uri]::EscapeDataString($Utilisateur)
$passEnc = [Uri]::EscapeDataString($MotDePasse)
$dbUrl = 'postgresql+psycopg2://' + $userEnc + ':' + $passEnc + '@localhost:5432/collegeaureole'

$contenu = @(
    'ENVIRONMENT=production',
    'AUREOLE_HOST=0.0.0.0',
    "AUREOLE_PORT=$PortHttp",
    "JWT_SECRET_KEY=$jwt",
    'CORS_ORIGINS=http://tauri.localhost,https://tauri.localhost,tauri://localhost,http://localhost',
    "DATABASE_URL=$dbUrl",
    'AUTO_CREATE_TABLES=true',
    'LOG_LEVEL=INFO'
)

[System.IO.File]::WriteAllLines($EnvPath, $contenu, [System.Text.UTF8Encoding]::new($false))
if (-not (Test-Path -LiteralPath $EnvPath)) {
    throw "Impossible d'écrire $EnvPath"
}