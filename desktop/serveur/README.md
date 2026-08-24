# Déploiement LAN — College Aureole

Architecture client léger + poste-serveur :

```
┌─ Poste SERVEUR (1×) ────────────┐      ┌─ Postes CLIENTS (N×) ──────┐
│  PostgreSQL (prérequis)         │ LAN  │  Client Tauri (~15 Mo)     │
│  college-aureole-serveur.exe    │◄─────│  UI embarquée, zéro Python │
│   service Windows (WinSW)       │ HTTP │  adresse serveur mémorisée │
│   écoute 0.0.0.0:<port API>     │      │  installeur NSIS           │
└─────────────────────────────────┘      └────────────────────────────┘
```

## Installeurs produits par la CI

| Fichier | Poste | Rôle |
|---|---|---|
| `college-aureole_x64-setup.exe` | chaque poste utilisateur | client léger (interface seule) |
| `college-aureole-serveur_x64-setup.exe` | le poste-serveur uniquement | backend FastAPI en service Windows |

## Installation du poste-serveur

1. **PostgreSQL** : installer PostgreSQL ≥ 14 et créer une base dédiée
   (`collegeaureole`) avec un rôle propriétaire et son mot de passe.
2. **Installeur serveur** : lancer `college-aureole-serveur_x64-setup.exe`,
   saisir le port HTTP et les paramètres PostgreSQL. L'installeur :
   - copie l'application dans `C:\Program Files\CollegeAureole\serveur`,
   - génère le fichier `.env` (connexion base + clé JWT aléatoire),
   - crée la règle de pare-feu pour le port choisi,
   - installe et démarre le **service Windows** « College Aureole - Serveur ».
3. **Vérification** : depuis n'importe quel poste du LAN, ouvrir
   `http://<adresse-serveur>:<port>/api/health` → doit répondre
   `{"status":"running","database":"connected"}`.

## Installation des clients

Lancer `college-aureole_x64-setup.exe`. Au premier démarrage, l'écran
« Connexion au serveur » demande l'adresse du poste-serveur
(`http://<ip>:<port>`), la teste puis la mémorise.

Mise à jour d'un client : réinstaller par-dessus. Mise à jour du serveur :
relancer l'installeur serveur (le `.env` et le dossier `uploads` sont
conservés).

## Exploitation

- Journaux service : `<install>\college-aureole-service.out.log` (rotation)
- Redémarrage manuel : `services.msc` → « College Aureole - Serveur »
- Sauvegardes : `pg_dump collegeaureole` (les logos sont dans
  `<install>\uploads`)
- Désinstallation : `desinstallation.exe` dans le dossier d'installation
  (arrête le service ; supprime aussi `.env` et `uploads`)

## Notes de sécurité

- HTTP simple sur le LAN (pas de TLS) : à réserver au réseau local de
  l'établissement.
- La clé JWT est générée à l'installation et stockée dans `.env`
  (lecture restreinte aux utilisateurs locaux).
- Le service tourne sous LocalSystem ; pour un durcissement supplémentaire,
  créer un compte de service dédié dans `college-aureole-serveur.xml`.

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
makensis ..\desktop\serveur\serveur.nsi

# Client Tauri
cd ../frontend
npm run tauri build -- --bundles nsis
```
