; ─────────────────────────────────────────────────────────────────────────────
; Installeur NSIS TOUT-EN-UN College Aureole (mono-poste) : serveur + client.
;
; Attend un répertoire `paquetage/` à côté de ce script contenant :
;   paquetage\college-aureole-serveur\…     (sortie PyInstaller, onedir)
;   paquetage\college-aureole-service.exe   (wrapper WinSW x64 renommé)
;   paquetage\college-aureole-serveur.xml   (définition du service)
;   paquetage\college-aureole-client.exe    (exécutable portable du client Tauri)
;
; Build :  makensis tout-en-un.nsi
;
; Flow :
;   1. Bienvenue
;   2. Page HTTP (port, défaut 8000)
;   3. Page PostgreSQL (utilisateur + mot de passe)
;   4. Dossier d'installation
;   5. Installation (fichiers, .env, pare-feu, service, dépendance PG)
;   6. Client : copie de l'exécutable portable + raccourci Bureau/Menu
;   7. Vérification finale (healthcheck HTTP + adresse)
;   8. Fin
; ─────────────────────────────────────────────────────────────────────────────

Unicode true
RequestExecutionLevel admin

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "WordFunc.nsh"

Name "College Aureole"
OutFile "..\..\dist\college-aureole-setup.exe"
InstallDir "$PROGRAMFILES64\CollegeAureole"
InstallDirRegKey HKLM "Software\CollegeAureole" "InstallDir"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"

!insertmacro MUI_PAGE_WELCOME
Page custom PageHttp PageHttpLeave
Page custom PagePg PagePgLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
Page custom PageResult PageResultLeave
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "French"

; ── Variables de configuration ──
Var PortApi        ; port HTTP du backend
Var PgUtilisateur  ; rôle PostgreSQL
Var PgMotDePasse   ; mot de passe PostgreSQL
Var IniFichier     ; chemin du formulaire InstallOptions
Var ServicePGEtab  ; nom du service PostgreSQL détecté ("" si introuvable)
Var HealthOK       ; "1" si le healthcheck a réussi
Var ServeurIP      ; adresse affichée dans le message final

; ============================================================
; PAGE 1 : Interface HTTP
; ============================================================
Function PageHttp
  InitPluginsDir
  StrCpy $IniFichier "$PLUGINSDIR\http.ini"
  File /oname=$IniFichier "http.ini"
  StrCpy $0 ""
  ReadINIStr $0 "$IniFichier" "Field 3" "State"
  ${If} $0 == ""
    WriteINIStr "$IniFichier" "Field 3" "State" "8000"
  ${EndIf}
  InstallOptions::dialog "$IniFichier"
  Pop $0
FunctionEnd

Function PageHttpLeave
  ReadINIStr $PortApi "$IniFichier" "Field 3" "State"

  ; Validation : obligatoire + entier dans une plage raisonnable
  ${If} $PortApi == ""
    MessageBox MB_ICONEXCLAMATION "Le port HTTP est obligatoire."
    Abort
  ${EndIf}
  ; Vérifie que c'est un nombre
  ClearErrors
  IntOp $0 $PortApi + 0
  IfErrors 0 +3
    MessageBox MB_ICONEXCLAMATION "Le port HTTP doit être un nombre."
    Abort
  ${If} $PortApi < 1024
    MessageBox MB_ICONEXCLAMATION "Le port HTTP doit être supérieur ou égal à 1024."
    Abort
  ${EndIf}
  ${If} $PortApi > 65535
    MessageBox MB_ICONEXCLAMATION "Le port HTTP doit être inférieur ou égal à 65535."
    Abort
  ${EndIf}
FunctionEnd

; ============================================================
; PAGE 2 : Base de données PostgreSQL
; ============================================================
Function PagePg
  StrCpy $IniFichier "$PLUGINSDIR\pg.ini"
  File /oname=$IniFichier "pg.ini"
  StrCpy $0 ""
  ReadINIStr $0 "$IniFichier" "Field 4" "State"
  ${If} $0 == ""
    WriteINIStr "$IniFichier" "Field 4" "State" "collegeaureole"
  ${EndIf}
  InstallOptions::dialog "$IniFichier"
  Pop $0
