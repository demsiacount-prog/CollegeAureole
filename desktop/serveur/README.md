# College Aureole — Application mono-poste

College Aureole est désormais une **application autonome installée sur un seul
poste** : l'interface (client), le serveur (backend FastAPI) et la base de
données (PostgreSQL) vivent sur la même machine.

```
┌─ Poste unique (installé par l'admin) ─────────────┐
│  Client Tauri (exe portable, raccourci Bureau)    │
│  college-aureole-serveur.exe (backend + API)      │
│   ↳ service Windows (WinSW), démarrage auto       │
│  PostgreSQL (démarrage auto, avant le backend)    │
└───────────────────────────────────────────────────┘
```

L'utilisateur final lance simplement l'application : elle se connecte
**automatiquement** au serveur local (`http://localhost:8000`), sans aucun
écran technique.

## Installeurs produits par la CI

| Fichier | Rôle |
|---|---|
| `college-aureole-setup.exe` | **Tout-en-un** : installe le serveur (service) **et** le client, avec raccourci Bureau. C'est l'installeur à utiliser. |
| `college-aureole_x64-setup.exe` | Installateur du client seul (pour déploiements particuliers ou mises à jour client). |

## Installation (rôle admin)

1. **PostgreSQL** : sur le poste, installer PostgreSQL ≥ 14 et créer une base
   dédiée (`collegeaureole`) avec un rôle propriétaire et son mot de passe.
   *L'installeur ne gère pas PostgreSQL* : il ne fait que détecter (au boot,
   le backend démarre après le service PostgreSQL).
2. **Installeur tout-en-un** : lancer `college-aureole-setup.exe`, puis saisir :
   - le **port HTTP** (défaut `8000`),
   - l'**utilisateur** et le **mot de passe** de la base PostgreSQL.
   L'installeur :
   - copie l'application dans `C:\Program Files\CollegeAureole\`,
   - génère le fichier `.env` (connexion base + clé JWT aléatoire),
   - crée la règle de pare-feu pour le port choisi,
   - installe et démarre le **service Windows** « College Aureole - Serveur »
     (avec dépendance sur le service PostgreSQL, redémarrage auto si la base
     n'est pas encore prête),
   - installe le **client** + un raccourci « College Aureole » sur le Bureau,
   - vérifie le démarrage (`/api/health`) et affiche l'adresse finale.
3. **Vérification** : ouvrir
   `http://localhost:<port>/api/health` → doit répondre
   `{"status":"running","database":"connected"}`.

## Utilisation (rôle utilisateur final)

Double-cliquer sur le raccourci « College Aureole » sur le Bureau : le serveur
local est détecté automatiquement. Aucune configuration requise.

## Mises à jour

- **Tout-en-un** : réinstaller `college-aureole-setup.exe` par-dessus (le
  `.env` et le dossier `uploads` sont conservés).
- **Client seul** : réinstaller `college-aureole_x64-setup.exe`.

## Exploitation

- Journaux service : `<install>\college-aureole-service.out.log` (rotation)
- Redémarrage manuel : `services.msc` → « College Aureole - Serveur »
- Sauvegardes : `pg_dump collegeaureole` (les logos sont dans
  `<install>\uploads`)
- Désinstallation : `desinstallation.exe` dans le dossier d'installation
  (arrête le service ; supprime aussi `.env`, `uploads` et le client).

## Notes de sécurité

- HTTP simple en local (pas de TLS) : à réserver à l'usage mono-poste.
- La clé JWT est générée à l'installation et stockée dans `.env`
  (lecture restreinte aux utilisateurs locaux).
- Le service tourne sous LocalSystem ; pour un durcissement supplémentaire,
  créer un compte de service dédié dans `tout-en-un.nsi`.

## Build local (hors CI)

```powershell
# Backend
cd backend
pip install -r requirements.txt pyinstaller
pyinstaller college-aureole-backend.spec

# Assemblage paquetage + NSIS (WinSW téléchargé une fois)
mkdir ..\desktop\serveur\paquetage
Copy-Item dist\college-aureole-serveur ..\desktop\serveur\paquetage\ -Recurse
Invoke-WebRequest https://github.com/winsw/winsw/releases/download/v2.12.0/WinSW-x64.exe `
  -OutFile ..\desktop\serveur\paquetage\college-aureole-service.exe
Copy-Item ..\desktop\serveur\college-aureole-serveur.xml ..\desktop\serveur\paquetage\

# Client Tauri (exe portable requis pour le tout-en-un)
cd ../frontend
npm run tauri build -- --bundles nsis
Copy-Item src-tauri\target\release\"College Aureole.exe" ..\desktop\serveur\paquetage\college-aureole-client.exe

# Installeur tout-en-un
makensis ..\desktop\serveur\tout-en-un.nsi
```
