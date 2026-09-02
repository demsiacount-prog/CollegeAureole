param(
    [string]$XmlPath,
    [string]$Dep
)

# Lit le XML du service (déjà copié par l'installeur) en UTF-8.
$content = [System.IO.File]::ReadAllText($XmlPath, [System.Text.Encoding]::UTF8)

# Injecte la dépendance PostgreSQL (<depend>) juste après <delayedautostart>,
# uniquement si un service PG a été détecté et qu'aucun <depend> n'existe déjà.
if ($Dep -ne '' -and $content -notmatch '<depend>') {
    $content = $content -replace '</delayedautostart>', "</delayedautostart>`r`n  <depend>$Dep</depend>"
}

# Réécrit le XML en UTF-8 sans BOM (requis par WinSW).
[System.IO.File]::WriteAllText($XmlPath, $content, [System.Text.UTF8Encoding]::new($false))