FunctionEnd

Function PagePgLeave
  ReadINIStr $PgUtilisateur "$IniFichier" "Field 4" "State"
  ReadINIStr $PgMotDePasse  "$IniFichier" "Field 6" "State"

  ${If} $PgUtilisateur == ""
    MessageBox MB_ICONEXCLAMATION "L'utilisateur de la base est obligatoire."
    Abort
  ${EndIf}
FunctionEnd

; ============================================================
; PAGE RESULTAT : confirmation + adresse
; ============================================================
Function PageResult
  ; Résolution de l'adresse affichée avant toute lecture dans PageResultLeave.
  Call DetecterIP
FunctionEnd

Function PageResultLeave
  ${If} $HealthOK == "1"
    MessageBox MB_ICONINFORMATION "✔ Serveur démarré avec succès.$\n$\nAdresse : http://$ServeurIP:$PortApi$\nContrôle : http://$ServeurIP:$PortApi/api/health"
  ${EndIf}
FunctionEnd

; ============================================================
; INSTALLATION
; ============================================================
Section "Serveur" SectionServeur
  SetOutPath "$INSTDIR"

  ; Arrêt propre d'une installation existante avant mise à jour des fichiers.
  ; On différencie first install (exe absent : le stop échoue = normal)
  ; d'une mise à jour (exe présent : le stop doit réussir).
  ${If} ${FileExists} "$INSTDIR\college-aureole-service.exe"
    nsExec::ExecToStack '"$INSTDIR\college-aureole-service.exe" stop'
    Pop $0
    Pop $1 ; ignore la sortie
    ${If} $0 != 0
      DetailPrint "AVERTISSEMENT : arrêt du service existant a échoué (code $0)."
    ${EndIf}
  ${EndIf}

  ; Fichiers applicatifs (PyInstaller onedir : binaire + _internal)
  File /r "paquetage\college-aureole-serveur\*.*"
  File "paquetage\college-aureole-service.exe"
  File "paquetage\college-aureole-serveur.xml"

  ; WinSW exige que le fichier de configuration XML porte EXACTEMENT le même
  ; nom de base que l'exécutable du service (college-aureole-service.exe →
  ; college-aureole-service.xml). Le fichier livré s'appelle
  ; college-aureole-serveur.xml : on le renomme.
  Delete "$INSTDIR\college-aureole-service.xml"
  Rename "$INSTDIR\college-aureole-serveur.xml" "$INSTDIR\college-aureole-service.xml"
  ${IfNot} ${FileExists} "$INSTDIR\college-aureole-service.xml"
    MessageBox MB_ICONSTOP "Échec du renommage de la configuration du service.$\nInstallation interrompue."
    Abort
  ${EndIf}

  ; Dossier des fichiers téléversés (logos) — préservé lors des mises à jour
  CreateDirectory "$INSTDIR\uploads"

  ; Mise à jour de la dépendance de service PostgreSQL dans le XML
  Call InjecterDependancePG

  ; Fichier .env généré (conservé lors des mises à jour)
  ${IfNot} ${FileExists} "$INSTDIR\.env"
    Call GenererEnv
  ${ElseIfNot} ${Silent}
    DetailPrint ".env existant conservé (configuration inchangée)."
  ${EndIf}

  ; Règle de pare-feu entrante pour le port HTTP (non bloquant si échec)
  nsExec::ExecToStack 'netsh advfirewall firewall delete rule name="College Aureole Serveur"'
  Pop $0
  nsExec::ExecToStack 'netsh advfirewall firewall add rule name="College Aureole Serveur" dir=in action=allow protocol=TCP localport=$PortApi'
  Pop $0
  Pop $1
  ${If} $0 != 0
    DetailPrint "AVERTISSEMENT : création de la règle de pare-feu a échoué (code $0)."
  ${EndIf}

  ; Enregistrement du service Windows + vérification réelle
  nsExec::ExecToStack '"$INSTDIR\college-aureole-service.exe" install'
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "L'enregistrement du service Windows a échoué (code $0).$\nInstallation interrompue. Consultez les détails ci-dessus."
    Abort
  ${EndIf}

  ; --- Démarrage + healthcheck réel ---
  Call DemarrerEtVerifier

  WriteUninstaller "$INSTDIR\desinstallation.exe"
  WriteRegStr HKLM "Software\CollegeAureole" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CollegeAureoleServeur" \
                   "DisplayName" "College Aureole - Serveur"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CollegeAureoleServeur" \
                   "UninstallString" '"$INSTDIR\desinstallation.exe"'
