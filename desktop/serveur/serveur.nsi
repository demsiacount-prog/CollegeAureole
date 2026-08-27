; ─────────────────────────────────────────────────────────────────────────────
; Installeur NSIS du SERVEUR College Aureole (poste-serveur LAN).
;
; Attend un répertoire `paquetage/` à côté de ce script contenant :
;   paquetage\college-aureole-serveur\…     (sortie PyInstaller, onedir)
;   paquetage\college-aureole-service.exe   (wrapper WinSW x64 renommé)
;   paquetage\college-aureole-serveur.xml   (définition du service)
;
; Build :  makensis serveur.nsi
; ─────────────────────────────────────────────────────────────────────────────

Unicode true
RequestExecutionLevel admin

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"

Name "College Aureole - Serveur"
OutFile "..\..\dist\college-aureole-serveur_x64-setup.exe"
InstallDir "$PROGRAMFILES64\CollegeAureole\serveur"
InstallDirRegKey HKLM "Software\CollegeAureole\Serveur" "InstallDir"

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"

!insertmacro MUI_PAGE_WELCOME
Page custom PageConfig PageConfigLeave
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "French"

; ── Variables de configuration ──
Var PortApi        ; port HTTP du backend
Var PgHote         ; hôte PostgreSQL
Var PgPort         ; port PostgreSQL
Var PgBase         ; nom de la base
Var PgUtilisateur  ; rôle PostgreSQL
Var PgMotDePasse   ; mot de passe PostgreSQL
Var IniFichier     ; chemin du formulaire InstallOptions

