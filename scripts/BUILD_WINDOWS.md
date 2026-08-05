# Build Windows (app desktop Tauri)

L'application desktop (mode mono-poste, base SQLite dans `%APPDATA%`) ne peut pas
être **croisée** depuis Linux : Tauri compile sur l'OS cible. Le build Windows se
fait donc sur un PC Windows, avec le même dépôt.

## Prérequis (une seule fois)

1. **Python 3.10+** — https://www.python.org/downloads/windows/ (cocher *Add to PATH*)
2. **Rust** — https://rustup.rs (toolchain MSVC)
3. **Visual Studio Build Tools** — https://visualstudio.microsoft.com/visual-cpp-build-tools/
   → charge *Desktop development with C++*
4. **Node.js 18+** — https://nodejs.org/

## Build (tout en un)

```powershell
# depuis la racine du dépôt
powershell -ExecutionPolicy Bypass -File scripts\build-windows.ps1
```

Ce script :
1. crée `backend\venv` + installe `requirements.txt` et `pyinstaller`,
2. compile le **sidecar backend** (`college-aureole-backend.spec` → onefile) et le
   copie dans `frontend\src-tauri\binaries\college-aureole-backend-x86_64-pc-windows-msvc.exe`,
3. build le frontend (`npm run build`),
4. lance `npm run tauri build -- --bundles nsis`.

Résultat : `frontend\src-tauri\target\release\bundle\nsis\College Aureole_0.1.6_x64-setup.exe`
(double-clic pour installer).

## À la main (optionnel)

```powershell
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt pyinstaller
venv\Scripts\pyinstaller --noconfirm college-aureole-backend.spec
copy dist\college-aureole-backend\college-aureole-backend.exe ..\frontend\src-tauri\binaries\college-aureole-backend-x86_64-pc-windows-msvc.exe
cd ..\frontend
npm install
npm run build
npm run tauri build -- --bundles nsis
```

## Notes

- Les données desktop sont stockées dans `%APPDATA%\college-aureole\` (DB SQLite).
- Pour un désinstallateur propre, Tauri produit aussi un `.msi` si besoin :
  `npm run tauri build -- --bundles nsis,msi`.
- Ne committez pas `frontend\src-tauri\binaries\*.exe` (artefacts de build).