SectionEnd

; ------------------------------------------------------------
; CLIENT : copie de l'exécutable portable Tauri + raccourcis.
; ------------------------------------------------------------
Section "Client" SectionClient
  SetOutPath "$INSTDIR\client"

  ; Exécutable portable du client Tauri (obligatoire pour l'installeur
  ; tout-en-un). Copié tel quel puis renommé sous son nom d'application :
  ; /oname= avec un nom contenant des espaces n'est pas fiable en NSIS.
  File "paquetage\college-aureole-client.exe"
  Rename "$INSTDIR\client\college-aureole-client.exe" "$INSTDIR\client\College Aureole.exe"
  ${IfNot} ${FileExists} "$INSTDIR\client\College Aureole.exe"
    MessageBox MB_ICONSTOP "Échec de l'installation du client.$\nInstallation interrompue."
    Abort
  ${EndIf}

  ; Raccourci Bureau + Menu Démarrer
  CreateDirectory "$SMPROGRAMS\College Aureole"
  CreateShortcut "$DESKTOP\College Aureole.lnk" "$INSTDIR\client\College Aureole.exe"
  CreateShortcut "$SMPROGRAMS\College Aureole\College Aureole.lnk" "$INSTDIR\client\College Aureole.exe"
SectionEnd

; ------------------------------------------------------------
; Détecte le service PostgreSQL et régénère le XML complet du service
; avec une dépendance <depend> (WinSW) le cas échéant.
; ------------------------------------------------------------
Function InjecterDependancePG
  StrCpy $ServicePGEtab ""

  ; Nom du service réel (variable : postgresql-x64-16, -17, ...). PowerShell
  ; est plus fiable pour lister les services et extraire le premier "postgres".
  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command "(Get-Service | Where-Object {$_.Name -match ''postgres''} | Select-Object -First 1).Name"'
  Pop $0
  Pop $1
  ${If} $0 == 0
    StrCpy $ServicePGEtab "$1"
  ${EndIf}

  ; Régénère entièrement le XML pour placer <depend> à l'intérieur de <service>.
  ; ⚠️ On passe par PowerShell + [System.IO.File]::WriteAllText avec un encodage
  ; UTF-8 explicite : NSIS FileWrite écrit en ANSI, ce qui corrompait les
  ; caractères accentués de la ligne 1 et faisait échouer le chargement du XML
  ; par WinSW (« ligne 1 position 49 »). Le here-string PowerShell conserve ici
  ; l'encodage correct.
  ${If} ${FileExists} "$INSTDIR\college-aureole-service.xml"
    ; Le script PowerShell est écrit dans un fichier .ps1 temporaire pour
    ; éviter les soucis d'échappement des guillemets et accents dans ExecToStack.
    FileOpen $4 "$PLUGINSDIR\genxml.ps1" w
    FileWrite $4 "$\$Env:dep = '$ServicePGEtab'$\r$\n"
    FileWrite $4 "$\$xml = '<?xml version=""1.0"" encoding=""UTF-8""?>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '<service>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <id>CollegeAureoleServeur</id>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <name>College Aureole - Serveur</name>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <description>Serveur applicatif FastAPI de l''application de gestion scolaire College Aureole.</description>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <executable>%BASE%\college-aureole-serveur.exe</executable>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <workingdirectory>%BASE%</workingdirectory>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <startmode>Automatic</startmode>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <delayedAutoStart>true</delayedAutoStart>' + [char]10$\r$\n"
    ${If} $ServicePGEtab != ""
      FileWrite $4 "$\$xml += '  <depend>' + $\$Env:dep + '</depend>' + [char]10$\r$\n"
    ${EndIf}
    FileWrite $4 "$\$xml += '  <onfailure action=""restart"" delay=""10 sec""/>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <onfailure action=""restart"" delay=""60 sec""/>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <resetfailure>1 hour</resetfailure>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <env name=""AUREOLE_UPLOADS_DIR"" value=""%BASE%\uploads""/>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <env name=""ENVIRONMENT"" value=""production""/>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  <log mode=""roll-by-size"">' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '    <sizeThreshold>10240</sizeThreshold>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '    <keepFiles>3</keepFiles>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '  </log>' + [char]10$\r$\n"
    FileWrite $4 "$\$xml += '</service>'" + [char]10 + [char]10
    FileWrite $4 "[System.IO.File]::WriteAllText('$INSTDIR\college-aureole-service.xml', $\$xml, [System.Text.UTF8Encoding]::new($\$false))$\r$\n"
    FileClose $4
    nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\genxml.ps1"'
    Pop $0
    Pop $1
    ${If} $0 != 0
      DetailPrint "AVERTISSEMENT : réécriture du XML via PowerShell a échoué (code $0)."
    ${EndIf}

    ${If} $ServicePGEtab != ""
      DetailPrint "Dépendance de service ajoutée : $ServicePGEtab"
    ${Else}
      DetailPrint "AVERTISSEMENT : service PostgreSQL non détecté. Le backend attendra"
      DetailPrint "la base au démarrage (redémarrage automatique via WinSW)."
    ${EndIf}
  ${Else}
    DetailPrint "AVERTISSEMENT : XML du service introuvable après l'installation."
  ${EndIf}