Function PageConfig
  InitPluginsDir
  StrCpy $IniFichier "$PLUGINSDIR\config.ini"
  File /oname=$IniFichier "config.ini"

  ; Valeurs par défaut (ou configuration existante lors d'une mise à jour)
  ReadINIStr $0 "$IniFichier" "Field 3" "State"
  ${If} $0 == ""
    WriteINIStr "$IniFichier" "Field 3" "State" "8000"
  ${EndIf}
  WriteINIStr "$IniFichier" "Field 7"  "State" "localhost"
  WriteINIStr "$IniFichier" "Field 9"  "State" "5432"
  WriteINIStr "$IniFichier" "Field 11" "State" "collegeaureole"
  WriteINIStr "$IniFichier" "Field 13" "State" "collegeaureole"

  InstallOptions::dialog "$IniFichier"
  Pop $0
FunctionEnd

Function PageConfigLeave
  ReadINIStr $PortApi       "$IniFichier" "Field 3"  "State"
  ReadINIStr $PgHote        "$IniFichier" "Field 7"  "State"
  ReadINIStr $PgPort        "$IniFichier" "Field 9"  "State"
  ReadINIStr $PgBase        "$IniFichier" "Field 11" "State"
  ReadINIStr $PgUtilisateur "$IniFichier" "Field 13" "State"
  ReadINIStr $PgMotDePasse  "$IniFichier" "Field 15" "State"

  ${If} $PortApi == ""
    MessageBox MB_ICONEXCLAMATION "Le port HTTP est obligatoire."
    Abort
  ${EndIf}
  ${If} $PgHote == ""
    MessageBox MB_ICONEXCLAMATION "L'hôte PostgreSQL est obligatoire."
    Abort
  ${EndIf}
FunctionEnd

; ── Installation ──
Section "Serveur" SectionServeur
  SetOutPath "$INSTDIR"

  ; Arrêt propre d'une installation existante avant mise à jour des fichiers
  nsExec::ExecToLog '"$INSTDIR\college-aureole-service.exe" stop'
  Pop $0 ; code ignoré (service pas encore installé au premier passage)

  ; Fichiers applicatifs (PyInstaller onedir : binaire + _internal)
  File /r "paquetage\college-aureole-serveur\*.*"
  File "paquetage\college-aureole-service.exe"
  File "paquetage\college-aureole-serveur.xml"

  ; Dossier des fichiers téléversés (logos) — préservé lors des mises à jour
  CreateDirectory "$INSTDIR\uploads"

  ; Fichier .env généré une seule fois (conservé lors des mises à jour).
  ; Cochez « Réinitialiser » n'existe plus : supprimez .env manuellement pour
  ; relancer l'assistant. Les valeurs saisies ici ne sont donc utilisées que
  ; si le fichier est absent.
  ${IfNot} ${FileExists} "$INSTDIR\.env"
    Call GenererEnv
  ${ElseIfNot} ${Silent}
    DetailPrint ".env existant conservé (configuration inchangée)."
  ${EndIf}

  ; Règle de pare-feu entrante pour le port HTTP
  nsExec::ExecToLog 'netsh advfirewall firewall delete rule name="College Aureole Serveur"'
  nsExec::ExecToLog 'netsh advfirewall firewall add rule name="College Aureole Serveur" dir=in action=allow protocol=TCP localport=$PortApi'

  ; Enregistrement et démarrage du service Windows
  nsExec::ExecToLog '"$INSTDIR\college-aureole-service.exe" install'
  nsExec::ExecToLog '"$INSTDIR\college-aureole-service.exe" start'

  WriteUninstaller "$INSTDIR\desinstallation.exe"
  WriteRegStr HKLM "Software\CollegeAureole\Serveur" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CollegeAureoleServeur" \
                   "DisplayName" "College Aureole - Serveur"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CollegeAureoleServeur" \
                   "UninstallString" '"$INSTDIR\desinstallation.exe"'
SectionEnd

; Génère le fichier .env : connexion PostgreSQL + secret JWT aléatoire.
Function GenererEnv
  DetailPrint "Génération du fichier .env…"

  ; Secret JWT : deux GUID concaténés (64 caractères hexadécimaux).
  ; Générés via PowerShell : [guid]::NewGuid() repose sur le générateur
  ; aléatoire cryptographique de .NET, plus sûr que l'alternative VBScript.
  nsExec::ExecToStack 'powershell -NoProfile -Command "[guid]::NewGuid().ToString(''N'')+[guid]::NewGuid().ToString(''N'')"'
  Pop $0
  Pop $1
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "PowerShell est requis pour générer la clé de sécurité.$\nInstallation interrompue."
    Abort
  ${EndIf}

  FileOpen $2 "$INSTDIR\.env" w
  FileWrite $2 "ENVIRONMENT=production$\r$\n"
  FileWrite $2 "AUREOLE_HOST=0.0.0.0$\r$\n"
  FileWrite $2 "AUREOLE_PORT=$PortApi$\r$\n"
  FileWrite $2 "JWT_SECRET_KEY=$1$\r$\n"
  FileWrite $2 "CORS_ORIGINS=http://tauri.localhost,https://tauri.localhost,tauri://localhost$\r$\n"
  FileWrite $2 "DATABASE_URL=postgresql+psycopg2://$PgUtilisateur:$PgMotDePasse@$PgHote:$PgPort/$PgBase$\r$\n"
  FileClose $2

  ; Lecture restreinte du .env (mot de passe base + clé JWT) : SYSTEM et
  ; Administrateurs uniquement, via SIDs bien connus (indépendant de la
  ; langue de Windows). Le service tourne sous LocalSystem : il y accède.
  nsExec::ExecToLog 'icacls "$INSTDIR\.env" /inheritance:r /grant:r *S-1-5-18:F *S-1-5-32-544:F'
FunctionEnd

; ── Désinstallation ──
Section "Uninstall"
  ExecWait '"$INSTDIR\college-aureole-service.exe" stop'
  ExecWait '"$INSTDIR\college-aureole-service.exe" uninstall'
  nsExec::Exec 'netsh advfirewall firewall delete rule name="College Aureole Serveur"'

  Delete "$INSTDIR\desinstallation.exe"
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\college-aureole-serveur.exe"
  Delete "$INSTDIR\college-aureole-service.exe"
  Delete "$INSTDIR\college-aureole-serveur.xml"
  Delete "$INSTDIR\.env"
  RMDir /r "$INSTDIR\uploads"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\CollegeAureole\Serveur"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\CollegeAureoleServeur"
SectionEnd
