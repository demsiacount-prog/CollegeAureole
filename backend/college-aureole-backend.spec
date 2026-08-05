# -*- mode: python ; coding: utf-8 -*-
# Spécification PyInstaller du backend embarqué (sidecar) de l'app desktop
# Tauri. Construit un exécutable autonome à partir de main_desktop.py :
#   cd backend && venv/bin/pyinstaller college-aureole-backend.spec
# Produit dist/college-aureole-backend/college-aureole-backend, à copier dans
# frontend/src-tauri/binaries/college-aureole-backend-<triple-cible>.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = []
# SQLAlchemy charge ses dialectes dynamiquement.
hiddenimports += collect_submodules("sqlalchemy")
hiddenimports += [
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.dialects.postgresql.psycopg2",
]
# Uvicorn (serveurs, protocoles, loops) résolus dynamiquement.
hiddenimports += collect_submodules("uvicorn")
hiddenimports += [
    "multipart",
    "passlib.handlers.argon2",
    "argon2",
    "argon2.low_level",
    "psycopg2",
    "jwt",
    "jwt.algorithms",
    "dotenv",
    "openpyxl",
    "faker",
    "email_validator",
]

# Données requises par les libs (Faker : providers/locales ; openpyxl : styles/traductions).
datas = collect_data_files("faker")
datas += collect_data_files("openpyxl")

a = Analysis(
    ["main_desktop.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "IPython", "pytest"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="college-aureole-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