FunctionEnd

; ------------------------------------------------------------
; Démarre le service puis effectue un healthcheck HTTP réel
; ------------------------------------------------------------
Function DemarrerEtVerifier
  StrCpy $HealthOK "0"

  nsExec::ExecToStack '"$INSTDIR\college-aureole-service.exe" start'
  Pop $0
  Pop $1
  ${If} $0 != 0
    DetailPrint "AVERTISSEMENT : démarrage du service a renvoyé un code $0."
    DetailPrint "Vérification malgré tout du port HTTP..."
  ${EndIf}

  ; Boucle : 10 tentatives espacées de 2 s (max ~20 s pour le boot du backend)
  StrCpy $R0 "0"
loop_health:
  IntOp $R0 $R0 + 1
  StrCpy $R1 ""
  nsExec::ExecToStack '"$SYSDIR\curl.exe" -s -o NUL -w "%{http_code}" http://localhost:$PortApi/api/health'
  Pop $0
  Pop $R1
  ${If} $R1 == "200"
    StrCpy $HealthOK "1"
    DetailPrint "✔ Le serveur répond correctement sur le port $PortApi."
    Return
  ${EndIf}
  ${If} $R0 < 10
    Sleep 2000
    Goto loop_health
  ${EndIf}

  DetailPrint ""
  DetailPrint "Le serveur n'a pas répondu correctement sur le port $PortApi."
  DetailPrint "Consultez le journal : $INSTDIR\college-aureole-service.out.log"
  MessageBox MB_ICONEXCLAMATION "Le serveur n'a pas répondu immédiatement.$\n$\nVérifiez le journal :$\n$INSTDIR\college-aureole-service.out.log$\n$\nLe service redémarre automatiquement tant que la base n'est pas prête."
FunctionEnd

; ============================================================
; Génère le fichier .env
; ============================================================
Function GenererEnv
  DetailPrint "Génération du fichier .env…"

  ; Clé JWT : deux GUID concaténés via un fichier .ps1 temporaire
  ; (robuste face aux apostrophes typographiques).
  ClearErrors
  FileOpen $3 "$PLUGINSDIR\genkey.ps1" w
  IfErrors 0 +3
    MessageBox MB_ICONSTOP "Impossible de créer le script temporaire de génération de clé.$\nInstallation interrompue."
    Abort
  FileWrite $3 "[Console]::Out.Write([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N'))$\r$\n"
  FileClose $3

  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\genkey.ps1"'
  Pop $0
  Pop $1
  DetailPrint "Code retour PowerShell : $0 | Sortie : $1"
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "PowerShell est requis pour générer la clé de sécurité.$\nInstallation interrompue.$\n$\nCode retour : $0$\nSortie : $1"
    Abort
  ${EndIf}

  ; Écriture du .env. Hôte/port/base fixés en mono-poste (localhost:5432).
  FileOpen $2 "$INSTDIR\.env" w
  FileWrite $2 "ENVIRONMENT=production$\r$\n"
  FileWrite $2 "AUREOLE_HOST=0.0.0.0$\r$\n"
  FileWrite $2 "AUREOLE_PORT=$PortApi$\r$\n"
  FileWrite $2 "JWT_SECRET_KEY=$1$\r$\n"
  FileWrite $2 "CORS_ORIGINS=http://tauri.localhost,https://tauri.localhost,tauri://localhost,http://localhost$\r$\n"
  FileWrite $2 "DATABASE_URL=postgresql+psycopg2://$PgUtilisateur:$PgMotDePasse@localhost:5432/collegeaureole$\r$\n"
  FileWrite $2 "AUTO_CREATE_TABLES=true$\r$\n"
  FileWrite $2 "LOG_LEVEL=INFO$\r$\n"
  FileClose $2

  ; Vérification que le .env est bien non vide
  ${IfNot} ${FileExists} "$INSTDIR\.env"
    MessageBox MB_ICONSTOP "Échec de la création du fichier .env.$\nInstallation interrompue."
    Abort
  ${EndIf}

  ; Lecture restreinte du .env (SYSTEM + Administrateurs)
  nsExec::ExecToLog 'icacls "$INSTDIR\.env" /inheritance:r /grant:r *S-1-5-18:F *S-1-5-32-544:F'
FunctionEnd

; ============================================================
; Détection de l'adresse IP affichée (première IPv4 hors 127.0.0.1)
; ============================================================
Function DetecterIP
  StrCpy $ServeurIP "localhost"
  ; Tente de récupérer la première IPv4 du réseau (hors 127.0.0.1). En cas
  ; d'échec ou d'IP introuvable, on reste sur "localhost".
  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {\$_.IPAddress -notmatch ''^127\.'' -and \$_.InterfaceAlias -notmatch ''Loopback''} | Select-Object -First 1).IPAddress"'
  Pop $0
  Pop $1
  ${If} $0 == 0
    StrCpy $0 "$1"
    StrCpy $ServeurIP "$0"
  ${EndIf}
  ${If} $ServeurIP == ""
    StrCpy $ServeurIP "localhost"
  ${EndIf}
FunctionEnd

; ============================================================
; Désinstallation
; ============================================================
Section "Uninstall"
  ExecWait '"$INSTDIR\college-aureole-service.exe" stop'
  ExecWait '"$INSTDIR\college-aureole-service.exe" uninstall'
  nsExec::Exec 'netsh advfirewall firewall delete rule name="College Aureole Serveur"'

  Delete "$INSTDIR\desinstallation.exe"
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\college-aureole-serveur.exe"
  Delete "$INSTDIR\college-aureole-service.exe"
  Delete "$INSTDIR\college-aureole-service.xml"
  Delete "$INSTDIR\.env"
  RMDir /r "$INSTDIR\uploads"

  ; Client + raccourcis
  Delete "$DESKTOP\College Aureole.lnk"
  Delete "$SMPROGRAMS\College Aureole\College Aureole.lnk"
  RMDir "$SMPROGRAMS\College Aureole"
  RMDir /r "$INSTDIR\client"

  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\CollegeAureole\Serveur"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CollegeAureoleServeur"
  DeleteRegKey HKLM "Software\CollegeAureole"
SectionEnd
